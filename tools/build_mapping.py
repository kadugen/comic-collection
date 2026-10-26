#!/usr/bin/env python3
"""Match each row of the collection sheet to a ComicBookRealm comic_id.

Writes data/mapping.json, which the page uses to fetch live prices.
Re-run after adding comics to the sheet:  python3 -I tools/build_mapping.py

Rows without a ComicBookRealm link (or whose issue string doesn't match
exactly) are resolved through tools/overrides.json, keyed "name|issue|publisher"
(lowercase). An override gives a series_id (plus "issue" if the label differs),
or an exact comic_id + series_id, or {"skip": true} to keep the sheet's value.
"""
import csv, io, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEET_CSV = ("https://docs.google.com/spreadsheets/d/"
             "1jF_oVuxJko2OIman4ypQ1jRx9sjJdK035rpmuqM5dDI/export?format=csv")
API = "https://comicbookrealm.com/api/11fa99d0"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://comicbookrealm.com/"}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


CACHE = ROOT / "tools/.cache"


def api(path):
    cached = CACHE / (re.sub(r"\W", "_", path) + ".json")
    if cached.exists():
        return json.loads(cached.read_text())
    for attempt in range(8):
        time.sleep(0.5)  # be gentle with an unofficial API
        data = json.loads(get(f"{API}/{path}/callback=?"))
        if data.get("error") != "Exceeded API Limits":
            CACHE.mkdir(exist_ok=True)
            cached.write_text(json.dumps(data))
            return data
        wait = 15 * (attempt + 1)
        print(f"  rate limited; waiting {wait}s", file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError(f"still rate limited: {path}")


def row_key(issue, name, co):
    return "|".join(s.strip().lower() for s in (name, issue, co))


_series_cache = {}


def series_issues(series_id):
    """issue string (lowercase) -> comic dict, across every type and variant."""
    if series_id in _series_cache:
        return _series_cache[series_id]
    info = api(f"series/series_id/{series_id}")["series"]
    out = {"_title": info["title"], "_publisher": info["publisher"]["publisher_name"]}
    for type_id, t in (info.get("type_breakdown") or {}).items():
        for offset in range(0, int(t["count"]), 100):
            comics = api(f"comics/series_id/{series_id}/type_id/{type_id}/offset/{offset}")
            for c in (comics.get("series", {}).get("comics") or {}).values():
                for entry in [c, *(c.get("variants") or {}).values()]:
                    label = entry["issue"].lower()
                    if type_id != "1":
                        label = f"{t['type'].lower()} {label}"
                    out.setdefault(label, entry)
    _series_cache[series_id] = out
    return out


def main():
    overrides = json.loads((ROOT / "tools/overrides.json").read_text())
    rows = list(csv.reader(io.StringIO(get(SHEET_CSV))))[1:]
    map_path = ROOT / "data/mapping.json"
    old = json.loads(map_path.read_text()) if map_path.exists() else {}
    mapping, unmatched = {}, []
    for row in rows:
        row += [""] * (5 - len(row))
        issue, name, co, _value, link = (c.strip() for c in row[:5])
        if not name:
            continue
        key = row_key(issue, name, co)
        if key in mapping:
            continue
        if key in old:
            mapping[key] = old[key]
            continue
        ov = overrides.get(key, {})
        if ov.get("skip"):
            continue
        if "comic_id" in ov:
            mapping[key] = {"comic_id": str(ov["comic_id"]), "series_id": str(ov["series_id"])}
            continue
        m = re.search(r"comicbookrealm\.com/series/(\d+)", link)
        series_id = ov.get("series_id") or (m and m.group(1))
        if not series_id:
            unmatched.append((key, "no ComicBookRealm series"))
            continue
        issues = series_issues(str(series_id))
        want = str(ov.get("issue", issue)).lower()
        hit = issues.get(want)
        if not hit:
            unmatched.append((key, f"series {series_id} ({issues['_title']}) has no issue '{want}'"))
            continue
        mapping[key] = {"comic_id": hit["comic_id"], "series_id": str(series_id),
                        "series": issues["_title"]}

    (ROOT / "data").mkdir(exist_ok=True)
    map_path.write_text(json.dumps(mapping, indent=1, sort_keys=True))
    print(f"matched {len(mapping)} comics")
    for key, why in unmatched:
        print(f"UNMATCHED  {key}  -> {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
