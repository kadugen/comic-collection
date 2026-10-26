#!/usr/bin/env python3
"""Fetch current ComicBookRealm values for every comic in the sheet.

Writes data/prices.json (what the page shows) and appends today's values to
data/history.json (used for "change over 30 days").
Run:  python3 -I tools/update_prices.py
"""
import csv, io, json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_mapping import API, ROOT, SHEET_CSV, get, row_key  # noqa: E402

COVER = "https://iwt.sfo2.cdn.digitaloceanspaces.com/cbr-covers/{name}_{size}.{ext}"
HISTORY_DAYS = 400


def money(s):
    s = re.sub(r"[^0-9.]", "", s or "")
    return float(s) if s else None


def fetch_comic(comic_id):
    for attempt in range(4):
        try:
            data = json.loads(get(f"{API}/comic/comic_id/{comic_id}/stats/0/callback=?"))
        except Exception:
            data = {}
        if "comic" in data:
            return comic_id, data["comic"]
        time.sleep(5 * (attempt + 1))
    return comic_id, None


def cover_urls(c):
    cov = c.get("cover") or {}
    if cov.get("status") != "approved" or not cov.get("name"):
        return None, None
    sizes = cov.get("sizes", "").split("|")
    large = "xl" if "xl" in sizes else "l"
    return (COVER.format(name=cov["name"], size="s", ext=cov["ext"]),
            COVER.format(name=cov["name"], size=large, ext=cov["ext"]))


def fix_text(s):
    """Undo the API's double-encoded UTF-8 (e.g. 'â\x80¢' -> '•')."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def issue_date(c):
    d = (c or {}).get("issue_date") or ""
    return None if d.startswith("0000") or not d else d


def key_note(desc):
    """First meaningful line of the description, e.g. '1st appearance of ...'."""
    for line in fix_text(desc or "").splitlines():
        line = line.strip().lstrip("•").strip().strip('"')
        if line:
            return line[:140]
    return ""


def main():
    mapping = json.loads((ROOT / "data/mapping.json").read_text())
    rows = list(csv.reader(io.StringIO(get(SHEET_CSV))))[1:]

    ids = sorted({m["comic_id"] for m in mapping.values()})
    with ThreadPoolExecutor(max_workers=6) as pool:
        details = dict(pool.map(fetch_comic, ids))

    comics, total = [], 0.0
    for row in rows:
        row += [""] * (5 - len(row))
        issue, name, co, sheet_value, link = (c.strip() for c in row[:5])
        if not name:
            continue
        m = mapping.get(row_key(issue, name, co))
        c = details.get(m["comic_id"]) if m else None
        value = money(c["pricing"]["current_value"]) if c else None
        source = "ComicBookRealm"
        if value is None:
            value, source = money(sheet_value), "sheet"
        thumb, cover = cover_urls(c) if c else (None, None)
        comics.append({
            "name": name, "issue": issue, "publisher": co,
            "value": value, "source": source,
            "comic_id": m["comic_id"] if m else None,
            "series": m.get("series") if m else None,
            "date": issue_date(c),
            "note": key_note((c or {}).get("description")),
            "thumb": thumb, "cover": cover,
            "url": (f"https://comicbookrealm.com/series/{m['series_id']}/{m['comic_id']}/x#{m['comic_id']}"
                    if m and m.get("series_id") else (link if link.startswith("http") else None)),
        })
        total += value or 0

    now = datetime.now(timezone.utc)
    (ROOT / "data/prices.json").write_text(json.dumps(
        {"updated": now.isoformat(timespec="seconds"), "total": round(total, 2),
         "comics": comics}, indent=1))

    hist_path = ROOT / "data/history.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else {}
    history[now.date().isoformat()] = {
        "total": round(total, 2),
        "values": {c["comic_id"]: c["value"] for c in comics
                   if c["comic_id"] and c["source"] != "sheet"},
    }
    keep = sorted(history)[-HISTORY_DAYS:]
    hist_path.write_text(json.dumps({d: history[d] for d in keep}, separators=(",", ":")))

    missing = sum(1 for i in ids if not details.get(i))
    print(f"{len(comics)} comics, total ${total:,.2f}; {missing} lookups failed")
    return 1 if missing > len(ids) // 2 else 0


if __name__ == "__main__":
    sys.exit(main())
