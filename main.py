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

# -----------------------------
# CONFIGURATION
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
    "https://politepol.com/fd/87W4AhwO5swk.xml",
"https://politepol.com/fd/b1zBxlQviouX.xml",
"https://politepol.com/fd/xxMR0SLCHBuN.xml",
"https://evilgodfahim.github.io/edi/articles.xml",
"https://evilgodfahim.github.io/bdp/articles.xml"
]

MASTER_FILE = "feed_master.xml"
DAILY_FILE = "daily_feed.xml"
DAILY_FILE_2 = "daily_feed_2.xml"
LAST_SEEN_FILE = "last_seen.json"

MAX_ITEMS = 1000
BD_OFFSET = 6
LOOKBACK_HOURS = 48
LINK_RETENTION_DAYS = 7

# -----------------------------
# LINK NORMALIZER
# -----------------------------
def normalize_link(url):
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # keep query/fragment/params — restore them into normalized link
    # attempt to collapse duplicated halves in path like /a/b/a/b -> /a/b
    try:
        segments = path.strip("/").split("/")
        n = len(segments)
        if n >= 2 and n % 2 == 0:
            half = n // 2
            if segments[:half] == segments[half:]:
                segments = segments[:half]
                path = "/" + "/".join(segments)
    except Exception:
        pass

    normalized = urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))
    return normalized

# -----------------------------
# SOURCE EXTRACTOR
# -----------------------------
def extract_source(link):
    try:
        host = urlparse(link).netloc.lower()
        host = host.replace("www.", "")
        parts = host.split(".")
        if len(parts) >= 2:
            return parts[0]
        return host
    except:
        return "unknown"

# -----------------------------
# UTILITIES
# -----------------------------
def parse_date(entry):
    # 1) prefer feedparser parsed tuples
    for f in ("published_parsed", "updated_parsed", "created_parsed"):
        t = None
        try:
            t = entry.get(f) if isinstance(entry, dict) else getattr(entry, f, None)
        except Exception:
            t = None
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass

    # 2) try common string fields with robust parsing
    for key in ("published", "updated", "pubDate", "created"):
        val = None
        try:
            val = entry.get(key) if isinstance(entry, dict) else getattr(entry, key, None)
        except Exception:
            val = None
        if val:
            try:
                dt = parsedate_to_datetime(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue

    # 3) fallback to now (UTC)
    return datetime.now(timezone.utc)

def load_existing(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception:
        return []
    items = []
    for item in root.findall(".//item"):
        try:
            title_node = item.find("title")
            link_node = item.find("link")
            desc_node = item.find("description")
            pub_node = item.find("pubDate")
            title = (title_node.text or "").strip() if title_node is not None else ""
            link = normalize_link(link_node.text or "") if link_node is not None else ""
            desc = desc_node.text or "" if desc_node is not None else ""
            pubDate_text = pub_node.text if pub_node is not None else None
            if pubDate_text:
                try:
                    dt = parsedate_to_datetime(pubDate_text)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    dt = dt.astimezone(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)
            items.append({"title": title, "link": link, "description": desc, "pubDate": dt})
        except Exception:
            continue
    return items

def write_rss(items, file_path, title="Feed"):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = "https://evilgodfahim.github.io/"
    ET.SubElement(channel, "description").text = f"{title} generated by script"

    for item in items:
        it = ET.SubElement(channel, "item")
        ET.SubElement(it, "title").text = item.get("title", "")
        ET.SubElement(it, "link").text = item.get("link", "")
        ET.SubElement(it, "description").text = item.get("description", "")
        pub = item.get("pubDate")
        if isinstance(pub, datetime):
            ET.SubElement(it, "pubDate").text = pub.strftime("%a, %d %b %Y %H:%M:%S %z")
        else:
            ET.SubElement(it, "pubDate").text = str(pub)

    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

# -----------------------------
# ENHANCED LAST SEEN TRACKING
# -----------------------------
def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        try:
            with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_seen_str = data.get("last_seen")
                processed = set(data.get("processed_links", []))
                last_seen_dt = datetime.fromisoformat(last_seen_str) if last_seen_str else None
                return {"last_seen": last_seen_dt, "processed_links": processed}
        except Exception:
            return {"last_seen": None, "processed_links": set()}
    return {"last_seen": None, "processed_links": set()}

def save_last_seen(last_dt, processed_links, master_items):
    cutoff = last_dt - timedelta(days=LINK_RETENTION_DAYS)
    master_links_recent = {
        item["link"] for item in master_items
        if item["pubDate"] > cutoff
    }
    links_to_keep = [link for link in processed_links if link in master_links_recent]

    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "last_seen": last_dt.isoformat(),
            "processed_links": links_to_keep
        }, f, indent=2)

