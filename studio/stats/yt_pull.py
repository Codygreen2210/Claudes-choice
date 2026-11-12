"""Pull the channel's YouTube numbers (YouTube Data API + YouTube Analytics API) into one JSON file.

Runs in GitHub Actions (.github/workflows/yt-stats.yml) with three repo secrets:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN   (scopes: youtube.readonly, yt-analytics.readonly)
Writes OUT/latest.json and OUT/<date>.json. No revenue or audience age/gender is pulled (the repo is public).
Standard library only.   python3 yt_pull.py OUT
"""
import json, os, sys, datetime, urllib.request, urllib.parse, urllib.error

OUT = sys.argv[1] if len(sys.argv) > 1 else 'yt'
TODAY = datetime.date.today()


def post(url, data):
    req = urllib.request.Request(url, urllib.parse.urlencode(data).encode())
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def token():
    return post('https://oauth2.googleapis.com/token', {
        'client_id': os.environ['YT_CLIENT_ID'], 'client_secret': os.environ['YT_CLIENT_SECRET'],
        'refresh_token': os.environ['YT_REFRESH_TOKEN'], 'grant_type': 'refresh_token'})['access_token']


TOK = token()


def get(url, **q):
    req = urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers={'Authorization': 'Bearer ' + TOK})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{e.code} {url}: {e.read()[:400]!r}')


def data(path, **q):
    return get('https://www.googleapis.com/youtube/v3/' + path, **q)


def report(metrics, **q):
    """One Analytics report as a list of dicts. Drops a metric the API refuses (e.g. engagedViews) and tries again."""
    ms = metrics.split(',')
    while ms:
        try:
            r = get('https://youtubeanalytics.googleapis.com/v2/reports', ids='channel==MINE', metrics=','.join(ms),
                    startDate=q.pop('startDate', '2015-01-01'), endDate=str(TODAY), **q)
            cols = [h['name'] for h in r.get('columnHeaders', [])]
            return [dict(zip(cols, row)) for row in r.get('rows', [])]
        except RuntimeError as e:
            bad = next((m for m in ms if m in str(e)), None)
            if not bad: raise
            print('dropping metric', bad); ms.remove(bad)
    return []


ch = data('channels', part='id,snippet,statistics,contentDetails', mine='true')['items'][0]
uploads = ch['contentDetails']['relatedPlaylists']['uploads']
ids, page = [], None
while len(ids) < 500:
    q = dict(part='contentDetails', playlistId=uploads, maxResults=50)
    if page: q['pageToken'] = page
    r = data('playlistItems', **q); ids += [i['contentDetails']['videoId'] for i in r['items']]
    page = r.get('nextPageToken')
    if not page: break

videos = {}
for k in range(0, len(ids), 50):
    for v in data('videos', part='snippet,contentDetails,statistics,status', id=','.join(ids[k:k + 50]))['items']:
        videos[v['id']] = dict(title=v['snippet']['title'], published=v['snippet']['publishedAt'],
                               duration=v['contentDetails']['duration'], privacy=v['status']['privacyStatus'],
                               public_views=int(v['statistics'].get('viewCount', 0)), public_likes=int(v['statistics'].get('likeCount', 0)),
                               public_comments=int(v['statistics'].get('commentCount', 0)))

per_video = report('views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,'
                   'subscribersGained,subscribersLost', dimensions='video', sort='-views', maxResults=200)
for row in per_video:
    videos.setdefault(row['video'], {})['analytics'] = {k: v for k, v in row.items() if k != 'video'}

# where each recent video loses people: share of viewers still watching at each 1% of the video
since = TODAY - datetime.timedelta(days=45)
for vid, v in videos.items():
    if v.get('published', '')[:10] >= str(since):
        try:
            v['retention'] = report('audienceWatchRatio,relativeRetentionPerformance', dimensions='elapsedVideoTimeRatio',
                                    filters=f'video=={vid}')
        except RuntimeError as e:
            v['retention_error'] = str(e)[:200]

out = dict(pulled=datetime.datetime.utcnow().isoformat() + 'Z',
           channel=dict(id=ch['id'], title=ch['snippet']['title'], **{k: int(x) for k, x in ch['statistics'].items() if x.isdigit()}),
           daily=report('views,engagedViews,estimatedMinutesWatched,subscribersGained,subscribersLost', dimensions='day', sort='day',
                        startDate=str(TODAY - datetime.timedelta(days=90))),
           traffic=report('views,estimatedMinutesWatched', dimensions='insightTrafficSourceType', sort='-views',
                          startDate=str(TODAY - datetime.timedelta(days=28))),
           videos=videos)
os.makedirs(OUT, exist_ok=True)
for name in ('latest.json', f'{TODAY}.json'):
    json.dump(out, open(os.path.join(OUT, name), 'w'), indent=1)
print(f"{out['channel']['title']}: {len(videos)} videos, {out['channel'].get('subscriberCount')} subs")
