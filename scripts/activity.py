"""Render GitHub contribution grid and streak stats as dependency-free SVGs."""
import html
import json
import sys
from calendar import month_abbr
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COLORS = ['#19283b', '#164e63', '#0e7490', '#06b6d4', '#67e8f9']
LEVELS = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE']
BLUE = '#22d3ee'
LIGHT_BLUE = '#67e8f9'


def day_label(count: int) -> str:
    return 'day' if count == 1 else 'days'


def parse_day(value: str) -> date:
    return date.fromisoformat(value)


def format_full(value: str) -> str:
    return f'{parse_day(value):%b %d, %Y}'


def format_range(start: str | None, end: str | None) -> str:
    if not start or not end:
        return '—'
    first, last = parse_day(start), parse_day(end)
    if first.year == last.year:
        return f'{first:%b %d} - {last:%b %d}'
    return f'{first:%b %d, %Y} - {last:%b %d, %Y}'


def calculate_streaks(days: list[dict]) -> tuple[int, str | None, str | None, int, str | None, str | None]:
    """Return (current, current start/end, longest, longest start/end)."""
    today = date.today()
    usable = [day for day in days if parse_day(day['date']) <= today]
    usable.sort(key=lambda day: day['date'])
    if not usable:
        return 0, None, None, 0, None, None

    active_dates = [
        parse_day(day['date'])
        for day in usable
        if int(day['contributionCount']) > 0
    ]
    active_set = set(active_dates)

    last_date = parse_day(usable[-1]['date'])
    current_end = None
    if last_date in active_set:
        current_end = last_date
    elif last_date - timedelta(days=1) in active_set:
        # GitHub still shows yesterday's streak until today has activity.
        current_end = last_date - timedelta(days=1)

    current_start = current_end
    while current_start is not None and current_start - timedelta(days=1) in active_set:
        current_start -= timedelta(days=1)
    current = (current_end - current_start).days + 1 if current_end else 0

    longest = 0
    longest_start = longest_end = None
    run_start = previous = None
    for day in active_dates:
        if previous is None or (day - previous).days != 1:
            run_start = day
        length = (day - run_start).days + 1
        if length > longest:
            longest, longest_start, longest_end = length, run_start, day
        previous = day

    return (
        current,
        current_start.isoformat() if current_start else None,
        current_end.isoformat() if current_end else None,
        longest,
        longest_start.isoformat() if longest_start else None,
        longest_end.isoformat() if longest_end else None,
    )


def render_grid(weeks: list[dict], total: int, first_day: str, last_day: str) -> str:
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 222" role="img" aria-labelledby="title desc">',
        '<title id="title">GitHub contribution activity</title>',
        f'<desc id="desc">{total:,} contributions between {first_day} and {last_day}. Brighter cells indicate more activity.</desc>',
        '<rect width="900" height="222" rx="16" fill="#0d1524"/>',
        '<g font-family="system-ui,sans-serif" fill="#e2e8f0">',
        '<text x="28" y="36" font-size="16" font-weight="600">A year of building</text>',
        f'<text x="28" y="58" font-size="12" fill="#94a3b8">{total:,} contributions in the past year</text>',
    ]

    last_month = None
    for week_index, week in enumerate(weeks):
        x = 40 + week_index * 15
        for day in week['contributionDays']:
            y = 88 + day['weekday'] * 15
            month = day['date'][:7]
            if month != last_month and x < 840:
                label = html.escape(month_abbr[int(day['date'][5:7])])
                svg.append(f'<text x="{x}" y="79" font-size="9" fill="#94a3b8">{label}</text>')
                last_month = month
            color = COLORS[LEVELS.index(day['contributionLevel'])]
            title = html.escape(f'{day["date"]}: {day["contributionCount"]:,} contributions')
            svg.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{color}"><title>{title}</title></rect>')

    svg.append('<path d="M28 190H872" stroke="#24384d"/>')
    svg.append('<text x="690" y="207" font-size="10" fill="#94a3b8">Less</text>')
    for i, color in enumerate(COLORS):
        svg.append(f'<rect x="{720 + i * 15}" y="198" width="11" height="11" rx="2" fill="{color}"/>')
    svg.append('<text x="800" y="207" font-size="10" fill="#94a3b8">More</text></g></svg>')
    return '\n'.join(svg) + '\n'