# -----------------------------
# MASTER FEED UPDATE
# -----------------------------
def update_master():
    print("[Updating feed_master.xml]")

    existing = load_existing(MASTER_FILE)

    existing_links = {x["link"] for x in existing}
    existing_titles = {x["title"].strip() for x in existing}

    new_items = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # robust entry access
                raw_link = entry.get("link") if isinstance(entry, dict) else getattr(entry, "link", "")
                link = normalize_link(raw_link)

                # preserve your filter — skip any links that reference your own domain if intended
                if "evilgodfahim" in link:
                    continue

                title_raw = entry.get("title", "") if isinstance(entry, dict) else getattr(entry, "title", "")
                title = title_raw.strip()

                source = extract_source(link)
                final_title = f"{title}. [ {source} ]" if title else f"No Title. [ {source} ]"

                # skip duplicates by link OR by final_title (which includes the source tag)
                if link in existing_links or final_title in existing_titles:
                    continue

                # description: use summary, else content (content:encoded)
                desc = ""
                try:
                    desc = entry.get("summary", "") if isinstance(entry, dict) else getattr(entry, "summary", "")
                except Exception:
                    desc = ""
                if not desc:
                    try:
                        content = entry.get("content") if isinstance(entry, dict) else getattr(entry, "content", None)
                        if content:
                            if isinstance(content, list):
                                first = content[0]
                                if isinstance(first, dict):
                                    desc = first.get("value", "") or ""
                                else:
                                    # some feedparser builds expose objects with .value
                                    desc = getattr(first, "value", "") or ""
                            else:
                                # some feeds put full html in entry.content as a string
                                desc = content if isinstance(content, str) else ""
                    except Exception:
                        desc = ""

                pub_dt = parse_date(entry)

                new_items.append({
                    "title": final_title,
                    "link": link,
                    "description": desc,
                    "pubDate": pub_dt
                })

                existing_links.add(link)
                existing_titles.add(final_title)

        except Exception as e:
            print(f"Error parsing {url}: {e}")

    all_items = existing + new_items
    all_items.sort(key=lambda x: x["pubDate"], reverse=True)
    all_items = all_items[:MAX_ITEMS]

    if not all_items:
        all_items = [{
            "title": "No articles yet",
            "link": "https://evilgodfahim.github.io/",
            "description": "Master feed will populate after first successful fetch.",
            "pubDate": datetime.now(timezone.utc)
        }]

    write_rss(all_items, MASTER_FILE, title="Master Feed (Updated every 30 mins)")
    print(f"✓ feed_master.xml updated with {len(all_items)} items ({len(new_items)} new)")

# -----------------------------
# DAILY FEED UPDATE
# -----------------------------
def update_daily():
    print("[Updating daily_feed.xml with robust tracking]")
    to_zone = timezone(timedelta(hours=BD_OFFSET))

    last_data = load_last_seen()
    last_seen_dt = last_data["last_seen"]
    processed_links = set(last_data["processed_links"])

    if last_seen_dt:
        lookback_dt = last_seen_dt - timedelta(hours=LOOKBACK_HOURS)
    else:
        lookback_dt = None

    master_items = load_existing(MASTER_FILE)
    new_items = []

    for item in master_items:
        link = item["link"]
        pub = item["pubDate"].astimezone(to_zone)

        if link in processed_links:
            continue

        if not lookback_dt or pub > lookback_dt:
            new_items.append(item)
            processed_links.add(link)

    if not new_items:
        placeholder = [{
            "title": "No new articles today",
            "link": "https://evilgodfahim.github.io/",
            "description": "Daily feed will populate after first articles appear.",
            "pubDate": datetime.now(timezone.utc)
        }]

        write_rss(placeholder, DAILY_FILE, title="Daily Feed (Updated 9 AM BD)")
        write_rss([], DAILY_FILE_2, title="Daily Feed Extra (Updated 9 AM BD)")

        last_dt = placeholder[0]["pubDate"]
        save_last_seen(last_dt, processed_links, master_items)
        return

    new_items.sort(key=lambda x: x["pubDate"], reverse=True)

    first_batch = new_items[:100]
    second_batch = new_items[100:]

    write_rss(first_batch, DAILY_FILE, title="Daily Feed (Updated 9 AM BD)")

    if second_batch:
        write_rss(second_batch, DAILY_FILE_2, title="Daily Feed Extra (Updated 9 AM BD)")
    else:
        write_rss([], DAILY_FILE_2, title="Daily Feed Extra (Updated 9 AM BD)")

    last_dt = max([i["pubDate"] for i in new_items])
    save_last_seen(last_dt, processed_links, master_items)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    args = sys.argv[1:]
    if "--master-only" in args:
        update_master()
    elif "--daily-only" in args:
        update_daily()
    else:
        update_master()
        update_daily()