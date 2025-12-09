#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import os
import sys
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import re
from urllib.parse import urlparse, urlunparse
from email.utils import parsedate_to_datetime
import hashlib

# -----------------------------
# CONFIG
# -----------------------------
FEEDS = [
    "https://politepol.com/fd/lRzLqNhRg2jV.xml",
    "https://politepol.com/fd/LWVzWA8NSHfJ.xml",
    "https://evilgodfahim.github.io/juop/editorial_news.xml",
    "https://evilgodfahim.github.io/bbop/feed.xml",
    "https://evilgodfahim.github.io/bdpratidin-rss/feed.xml",
    "https://fetchrss.com/feed/aLNkZSZkMOtSaLNkNF2oqA-i.rss",
    "https://politepol.com/fd/4LWXWOY5wPR9.xml",
    "https://politepol.com/fd/VnoJt9i4mZPJ.xml",
    "https://evilgodfahim.github.io/sop/opinion_feed.xml",
    "https://politepol.com/fd/tqu8P8uIlNm1.xml",
    "https://feeds.bbci.co.uk/bengali/rss.xml",
    "https://politepol.com/fd/YgbESpqhLwdK.xml",
    "https://politepol.com/fd/TnjwLaSLd1M8.xml",
    "https://politepol.com/fd/e0zKTeKoRpXa.xml",
    "https://evilgodfahim.github.io/kk/opinion.xml",
    "https://politepol.com/fd/1yC3YJpL3i6t.xml",
    "https://politepol.com/fd/aPXIv1Q7cs7S.xml",
    "https://politepol.com/fd/eYS0c238EjkY.xml",
    "https://evilgodfahim.github.io/banglanews/opinion.xml",
    "https://evilgodfahim.github.io/kalbela/opinion.xml",
    "https://evilgodfahim.github.io/samakal/articles.xml",
    "https://politepol.com/fd/dwg0cNjfFTLe.xml",
    "https://politepol.com/fd/RW7B9eQ8SuQ8.xml",
    "https://politepol.com/fd/Om635UbkdlGQ.xml",
    "https://politepol.com/fd/iBikrmLHw51t.xml",
    "https://politepol.com/fd/joNpOlIQpxws.xml",
    "https://politepol.com/fd/xwWyLagKzYe1.xml",
    "https://evilgodfahim.github.io/juop/tp_editorial_news.xml",
    "https://politepol.com/fd/OM5MULjADosd.xml",
    "https://politepol.com/fd/FvaPzwOZSVaI.xml",
    "https://politepol.com/fd/CxsnfXBZ1EMn.xml",
    "https://politepol.com/fd/MMd5ai243dRY.xml",
    "https://politepol.com/fd/JULgDpaw0b8L.xml",
    "https://politepol.com/fd/fDXZXBMGFPEK.xml",
    "https://politepol.com/fd/pQRqQHo2RqLj.xml",
    "https://evilgodfahim.github.io/ad/articles.xml",
    "https://evilgodfahim.github.io/pb/articles.xml",
    "https://politepol.com/fd/bdnPXYy1YR1g.xml",
    "https://evilgodfahim.github.io/bt/columns.xml",
    "https://politepol.com/fd/l7Izgmv6b2LN.xml",
    "https://politepol.com/fd/WNWYGwauoZ66.xml",
    "https://evilgodfahim.github.io/bang24/articles.xml",
    "https://politepol.com/fd/q9DuibYN2O9z.xml",
    "https://politepol.com/fd/fssrDtv1qcWq.xml",
    "https://politepol.com/fd/sVAvn5KqTJ1i.xml",
    "https://politepol.com/fd/AQoFlVz07XoG.xml",
    "https://politepol.com/fd/jFlLPOQ6vEKp.xml",
    "https://politepol.com/fd/AVAsSOSdLHt6.xml",
    "https://politepol.com/fd/2pU3mHPVSGKg.xml",
    "https://politepol.com/fd/akNUGmmGEQiU.xml",
    "https://politepol.com/fd/4Sxhoa7GsEOT.xml",
    "https://evilgodfahim.github.io/dp/feed.xml",
    "https://politepol.com/fd/h5dpg9swLxDi.xml",
    "https://politepol.com/fd/O6MpruOsm40B.xml",
    "https://politepol.com/fd/uZUiPeYnZYfl.xml",
    "https://politepol.com/fd/87W4AhwO5swk.xml"
]

