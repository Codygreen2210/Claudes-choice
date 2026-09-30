# Builds the test statements (all fictional banks and people) plus the right answers.
# Run: python3 make.py   (needs reportlab; the Chrome one is made by make-chrome.mjs)
import json, random, datetime as dt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

MERCH = ['KROGER #412', 'SHELL OIL 5712', 'ENTERGY LOUISIANA', 'AMAZON MKTPLACE', 'HOME DEPOT 3321', 'VERIZON WIRELESS',
         'CHECK #1043', 'ATM WITHDRAWAL', 'NETFLIX.COM', 'WALMART SUPERCENTER', 'ZELLE TO D BOUDREAUX', 'STATE FARM INS']
IN = ['PAYROLL DEPOSIT ACME FAB', 'MOBILE DEPOSIT', 'ZELLE FROM M THIBODEAUX', 'IRS TREAS 310 TAX REF']

def txns(seed, start, n, opening):
    r = random.Random(seed); d = start; bal = opening; out = []
    for i in range(n):
        d += dt.timedelta(days=r.choice([0, 0, 1, 1, 2]))
        credit = r.random() < 0.22
        amt = round(r.uniform(400, 2400) if credit else r.uniform(3, 380), 2)
        desc = r.choice(IN if credit else MERCH)
        extra = r.random() < 0.25
        bal = round(bal + (amt if credit else -amt), 2)
        out.append(dict(date=d, desc=desc, extra=('REF ' + str(r.randint(10**9, 10**10))) if extra else None, amt=amt if credit else -amt, bal=bal))
    return out

def money(x, dollar=False):
    return ('$' if dollar else '') + f'{abs(x):,.2f}'

def sbal(x, dollar=False):  # balances keep their sign (overdrawn shows a minus)
    return ('-' if x < 0 else '') + money(x, dollar)

def truth(name, rows, opening, closing, extra=None):
    t = dict(opening=opening, closing=closing, rows=[dict(date=r['date'].isoformat(), amount=r['amt'], desc=r['desc'] + (' ' + r['extra'] if r['extra'] else '')) for r in rows])
    if extra: t.update(extra)
    json.dump(t, open(name + '.json', 'w'), indent=1)

# 1. Two amount columns (withdrawals / deposits) plus a running balance, over a year end.
def bayou():
    op = 2140.55; rows = txns(1, dt.date(2025, 12, 15), 46, op)
    c = canvas.Canvas('bayou.pdf', pagesize=letter)
    per = 28
    for p in range(0, len(rows), per):
        c.setFont('Helvetica-Bold', 13); c.drawString(50, 750, 'First Bayou Savings Bank (fictional)')
        c.setFont('Helvetica', 9); c.drawString(50, 736, 'Statement period: December 15, 2025 through January 14, 2026')
        c.drawString(50, 724, 'Account 0000-1234   Test Customer')
        y = 690
        c.setFont('Helvetica-Bold', 9)
        c.drawString(50, y, 'Date'); c.drawString(100, y, 'Description'); c.drawRightString(400, y, 'Withdrawals'); c.drawRightString(480, y, 'Deposits'); c.drawRightString(560, y, 'Balance')
        c.setFont('Helvetica', 9); y -= 16
        if p == 0:
            c.drawString(100, y, 'Beginning Balance'); c.drawRightString(560, y, money(op)); y -= 14
        for r in rows[p:p + per]:
            c.drawString(50, y, r['date'].strftime('%m/%d')); c.drawString(100, y, r['desc'])
            c.drawRightString(400 if r['amt'] < 0 else 480, y, money(r['amt'])); c.drawRightString(560, y, sbal(r['bal'])); y -= 12
            if r['extra']: c.drawString(100, y, r['extra']); y -= 12
            y -= 2
        if p + per >= len(rows):
            y -= 6; c.setFont('Helvetica-Bold', 9); c.drawString(100, y, 'Ending Balance'); c.drawRightString(560, y, sbal(rows[-1]['bal']))
        c.setFont('Helvetica', 8); c.drawString(280, 40, f'Page {p // per + 1} of {(len(rows) + per - 1) // per}')
        c.showPage()
    c.save(); truth('bayou', rows, op, rows[-1]['bal'])

