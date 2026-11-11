"""Render GitHub's contribution calendar as a dependency-free SVG."""
import html
import json
import sys
from pathlib import Path

calendar = json.load(sys.stdin)['data']['user']['contributionsCollection']['contributionCalendar']
colors = ['#19283b', '#164e63', '#0e7490', '#06b6d4', '#67e8f9']
levels = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE']
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 222" role="img" aria-labelledby="title desc">',
       '<title id="title">GitHub contribution activity</title>',
       '<desc id="desc">Daily contributions over the past year. Brighter cells indicate more activity.</desc>',
       '<rect width="900" height="222" rx="16" fill="#0d1524"/>',
       '<g font-family="system-ui,sans-serif" fill="#e2e8f0">',
       '<text x="28" y="36" font-size="16" font-weight="600">A year of building</text>',
       f'<text x="28" y="58" font-size="12" fill="#94a3b8">{int(calendar["totalContributions"]):,} contributions in the past year</text>']
last_month = None
for week_index, week in enumerate(calendar['weeks']):
    for day in week['contributionDays']:
        x, y = 40 + week_index * 15, 88 + day['weekday'] * 15
        month = day['date'][:7]
        if month != last_month and day['weekday'] == 0:
            if week_index < 51:
                svg.append(f'<text x="{x}" y="79" font-size="9" fill="#94a3b8">{day["date"][5:7]}</text>')
            last_month = month
        color = colors[levels.index(day['contributionLevel'])]
        label = html.escape(f'{day["date"]}: {day["contributionCount"]} contributions')
        svg.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{color}"><title>{label}</title></rect>')
svg.append('<text x="690" y="207" font-size="10" fill="#94a3b8">Less</text>')
for i, color in enumerate(colors):
    svg.append(f'<rect x="{720+i*15}" y="198" width="11" height="11" rx="2" fill="{color}"/>')
svg.append('<text x="800" y="207" font-size="10" fill="#94a3b8">More</text></g></svg>')
Path('assets/activity.svg').write_text('\n'.join(svg) + '\n')
