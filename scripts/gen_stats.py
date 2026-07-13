#!/usr/bin/env python3
"""Generate a fully self-hosted GitHub stats card (assets/stats.svg).

Runs inside GitHub Actions using the built-in GITHUB_TOKEN, so there are no
rate-limited third-party services and no personal access token to manage.
Queries the GitHub GraphQL API for public contribution + repo data and renders
a bespoke, theme-aware SVG. Stdlib only (urllib, json) so nothing to install.
"""
import json
import os
import sys
import urllib.request
import urllib.error

USER = os.environ.get("STATS_USER", "Anup-Ojha")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("STATS_OUT", "assets/stats.svg")

# Brand colours for common languages; anything else cycles the accent palette.
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Java": "#b07219", "C++": "#f34b7d", "C": "#555555", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584",
    "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384d54", "Vue": "#41b883",
    "PLpgSQL": "#336790", "Makefile": "#427819", "TeX": "#3D6117",
}
ACCENTS = ["#58e6ff", "#bc8cff", "#3fb950", "#f778ba", "#f0883e"]

QUERY = """
query($login:String!){
  user(login:$login){
    name login
    followers{ totalCount }
    following{ totalCount }
    contributionsCollection{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar{ totalContributions }
    }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, orderBy:{field:STARGAZERS, direction:DESC}){
      totalCount
      nodes{
        stargazerCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){
          edges{ size node{ name } }
        }
      }
    }
  }
}
"""


def fetch():
    if not TOKEN:
        if os.environ.get("ALLOW_MOCK") == "1":
            return mock()
        raise SystemExit("No GH_TOKEN/GITHUB_TOKEN set (set ALLOW_MOCK=1 to test locally).")
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": USER})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise SystemExit("GraphQL errors: " + json.dumps(payload["errors"]))
    return payload["data"]["user"]


def mock():
    return {
        "name": "Anup Ojha", "login": USER,
        "followers": {"totalCount": 42}, "following": {"totalCount": 17},
        "contributionsCollection": {
            "totalCommitContributions": 812, "totalPullRequestContributions": 63,
            "totalIssueContributions": 24, "totalPullRequestReviewContributions": 31,
            "restrictedContributionsCount": 140,
            "contributionCalendar": {"totalContributions": 977}},
        "repositories": {"totalCount": 38, "nodes": [
            {"stargazerCount": 12, "languages": {"edges": [
                {"size": 90000, "node": {"name": "Python"}},
                {"size": 30000, "node": {"name": "TypeScript"}}]}},
            {"stargazerCount": 7, "languages": {"edges": [
                {"size": 40000, "node": {"name": "Python"}},
                {"size": 25000, "node": {"name": "Java"}},
                {"size": 8000, "node": {"name": "HTML"}}]}},
        ]},
    }