MASTER_FILE = "feed_master.xml"
DAILY_FILE = "daily_feed.xml"
DAILY_FILE_2 = "daily_feed_2.xml"
LAST_SEEN_FILE = "last_seen.json"

MAX_ITEMS = 1000
BD_OFFSET = 6
LOOKBACK_HOURS = 48
LINK_RETENTION_DAYS = 7

# ----------------------------------------------------
# NORMALIZE LINKS
# ----------------------------------------------------
def normalize_link(url):
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # collapse duplicated path halves
    try:
        seg = path.strip("/").split("/")
        n = len(seg)
        if n >= 2 and n % 2 == 0:
            half = n // 2
            if seg[:half] == seg[half:]:
                seg = seg[:half]
                path = "/" + "/".join(seg)
    except:
        pass

    return urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

# ----------------------------------------------------
# SOURCE NAME
# ----------------------------------------------------
def extract_source(link):
    try:
        host = urlparse(link).netloc.lower().replace("www.", "")
        parts = host.split(".")
        return parts[0] if len(parts) >= 2 else host
    except:
        return "unknown"

# ----------------------------------------------------
# DATE
# ----------------------------------------------------
def parse_date(entry):
    for f in ("published_parsed", "updated_parsed", "created_parsed"):
        try:
            t = entry.get(f)
            if t:
                return datetime(*t[:6], tzinfo=timezone.utc)
        except:
            pass

    for f in ("published", "updated", "created", "pubDate"):
        val = entry.get(f)
        if val:
            try:
                dt = parsedate_to_datetime(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except:
                continue

    return datetime.now(timezone.utc)

# ----------------------------------------------------
# LOAD EXISTING
# ----------------------------------------------------
def load_existing(path):
    if not os.path.exists(path):
        return []

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except:
        return []

    out = []
    for itm in root.findall(".//item"):
        try:
            t = itm.find("title")
            l = itm.find("link")
            d = itm.find("description")
            p = itm.find("pubDate")

            title = t.text.strip() if t is not None else ""
            link = normalize_link(l.text) if l is not None else ""
            desc = d.text if d is not None else ""

            if p is not None:
                dt = parsedate_to_datetime(p.text)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            out.append({
                "title": title,
                "link": link,
                "description": desc,
                "pubDate": dt
            })
        except:
            continue
    return out

# ----------------------------------------------------
# WRITE XML
# ----------------------------------------------------
def write_rss(items, path, title="Feed"):
    root = ET.Element("rss", version="2.0")
    ch = ET.SubElement(root, "channel")
    ET.SubElement(ch, "title").text = title
    ET.SubElement(ch, "link").text = "https://evilgodfahim.github.io/"
    ET.SubElement(ch, "description").text = title

    for it in items:
        node = ET.SubElement(ch, "item")
        ET.SubElement(node, "title").text = it["title"]
        ET.SubElement(node, "link").text = it["link"]
        ET.SubElement(node, "description").text = it["description"]
        ET.SubElement(node, "pubDate").text = it["pubDate"].strftime("%a, %d %b %Y %H:%M:%S %z")

    xml = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)

# ----------------------------------------------------
# LAST SEEN
# ----------------------------------------------------
def load_last_seen():
    if not os.path.exists(LAST_SEEN_FILE):
        return {"last_seen": None, "processed_links": set()}
    try:
        with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        dt = d.get("last_seen")
        return {
            "last_seen": datetime.fromisoformat(dt) if dt else None,
            "processed_links": set(d.get("processed_links", []))
        }
    except:
        return {"last_seen": None, "processed_links": set()}

