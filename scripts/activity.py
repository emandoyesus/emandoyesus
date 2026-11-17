"""Render GitHub's public contribution calendar as dependency-free SVGs."""
import html
import json
import sys
from calendar import month_abbr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COLORS = ['#2a1016', '#7f1d2d', '#be123c', '#e11d48', '#fb7185']
LEVELS = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE']


def main() -> None:
    user = json.load(sys.stdin)['data']['user']
    calendar = user['contributionsCollection']['contributionCalendar']
    weeks = calendar['weeks']
    if not weeks:
        raise SystemExit('No contribution weeks returned by GitHub')

    stars = int(user['starredRepositories']['totalCount'])
    total = int(calendar['totalContributions'])
    first_day = weeks[0]['contributionDays'][0]['date']
    last_day = weeks[-1]['contributionDays'][-1]['date']

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 222" role="img" aria-labelledby="title desc">',
        '<title id="title">GitHub contribution activity</title>',
        f'<desc id="desc">{total:,} contributions between {first_day} and {last_day}. Brighter cells indicate more activity.</desc>',
        '<rect width="900" height="222" rx="16" fill="#160c10"/>',
        '<g font-family="system-ui,sans-serif" fill="#f5e6e9">',
        '<text x="28" y="36" font-size="16" font-weight="600">A year of building</text>',
        f'<text x="28" y="58" font-size="12" fill="#d0a8b2">{total:,} contributions in the past year</text>',
    ]

    last_month = None
    for week_index, week in enumerate(weeks):
        x = 40 + week_index * 15
        for day in week['contributionDays']:
            y = 88 + day['weekday'] * 15
            month = day['date'][:7]
            if month != last_month and x < 840:
                label = html.escape(month_abbr[int(day['date'][5:7])])
                svg.append(f'<text x="{x}" y="79" font-size="9" fill="#d0a8b2">{label}</text>')
                last_month = month
            color = COLORS[LEVELS.index(day['contributionLevel'])]
            title = html.escape(f'{day["date"]}: {day["contributionCount"]:,} contributions')
            svg.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{color}"><title>{title}</title></rect>')

    svg.append('<path d="M28 190H872" stroke="#4a232d"/>')
    svg.append('<text x="690" y="207" font-size="10" fill="#d0a8b2">Less</text>')
    for i, color in enumerate(COLORS):
        svg.append(f'<rect x="{720 + i * 15}" y="198" width="11" height="11" rx="2" fill="{color}"/>')
    svg.append('<text x="800" y="207" font-size="10" fill="#d0a8b2">More</text></g></svg>')

    (ROOT / 'assets/activity.svg').write_text('\n'.join(svg) + '\n')
    (ROOT / 'assets/stars-given.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="190" height="28" role="img" aria-labelledby="stars-title">
<title id="stars-title">Stars given: {stars}</title>
<rect width="190" height="28" rx="3" fill="#160c10"/>
<path d="M120 0h67q3 0 3 3v22q0 3-3 3h-67z" fill="#e11d48"/>
<g fill="white" font-family="Verdana, sans-serif" font-size="10" text-anchor="middle">
<text x="60" y="18">STARS GIVEN</text><text x="155" y="18">{stars}</text>
</g></svg>\n''')


if __name__ == '__main__':
    main()