def render_streaks(
    total: int,
    first_day: str,
    current: int,
    current_range: str,
    longest: int,
    longest_range: str,
) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 495 195" role="img" aria-labelledby="title desc">
<title id="title">GitHub streaks</title>
<desc id="desc">{total:,} total contributions from {first_day} to present. Current streak: {current} {day_label(current)} ({current_range}). Longest streak: {longest} {day_label(longest)} ({longest_range}).</desc>
<rect x="0.5" y="0.5" width="494" height="194" rx="10" fill="#0D1117" stroke="#30363D"/>
<g font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" text-anchor="middle">
<text x="247.5" y="19" fill="{BLUE}" font-size="10" font-weight="700" letter-spacing="1.5">GITHUB STREAKS</text>
<path d="M165 28V181M330 28V181" stroke="#30363D"/>
<text x="82.5" y="62" fill="{BLUE}" font-size="32" font-weight="700">{total:,}</text>
<text x="82.5" y="88" fill="#C9D1D9" font-size="11" font-weight="600">Total Contributions</text>
<text x="82.5" y="110" fill="#8B949E" font-size="9">{format_full(first_day)} - Present</text>
<circle cx="247.5" cy="66" r="30" fill="none" stroke="#30363D" stroke-width="5"/>
<circle cx="247.5" cy="66" r="30" fill="none" stroke="{BLUE}" stroke-width="5" stroke-linecap="round" stroke-dasharray="150 39" transform="rotate(-90 247.5 66)"/>
<path d="M247.5 27c5.2 6.3 7.8 10.2 7.8 14.2a7.8 7.8 0 0 1-15.6 0c0-4 2.6-7.9 7.8-14.2z" fill="{BLUE}"/>
<path d="M247.5 34c2.6 3.2 3.9 5.2 3.9 7.2a3.9 3.9 0 0 1-7.8 0c0-2 1.3-4 3.9-7.2z" fill="{LIGHT_BLUE}"/>
<text x="247.5" y="73" fill="{BLUE}" font-size="26" font-weight="700">{current}</text>
<text x="247.5" y="126" fill="#FFFFFF" font-size="11" font-weight="600">Current Streak</text>
<text x="247.5" y="148" fill="#8B949E" font-size="9">{current_range}</text>
<text x="412.5" y="62" fill="{BLUE}" font-size="32" font-weight="700">{longest}</text>
<text x="412.5" y="88" fill="#C9D1D9" font-size="11" font-weight="600">Longest Streak</text>
<text x="412.5" y="110" fill="#8B949E" font-size="9">{longest_range}</text>
</g></svg>
'''


def main() -> None:
    user = json.load(sys.stdin)['data']['user']
    calendar = user['contributionsCollection']['contributionCalendar']
    weeks = calendar['weeks']
    if not weeks:
        raise SystemExit('No contribution weeks returned by GitHub')

    days = [day for week in weeks for day in week['contributionDays']]
    if not days:
        raise SystemExit('No contribution days returned by GitHub')

    stars = int(user['starredRepositories']['totalCount'])
    total = int(calendar['totalContributions'])
    first_day = min(day['date'] for day in days)
    last_day = max(day['date'] for day in days)
    (current, current_start, current_end,
     longest, longest_start, longest_end) = calculate_streaks(days)

    (ROOT / 'assets/activity.svg').write_text(render_grid(weeks, total, first_day, last_day))
    (ROOT / 'assets/streaks.svg').write_text(render_streaks(
        total,
        first_day,
        current,
        format_range(current_start, current_end),
        longest,
        format_range(longest_start, longest_end),
    ))
    (ROOT / 'assets/stars-given.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="190" height="28" role="img" aria-labelledby="stars-title">
<title id="stars-title">Stars given: {stars}</title>
<rect width="190" height="28" rx="3" fill="#0d1524"/>
<path d="M120 0h67q3 0 3 3v22q0 3-3 3h-67z" fill="#0891b2"/>
<g fill="white" font-family="Verdana, sans-serif" font-size="10" text-anchor="middle">
<text x="60" y="18">STARS GIVEN</text><text x="155" y="18">{stars}</text>
</g></svg>\n''')


if __name__ == '__main__':
    main()