def aggregate(u):
    c = u["contributionsCollection"]
    repos = u["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]
    top = [(n, round(100 * s / total, 1)) for n, s in top]
    return {
        "name": u.get("name") or u["login"],
        "contribs": c["contributionCalendar"]["totalContributions"],
        "commits": c["totalCommitContributions"] + c["restrictedContributionsCount"],
        "prs": c["totalPullRequestContributions"],
        "reviews": c["totalPullRequestReviewContributions"],
        "issues": c["totalIssueContributions"],
        "stars": stars,
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "top_langs": top,
    }


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(d):
    # Four headline tiles (left column).
    tiles = [
        ("commits", "commits (1y)"), ("stars", "stars earned"),
        ("prs", "pull requests"), ("repos", "repositories"),
    ]
    tile_svg = []
    tx, ty, tw, th = 34, 70, 172, 82
    for i, (key, label) in enumerate(tiles):
        col, row = i % 2, i // 2
        x = tx + col * (tw + 16)
        y = ty + row * (th + 16)
        begin = 0.15 * i
        tile_svg.append(f"""
    <g opacity="0" transform="translate({x},{y})">
      <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{begin:.2f}s" fill="freeze"/>
      <animateTransform attributeName="transform" type="translate" from="{x},{y+10}" to="{x},{y}" dur="0.5s" begin="{begin:.2f}s" fill="freeze"/>
      <rect class="tile" width="{tw}" height="{th}" rx="10"/>
      <text class="num"   x="16" y="42">{d[key]:,}</text>
      <text class="label" x="16" y="64">{esc(label)}</text>
    </g>""")

    # Language bars (right column).
    bx, by, bw = 438, 92, 300
    bar_svg = [f'<text class="hdr" x="{bx}" y="{by-16}">top languages</text>']
    for i, (name, pct) in enumerate(d["top_langs"]):
        y = by + i * 34
        color = LANG_COLORS.get(name, ACCENTS[i % len(ACCENTS)])
        fill_w = max(4, round(bw * pct / 100))
        begin = 0.4 + 0.12 * i
        bar_svg.append(f"""
    <text class="lang" x="{bx}" y="{y-4}">{esc(name)}</text>
    <text class="pct"  x="{bx+bw}" y="{y-4}" text-anchor="end">{pct}%</text>
    <rect class="track" x="{bx}" y="{y}" width="{bw}" height="8" rx="4"/>
    <rect x="{bx}" y="{y}" width="0" height="8" rx="4" fill="{color}">
      <animate attributeName="width" from="0" to="{fill_w}" dur="1.1s" begin="{begin:.2f}s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1"/>
    </rect>""")
    if not d["top_langs"]:
        bar_svg.append(f'<text class="lang" x="{bx}" y="{by+10}">no public language data</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 300" role="img" aria-label="GitHub stats for {esc(d['name'])}">
  <defs>
    <style>
      :root {{ color-scheme: light dark; }}
      text {{ font-family: 'Fira Code','Cascadia Code',ui-monospace,'SF Mono',Menlo,Consolas,monospace; }}
      .win   {{ fill:#0d1117; stroke:#30363d; }}
      .bar   {{ fill:#161b22; }}
      .barln {{ stroke:#30363d; }}
      .ttl   {{ fill:#8b949e; font-size:14px; }}
      .tile  {{ fill:#161b22; stroke:#30363d; stroke-width:1; }}
      .num   {{ fill:#58e6ff; font-size:30px; font-weight:700; }}
      .label {{ fill:#8b949e; font-size:13px; }}
      .hdr   {{ fill:#bc8cff; font-size:15px; font-weight:700; }}
      .lang  {{ fill:#c9d1d9; font-size:14px; }}
      .pct   {{ fill:#8b949e; font-size:13px; }}
      .track {{ fill:#21262d; }}
      .foot  {{ fill:#6e7681; font-size:12px; }}
      @media (prefers-color-scheme: light) {{
        .win{{fill:#fff;stroke:#d0d7de;}} .bar{{fill:#f6f8fa;}} .barln{{stroke:#d0d7de;}}
        .ttl{{fill:#57606a;}} .tile{{fill:#f6f8fa;stroke:#d0d7de;}} .num{{fill:#0550ae;}}
        .label{{fill:#57606a;}} .hdr{{fill:#8250df;}} .lang{{fill:#1f2328;}} .pct{{fill:#57606a;}}
        .track{{fill:#eaeef2;}} .foot{{fill:#8c959f;}}
      }}
    </style>
  </defs>
  <rect class="win" x="4" y="4" width="812" height="292" rx="12" stroke-width="1.5"/>
  <path class="bar" d="M4 16 a12 12 0 0 1 12 -12 h788 a12 12 0 0 1 12 12 v28 h-812 z"/>
  <line class="barln" x1="4" y1="44" x2="816" y2="44"/>
  <text class="ttl" x="410" y="29" text-anchor="middle">anup@ojha: ~/stats · {d['contribs']:,} contributions this year</text>
  {''.join(tile_svg)}
  {''.join(bar_svg)}
  <text class="foot" x="34" y="284">{d['followers']:,} followers · {d['reviews']:,} reviews · {d['issues']:,} issues · self-generated via GitHub Actions</text>
</svg>
"""


def main():
    d = aggregate(fetch())
    svg = render(d)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT}: {d['commits']} commits, {d['stars']} stars, "
          f"{d['repos']} repos, langs={[n for n,_ in d['top_langs']]}")


if __name__ == "__main__":
    main()