def save_last_seen(dt, processed, master_items):
    cutoff = dt - timedelta(days=LINK_RETENTION_DAYS)
    recent = {i["link"] for i in master_items if i["pubDate"] > cutoff}
    keep = [l for l in processed if l in recent]

    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "last_seen": dt.isoformat(),
            "processed_links": keep
        }, f, indent=2)

# ----------------------------------------------------
# UNIQUE HASH (title + link)
# ----------------------------------------------------
def make_hash(title, link):
    base = (title.strip() + "||" + link.strip()).encode("utf-8", "ignore")
    return hashlib.sha256(base).hexdigest()

# ----------------------------------------------------
# MASTER UPDATE
# ----------------------------------------------------
def update_master():
    print("[master] updating")

    existing = load_existing(MASTER_FILE)
    seen_hash = {make_hash(i["title"], i["link"]) for i in existing}

    new_list = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries:
                raw_link = e.get("link", "")
                link = normalize_link(raw_link)

                if "evilgodfahim" in link:
                    continue

                title_raw = e.get("title", "").strip()
                src = extract_source(link)
                final_title = f"{title_raw}. [ {src} ]" if title_raw else f"No Title. [ {src} ]"

                h = make_hash(final_title, link)
                if h in seen_hash:
                    continue

                desc = e.get("summary", "")

                if not desc:
                    content = e.get("content")
                    if isinstance(content, list) and content:
                        v = content[0]
                        if isinstance(v, dict):
                            desc = v.get("value", "")
                        else:
                            desc = getattr(v, "value", "")
                    elif isinstance(content, str):
                        desc = content

                pub = parse_date(e)

                item = {
                    "title": final_title,
                    "link": link,
                    "description": desc,
                    "pubDate": pub
                }

                new_list.append(item)
                seen_hash.add(h)

        except Exception as err:
            print("[ERROR]", url, err)

    all_items = existing + new_list
    all_items.sort(key=lambda x: x["pubDate"], reverse=True)
    all_items = all_items[:MAX_ITEMS]

    if not all_items:
        all_items = [{
            "title": "No articles yet",
            "link": "https://evilgodfahim.github.io/",
            "description": "Empty",
            "pubDate": datetime.now(timezone.utc)
        }]

    write_rss(all_items, MASTER_FILE, "Master Feed")
    print("[master] done:", len(all_items), "items")

# ----------------------------------------------------
# DAILY UPDATE
# ----------------------------------------------------
def update_daily():
    print("[daily] updating")

    bd = timezone(timedelta(hours=BD_OFFSET))

    last_data = load_last_seen()
    last_seen = last_data["last_seen"]
    processed = last_data["processed_links"]

    if last_seen:
        lookback = last_seen - timedelta(hours=LOOKBACK_HOURS)
    else:
        lookback = None

    master = load_existing(MASTER_FILE)

    new_items = []
    for it in master:
        link = it["link"]
        pub = it["pubDate"].astimezone(bd)

        if link in processed:
            continue

        if not lookback or pub > lookback:
            new_items.append(it)
            processed.add(link)

    if not new_items:
        placeholder = [{
            "title": "No new articles today",
            "link": "https://evilgodfahim.github.io/",
            "description": "Empty",
            "pubDate": datetime.now(timezone.utc)
        }]

        write_rss(placeholder, DAILY_FILE, "Daily Feed")
        write_rss([], DAILY_FILE_2, "Daily Feed Extra")

        save_last_seen(placeholder[0]["pubDate"], processed, master)
        return

    new_items.sort(key=lambda x: x["pubDate"], reverse=True)

    first = new_items[:100]
    second = new_items[100:]

    write_rss(first, DAILY_FILE, "Daily Feed")
    write_rss(second, DAILY_FILE_2, "Daily Feed Extra")

    newest = max(i["pubDate"] for i in new_items)
    save_last_seen(newest, processed, master)

    print("[daily] done")

# ----------------------------------------------------
# MAIN
# ----------------------------------------------------
if __name__ == "__main__":
    a = sys.argv[1:]
    if "--master-only" in a:
        update_master()
    elif "--daily-only" in a:
        update_daily()
    else:
        update_master()
        update_daily()