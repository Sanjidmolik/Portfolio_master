"""Server-side GitHub integration with caching and graceful fallbacks.

The optional GITHUB_TOKEN never leaves the server. Without a token the public
REST API is used (60 req/h per IP), so results are cached in the database.
"""
from __future__ import annotations

import re
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone

import requests
from flask import current_app

from .models import Setting

API = "https://api.github.com"
USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")

CONTRIB_QUERY = """
query($login:String!){ user(login:$login){ contributionsCollection{
  contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } } } }
"""


def _headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "portfolio-site"}
    token = current_app.config.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(path, **params):
    r = requests.get(f"{API}{path}", headers=_headers(), params=params, timeout=8)
    r.raise_for_status()
    return r.json()


def _contributions_graphql(username):
    r = requests.post(f"{API}/graphql", headers=_headers(), timeout=10,
                      json={"query": CONTRIB_QUERY, "variables": {"login": username}})
    r.raise_for_status()
    cal = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    return {
        "source": "calendar",
        "total": cal["totalContributions"],
        "days": [{"date": d["date"], "count": d["contributionCount"]} for d in days],
    }


def _contributions_from_events(username):
    """Approximate recent activity from the public events feed (last ~90 days)."""
    counts = Counter()
    for page in (1, 2, 3):
        events = _get(f"/users/{username}/events/public", per_page=100, page=page)
        if not events:
            break
        for ev in events:
            day = ev.get("created_at", "")[:10]
            weight = len(ev.get("payload", {}).get("commits", []) or []) if ev.get("type") == "PushEvent" else 1
            counts[day] += max(weight, 1)
    today = date.today()
    start = today - timedelta(days=7 * 18 - 1)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # align to Sunday
    days, d = [], start
    while d <= today:
        days.append({"date": d.isoformat(), "count": counts.get(d.isoformat(), 0)})
        d += timedelta(days=1)
    return {"source": "events", "total": sum(x["count"] for x in days), "days": days}


def _level(count, max_count):
    if count <= 0:
        return 0
    if max_count <= 4:
        return min(4, count)
    ratio = count / max_count
    return 1 if ratio < 0.25 else 2 if ratio < 0.5 else 3 if ratio < 0.75 else 4


def fetch(username: str) -> dict:
    user = _get(f"/users/{username}")
    repos = _get(f"/users/{username}/repos", per_page=100, sort="updated", type="owner")
    own = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in own)
    forks = sum(r.get("forks_count", 0) for r in own)
    langs = Counter(r["language"] for r in own if r.get("language"))
    top_langs = [{"name": n, "count": c} for n, c in langs.most_common(6)]
    featured = sorted(own, key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at") or ""), reverse=True)[:6]

    # The contribution heatmap was removed from the site, so skip those extra API calls.
    # Set GITHUB_FETCH_CONTRIBUTIONS=1 to fetch them again.
    contributions = None
    if current_app.config.get("GITHUB_FETCH_CONTRIBUTIONS"):
        try:
            contributions = (_contributions_graphql(username) if current_app.config.get("GITHUB_TOKEN")
                             else _contributions_from_events(username))
        except Exception as exc:  # contributions are a nice-to-have
            current_app.logger.info("GitHub contributions unavailable: %s", exc)
    if contributions:
        mx = max((d["count"] for d in contributions["days"]), default=0)
        for d in contributions["days"]:
            d["level"] = _level(d["count"], mx)
        # chunk into weeks (columns)
        days = contributions["days"]
        contributions["weeks"] = [days[i:i + 7] for i in range(0, len(days), 7)]

    return {
        "profile": {
            "login": user.get("login"), "name": user.get("name"), "avatar": user.get("avatar_url"),
            "url": user.get("html_url"), "bio": user.get("bio"),
            "public_repos": user.get("public_repos", 0), "followers": user.get("followers", 0),
            "following": user.get("following", 0),
        },
        "stats": {"stars": stars, "forks": forks, "repos": len(own)},
        "languages": top_langs,
        "repos": [{
            "name": r["name"], "url": r["html_url"], "description": r.get("description") or "",
            "language": r.get("language"), "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0), "pushed_at": (r.get("pushed_at") or "")[:10],
        } for r in featured],
        "contributions": contributions,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def get_github_data(username: str | None, force: bool = False) -> dict | None:
    """Return cached GitHub data, refreshing when stale. Never raises."""
    if not username or not USERNAME_RE.match(username):
        return None
    key = f"github_cache:{username.lower()}"
    cached = Setting.read(key)
    ttl = current_app.config.get("GITHUB_CACHE_SECONDS", 3600)
    if cached and not force and time.time() - cached.get("ts", 0) < ttl:
        return cached["data"]
    if cached and not force and time.time() - cached.get("failed_ts", 0) < 600:
        return cached.get("data")  # recent failure: back off
    try:
        data = fetch(username)
        Setting.write(key, {"ts": time.time(), "data": data})
        return data
    except Exception as exc:
        current_app.logger.warning("GitHub fetch failed for %s: %s", username, exc)
        stale = (cached or {}).get("data")
        Setting.write(key, {"ts": (cached or {}).get("ts", 0), "failed_ts": time.time(), "data": stale})
        return stale