# 2. One signed amount column; balance printed only on the last line of each day; Times font; "Jan 05" dates.
def delta():
    op = 812.40; rows = txns(2, dt.date(2026, 3, 1), 30, op)
    c = canvas.Canvas('delta.pdf', pagesize=letter)
    c.setFont('Times-Bold', 12); c.drawString(60, 740, 'Delta Workers Credit Union (fictional) - March 2026')
    c.setFont('Times-Roman', 10); c.drawString(60, 724, 'Period 03/01/2026 - 03/31/2026')
    y = 696; c.setFont('Times-Bold', 10)
    c.drawString(60, y, 'Posted'); c.drawString(120, y, 'Transaction'); c.drawString(420, y, 'Amount'); c.drawString(500, y, 'Balance')
    c.setFont('Times-Roman', 10); y -= 16
    c.drawString(120, y, 'Previous Balance'); c.drawRightString(550, y, money(op)); y -= 13
    for i, r in enumerate(rows):
        last_of_day = i + 1 == len(rows) or rows[i + 1]['date'] != r['date']
        c.drawString(60, y, r['date'].strftime('%b %d')); c.drawString(120, y, r['desc'] + (' ' + r['extra'] if r['extra'] else ''))
        c.drawRightString(465, y, ('-' if r['amt'] < 0 else '') + money(r['amt']))
        if last_of_day: c.drawRightString(550, y, sbal(r['bal']))
        y -= 13
    c.drawString(120, y - 6, 'New Balance'); c.drawRightString(550, y - 6, sbal(rows[-1]['bal']))
    c.save(); truth('delta', rows, op, rows[-1]['bal'])

# 3. Big-bank style: deposits and withdrawals in separate sections, all amounts positive, no running balance.
def sections():
    op = 5310.00; rows = txns(3, dt.date(2026, 1, 2), 26, op)
    c = canvas.Canvas('sections.pdf', pagesize=letter)
    c.setFont('Helvetica-Bold', 12); c.drawString(50, 750, 'Pelican National Bank (fictional)')
    c.setFont('Helvetica', 9); c.drawString(50, 736, 'January 01, 2026 through January 31, 2026')
    c.drawString(50, 710, 'Beginning Balance'); c.drawRightString(300, 710, money(op, True))
    c.drawString(50, 698, 'Ending Balance'); c.drawRightString(300, 698, sbal(rows[-1]['bal'], True))
    y = 668
    for title, sign in (('DEPOSITS AND ADDITIONS', 1), ('ELECTRONIC WITHDRAWALS', -1)):
        part = [r for r in rows if (r['amt'] > 0) == (sign > 0)]
        c.setFont('Helvetica-Bold', 10); c.drawString(50, y, title); y -= 14
        c.setFont('Helvetica', 8); c.drawString(50, y, 'DATE'); c.drawString(100, y, 'DESCRIPTION'); c.drawRightString(560, y, 'AMOUNT'); y -= 12
        c.setFont('Helvetica', 9)
        for r in part:
            c.drawString(50, y, r['date'].strftime('%m/%d')); c.drawString(100, y, r['desc'] + (' ' + r['extra'] if r['extra'] else '')); c.drawRightString(560, y, money(r['amt'], True)); y -= 12
        c.setFont('Helvetica-Bold', 9); c.drawString(50, y, 'Total ' + title.title()); c.drawRightString(560, y, money(sum(abs(r['amt']) for r in part), True)); y -= 24
    c.save()
    order = sorted(rows, key=lambda r: (r['amt'] < 0))  # truth is in printed order: deposits then withdrawals
    truth('sections', order, op, rows[-1]['bal'])

# 6. A scanned page: a picture, no text layer.
def scanned():
    c = canvas.Canvas('scanned.pdf', pagesize=letter)
    for i in range(40): c.rect(50, 700 - i * 15, 500, 10, fill=1)
    c.save()

# Data for the Chrome-printed statement (UK style, with one wrong balance printed on purpose).
def chrome_data():
    op = 1500.00; rows = txns(4, dt.date(2026, 2, 3), 22, op)
    json.dump(dict(opening=op, rows=[dict(date=r['date'].isoformat(), desc=r['desc'] + (' ' + r['extra'] if r['extra'] else ''), amt=r['amt'], bal=r['bal']) for r in rows]), open('chrome-data.json', 'w'))
    truth('chrome', rows, op, rows[-1]['bal'], dict(badRow=9))

bayou(); delta(); sections(); scanned(); chrome_data()
print('ok')
