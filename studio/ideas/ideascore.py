"""ideascore.py: score a channel niche or video idea out of 100, by what Google has published about how
YouTube picks videos. Each factor is rated 0-10 with the evidence written next to it; measured evidence
(autocomplete, search volume, Studio data) beats judgement, and the report says which is which.

The factors and where they come from:
  watch_time   25  Covington, Adams, Sargin (Google, 2016) "Deep Neural Networks for YouTube Recommendations":
                   the ranking network is trained to predict expected watch time per impression, not clicks.
  click        15  Zhao et al. (Google, 2019) "Recommending What Video to Watch Next: A Multitask Ranking
                   System": engagement objectives (clicks, watch) are one half of the ranking.
  satisfaction 15  Same paper, the other half: satisfaction objectives (likes, survey ratings, dismissals);
                   YouTube's own posts on recommendations say survey answers and "valued watch time" count.
  chaining     15  Davidson et al. (Google, 2010) "The YouTube Video Recommendation System": candidates come
                   from co-visitation (videos watched together); Covington 2016 builds candidates from watch history.
  demand       15  Candidate generation can only pull you for people already interested in the topic
                   (search and watch history). Measured with autocomplete position and search volume.
  freshness     5  Covington 2016 feeds "example age" to the model so fresh uploads get a lift; topics with
                   news hooks or yearly rule changes get more of it.
  gap          10  Not in the papers: ranking compares you against the other candidates in the same slate,
                   so a topic owned by big channels or movie clips is harder to win.
  python3 ideascore.py ideas.json      (list of {"name", "factors": {factor: [rating, "evidence", "measured"|"judged"]}})
"""
import json, sys
W = {'watch_time': 25, 'click': 15, 'satisfaction': 15, 'chaining': 15, 'demand': 15, 'freshness': 5, 'gap': 10}
def score(idea):
    tot = sum(W[k] * v[0] / 10 for k, v in idea['factors'].items())
    band = 'STRONG' if tot >= 80 else 'WORKABLE' if tot >= 65 else 'WEAK'
    lines = [f"{idea['name']}: {tot:.0f}/100  {band}"]
    for k in W:
        r, ev, how = idea['factors'][k]
        lines.append(f"  {'  ' if r >= 7 else '->'} {k:12s} {r:>2}/10 x{W[k]:<3d} [{how}] {ev}")
    return tot, '\n'.join(lines)
if __name__ == '__main__':
    ideas = json.load(open(sys.argv[1]))
    for t, txt in sorted((score(i) for i in ideas), key=lambda x: -x[0]): print(txt + '\n')
