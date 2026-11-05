"""Pure controls for the executive-report investigation selector.

Only deterministic watchlist/alert dates can be selected. The reporting window
is a presentation filter; it never changes the underlying alert decision.
"""
from __future__ import annotations

from datetime import date, timedelta

from src.dashboard_presentation import severity


def reporting_windows(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    days = sorted(date.fromisoformat(r['investigation_date']) for r in rows)
    entire = {
        'key': 'all',
        'label': f'All evaluated dates · {days[0]:%d %b} – {days[-1]:%d %b %Y}',
        'start': days[0].isoformat(),
        'end': days[-1].isoformat(),
    }
    weeks = {}
    for day in days:
        start = day - timedelta(days=day.weekday())
        weeks[start] = {
            'key': start.isoformat(),
            'label': f'Week · {start:%d %b} – {start + timedelta(days=6):%d %b %Y}',
            'start': start.isoformat(),
            'end': (start + timedelta(days=6)).isoformat(),
        }
    return [entire, *(weeks[d] for d in sorted(weeks, reverse=True))]


def rows_for_window(rows: list[dict], window: dict) -> list[dict]:
    return sorted(
        (r for r in rows if window['start'] <= r['investigation_date'] <= window['end']),
        key=lambda r: r['investigation_date'],
    )


def selectable_investigations(rows: list[dict]) -> list[dict]:
    """Limit the interactive date dropdown to watch or confirmed alerts."""
    return sorted(
        (r for r in rows if severity(r) in ('yellow', 'red')),
        key=lambda r: r['investigation_date'],
        reverse=True,
    )


def investigation_option(row: dict) -> str:
    stamp = date.fromisoformat(row['investigation_date'])
    label = 'Alert' if severity(row) == 'red' else 'Watch'
    indicator = '🔴' if severity(row) == 'red' else '🟡'
    return f'{indicator} {stamp:%d %b %Y} · {label}'
