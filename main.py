#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import hashlib
import os
import sys
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import re
from urllib.parse import urlparse, urlunparse
from email.utils import parsedate_to_datetime
import requests

# -----------------------------
# CONFIGURATION
# -----------------------------
FEEDS = [
    "https://politepaul.com/fd/lRzLqNhRg2jV.xml",
    "https://evilgodfahim.github.io/inqifaq/feeds/feed.xml",
    "https://evilgodfahim.github.io/salo/feeds/feed.xml",
    "https://evilgodfahim.github.io/ch/thoughts.xml",
    "https://evilgodfahim.github.io/pa/opinion.xml",
    "https://evilgodfahim.github.io/ch/analysis.xml",
    "https://evilgodfahim.github.io/ch/explainer.xml",
    "https://politepaul.com/fd/LWVzWA8NSHfJ.xml",
    "https://evilgodfahim.github.io/prothomalo-rss/opinion.xml",
    "https://evilgodfahim.github.io/juop/editorial_news.xml",
    "https://evilgodfahim.github.io/bbop/feed.xml",
    "https://evilgodfahim.github.io/bdpratidin-rss/feed.xml",
    "https://fetchrss.com/feed/aLNkZSZkMOtSaLNkNF2oqA-i.rss",
    "https://politepaul.com/fd/4LWXWOY5wPR9.xml",
    "https://politepaul.com/fd/VnoJt9i4mZPJ.xml",
    "https://evilgodfahim.github.io/sop/opinion_feed.xml",
    "https://politepaul.com/fd/tqu8P8uIlNm1.xml",
    "https://feeds.bbci.co.uk/bengali/rss.xml",
    "https://politepaul.com/fd/YgbESpqhLwdK.xml",
    "https://politepaul.com/fd/TnjwLaSLd1M8.xml",
    "https://politepaul.com/fd/e0zKTeKoRpXa.xml",
    "https://evilgodfahim.github.io/kk/opinion.xml",
    "https://politepaul.com/fd/1yC3YJpL3i6t.xml",
    "https://politepaul.com/fd/aPXIv1Q7cs7S.xml",
    "https://politepaul.com/fd/eYS0c238EjkY.xml",
    "https://evilgodfahim.github.io/banglanews/opinion.xml",
    "https://evilgodfahim.github.io/kalbela/opinion.xml",
    "https://evilgodfahim.github.io/samakal/articles.xml",
    "https://evilgodfahim.github.io/ad/articles.xml",
    "https://politepaul.com/fd/dwg0cNjfFTLe.xml",
    "https://politepaul.com/fd/RW7B9eQ8SuQ8.xml",
    "https://politepaul.com/fd/Om635UbkdlGQ.xml",
    "https://politepaul.com/fd/iBikrmLHw51t.xml",
    "https://politepaul.com/fd/joNpOlIQpxws.xml",
    "https://politepaul.com/fd/xwWyLagKzYe1.xml",
    "https://evilgodfahim.github.io/juop/tp_editorial_news.xml",
    "https://politepaul.com/fd/OM5MULjADosd.xml",
    "https://politepaul.com/fd/FvaPzwOZSVaI.xml",
    "https://politepaul.com/fd/CxsnfXBZ1EMn.xml",
    "https://politepaul.com/fd/MMd5ai243dRY.xml",
    "https://politepaul.com/fd/JULgDpaw0b8L.xml",
    "https://politepaul.com/fd/fDXZXBMGFPEK.xml",
    "https://politepaul.com/fd/pQRqQHo2RqLj.xml",
    "https://evilgodfahim.github.io/ad/articles.xml",
    "https://evilgodfahim.github.io/pb/articles.xml",
    "https://politepaul.com/fd/bdnPXYy1YR1g.xml",
    "https://evilgodfahim.github.io/bt/columns.xml",
    "https://politepaul.com/fd/l7Izgmv6b2LN.xml",
    "https://politepaul.com/fd/WNWYGwauoZ66.xml",
    "https://evilgodfahim.github.io/bang24/articles.xml",
    "https://politepaul.com/fd/q9DuibYN2O9z.xml",
    "https://politepaul.com/fd/fssrDtv1qcWq.xml",
    "https://politepaul.com/fd/sVAvn5KqTJ1i.xml",
    "https://politepaul.com/fd/AQoFlVz07XoG.xml",
    "https://evilgodfahim.github.io/dp/feed.xml",
    "https://politepaul.com/fd/h5dpg9swLxDi.xml",
    "https://politepaul.com/fd/O6MpruOsm40B.xml",
    "https://politepaul.com/fd/uZUiPeYnZYfl.xml",
    "https://politepaul.com/fd/87W4AhwO5swk.xml",
    "https://politepaul.com/fd/b1zBxlQviouX.xml",
    "https://politepaul.com/fd/xxMR0SLCHBuN.xml",
    "https://evilgodfahim.github.io/edi/articles.xml",
    "https://evilgodfahim.github.io/bdp/articles.xml",
    "https://evilgodfahim.github.io/dr/opinion.xml",
]

MASTER_FILE      = "feed_master.xml"
DAILY_FILE       = "daily_feed.xml"
DAILY_FILE_2     = "daily_feed_2.xml"
LAST_SEEN_FILE   = "last_seen.json"
MASTER_SEEN_FILE = "master_seen_links.json"   # persistent master dedup
SOURCES_FILE     = "sources.txt"

MAX_ITEMS           = 1000
BD_OFFSET           = 6
LOOKBACK_HOURS      = 48
LINK_RETENTION_DAYS = 365
FETCH_TIMEOUT       = 15  # seconds per feed

# -----------------------------
# BLOCKLIST
# -----------------------------
BLOCKED_HOSTS = {"shomoyeralo.com"}


def is_blocked(link):
    if not link:
        return False
    try:
        host = urlparse(link).netloc.lower()
        for b in BLOCKED_HOSTS:
            if b in host:
                return True
    except Exception:
        pass
    return False


# -----------------------------
# LINK NORMALIZER
# -----------------------------
def normalize_link(url):
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
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
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))


# -----------------------------
# SOURCE EXTRACTOR
# -----------------------------
def extract_source(link):
    try:
        host = urlparse(link).netloc.lower().replace("www.", "")
        parts = host.split(".")
        return parts[0] if len(parts) >= 2 else host
    except Exception:
        return "unknown"


# -----------------------------
# DATE PARSER
# -----------------------------
def parse_date(entry):
    for f in ("published_parsed", "updated_parsed", "created_parsed"):
        t = None
        try:
            t = entry.get(f) if isinstance(entry, dict) else getattr(entry, f, None)
        except Exception:
            pass
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass

    for key in ("published", "updated", "pubDate", "created"):
        val = None
        try:
            val = entry.get(key) if isinstance(entry, dict) else getattr(entry, key, None)
        except Exception:
            pass
        if val:
            try:
                dt = parsedate_to_datetime(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue

    return datetime.now(timezone.utc)


# -----------------------------
# PERSISTENT MASTER SEEN LINKS
# Tracks every link ever added to master, with timestamps.
# Survives the MAX_ITEMS cap — items evicted from master XML
# won't be re-added on future runs.
# -----------------------------

def load_master_seen():
    """
    Returns (seen_dict, seen_set).
      seen_dict: {normalized_link: iso_timestamp}  — for saving back
      seen_set:  set of links                      — for fast lookup
    """
    if not os.path.exists(MASTER_SEEN_FILE):
        return {}, set()
    try:
        with open(MASTER_SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=LINK_RETENTION_DAYS)).isoformat()
        raw = data.get("seen_links", {})
        # Migrate old list format if needed
        if isinstance(raw, list):
            now_iso = datetime.now(timezone.utc).isoformat()
            seen = {link: now_iso for link in raw}
        else:
            seen = {link: ts for link, ts in raw.items() if ts >= cutoff}
        return seen, set(seen.keys())
    except Exception:
        return {}, set()


def save_master_seen(seen: dict):
    """Prune to LINK_RETENTION_DAYS and persist."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=LINK_RETENTION_DAYS)).isoformat()
    pruned = {link: ts for link, ts in seen.items() if ts >= cutoff}
    with open(MASTER_SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen_links": pruned}, f, indent=2)


# -----------------------------
# LOAD EXISTING
# -----------------------------
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
            link_node  = item.find("link")
            desc_node  = item.find("description")
            pub_node   = item.find("pubDate")

            title = (title_node.text or "").strip() if title_node is not None else ""
            link  = normalize_link(link_node.text or "") if link_node is not None else ""

            if is_blocked(link):
                continue

            desc = (
                "".join(desc_node.itertext())
                if desc_node is not None else ""
            )

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


# -----------------------------
# DESCRIPTION HELPERS
# -----------------------------

def get_description(entry):
    content_html = ""
    try:
        content_list = (
            entry.get("content") if isinstance(entry, dict)
            else getattr(entry, "content", None)
        )
        if content_list:
            if isinstance(content_list, list):
                for c in content_list:
                    val = (
                        (c.get("value") if isinstance(c, dict) else getattr(c, "value", None))
                        or ""
                    )
                    if len(val) > len(content_html):
                        content_html = val
            elif isinstance(content_list, str):
                content_html = content_list
    except Exception:
        pass

    summary = ""
    try:
        summary = (
            (entry.get("summary") if isinstance(entry, dict) else getattr(entry, "summary", None))
            or ""
        )
    except Exception:
        pass

    return content_html if len(content_html) >= len(summary) else summary


def get_thumbnail(entry):
    # 1. media:thumbnail
    try:
        thumbs = (
            entry.get("media_thumbnail") if isinstance(entry, dict)
            else getattr(entry, "media_thumbnail", None)
        )
        if thumbs:
            t = thumbs[0] if isinstance(thumbs, list) else thumbs
            url = (t.get("url") if isinstance(t, dict) else getattr(t, "url", None)) or ""
            if url:
                return url
    except Exception:
        pass

    # 2. media:content
    try:
        media = (
            entry.get("media_content") if isinstance(entry, dict)
            else getattr(entry, "media_content", None)
        )
        if media:
            for m in (media if isinstance(media, list) else [media]):
                url = (m.get("url") if isinstance(m, dict) else getattr(m, "url", None)) or ""
                if url:
                    return url
    except Exception:
        pass

    # 3. enclosures — images only
    try:
        enc = (
            entry.get("enclosures") if isinstance(entry, dict)
            else getattr(entry, "enclosures", None)
        )
        if enc:
            for e in (enc if isinstance(enc, list) else [enc]):
                url = (
                    (e.get("url") or e.get("href", "")) if isinstance(e, dict)
                    else getattr(e, "url", getattr(e, "href", ""))
                ) or ""
                etype = (
                    (e.get("type") if isinstance(e, dict) else getattr(e, "type", None))
                    or ""
                )
                if url and "image" in etype:
                    return url
    except Exception:
        pass

    return ""


def build_description(entry, link):
    body  = get_description(entry)
    thumb = get_thumbnail(entry)

    has_img  = bool(re.search(r"<img\b", body, re.IGNORECASE)) if body else False
    has_more = ("more_link" in body or "বিস্তারিত" in body) if body else False

    parts = []
    if thumb and not has_img:
        parts.append(
            f'<img src="{thumb}" style="float: left; margin: 0 10px 10px 0;" width="150" />'
        )
    if body:
        parts.append(body)
    if link and not has_more:
        parts.append(f'<a class="more_link" href="{link}">বিস্তারিত</a>')

    return "\n".join(parts)


# -----------------------------
# GUID HELPER
# -----------------------------

def make_guid(link):
    return hashlib.md5(link.encode("utf-8")).hexdigest()


# -----------------------------
# WRITE RSS
# -----------------------------

def write_rss(items, file_path, title="Feed"):
    filtered = [i for i in items if not is_blocked(i.get("link", ""))]

    impl   = minidom.getDOMImplementation()
    doc    = impl.createDocument(None, "rss", None)
    rss_el = doc.documentElement
    rss_el.setAttribute("version", "2.0")

    channel = doc.createElement("channel")
    rss_el.appendChild(channel)

    def add_text(parent, tag, value):
        el = doc.createElement(tag)
        el.appendChild(doc.createTextNode(value or ""))
        parent.appendChild(el)

    def add_cdata(parent, tag, value):
        el  = doc.createElement(tag)
        raw = (value or "").strip()
        if raw:
            parts  = raw.split("]]>")
            last_i = len(parts) - 1
            for i, part in enumerate(parts):
                if part:
                    el.appendChild(doc.createCDATASection(part))
                if i < last_i:
                    el.appendChild(doc.createTextNode("]]>"))
        parent.appendChild(el)

    add_text(channel, "title", title)
    add_text(channel, "link", "https://evilgodfahim.github.io/")
    add_text(channel, "description", f"{title} generated by script")

    for item in filtered:
        it = doc.createElement("item")

        add_cdata(it, "title", item.get("title", ""))
        add_text(it, "link", item.get("link", ""))
        add_cdata(it, "description", item.get("description", ""))

        pub = item.get("pubDate")
        pub_str = (
            pub.strftime("%a, %d %b %Y %H:%M:%S %z")
            if isinstance(pub, datetime) else str(pub or "")
        )
        add_text(it, "pubDate", pub_str)

        guid_el = doc.createElement("guid")
        guid_el.setAttribute("isPermaLink", "false")
        guid_el.appendChild(doc.createTextNode(make_guid(item.get("link", ""))))
        it.appendChild(guid_el)

        channel.appendChild(it)

    raw_xml   = doc.toprettyxml(indent="  ")
    clean_xml = "\n".join(line for line in raw_xml.splitlines() if line.strip())
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(clean_xml + "\n")


# -----------------------------
# LAST SEEN TRACKING (daily feed)
# -----------------------------

def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        try:
            with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_seen_str = data.get("last_seen")
                processed     = set(data.get("processed_links", []))
                last_seen_dt  = datetime.fromisoformat(last_seen_str) if last_seen_str else None
                return {"last_seen": last_seen_dt, "processed_links": processed}
        except Exception:
            return {"last_seen": None, "processed_links": set()}
    return {"last_seen": None, "processed_links": set()}


def save_last_seen(last_dt, processed_links, master_items):
    cutoff = last_dt - timedelta(days=LINK_RETENTION_DAYS)
    master_links_recent = {
        item["link"] for item in master_items
        if item["pubDate"] > cutoff and not is_blocked(item.get("link", ""))
    }
    links_to_keep = [link for link in processed_links if link in master_links_recent]
    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"last_seen": last_dt.isoformat(), "processed_links": links_to_keep},
            f, indent=2,
        )


# -----------------------------
# FEED FETCHER
# -----------------------------

def fetch_feed(url, timeout=FETCH_TIMEOUT):
    """
    Returns (feed, warn_str | None).
    feed is None on hard failure — caller should skip.
    """
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; feedparser/6.0)",
                "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
            },
            allow_redirects=True,
        )
    except requests.exceptions.Timeout:
        return None, f"timeout after {timeout}s"
    except requests.exceptions.ConnectionError as e:
        return None, f"connection error: {e}"
    except requests.exceptions.RequestException as e:
        return None, f"request error: {e}"

    if resp.status_code >= 400:
        return None, f"HTTP {resp.status_code}"

    feed = feedparser.parse(resp.content)

    if feed.bozo:
        exc = getattr(feed, "bozo_exception", "unknown")
        if not feed.entries:
            return None, f"malformed XML, 0 entries recoverable: {exc}"
        return feed, f"malformed XML, {len(feed.entries)} entries recovered: {exc}"

    return feed, None


# -----------------------------
# MASTER FEED UPDATE
# -----------------------------

def update_master():
    print("[Updating feed_master.xml]")

    existing        = load_existing(MASTER_FILE)
    existing_links  = {x["link"] for x in existing}
    existing_titles = {x["title"].strip() for x in existing}

    # Load persistent seen links — these survive the MAX_ITEMS cap.
    # Union with current master so both sources guard against re-addition.
    master_seen, master_seen_links = load_master_seen()
    all_known_links = existing_links | master_seen_links

    now_iso   = datetime.now(timezone.utc).isoformat()
    new_items = []

    ok_count = warn_count = skip_count = 0

    for url in FEEDS:
        feed, warn = fetch_feed(url)

        if feed is None:
            skip_count += 1
            print(f"  [SKIP] {url}")
            print(f"         {warn}")
            continue

        if warn:
            warn_count += 1
            print(f"  [WARN] {url}")
            print(f"         {warn}")
        else:
            ok_count += 1

        added = skipped_dup = skipped_blocked = skipped_self = 0

        for entry in feed.entries:
            raw_link = (
                entry.get("link") if isinstance(entry, dict)
                else getattr(entry, "link", "")
            ) or ""
            link = normalize_link(raw_link)

            if is_blocked(link):
                skipped_blocked += 1
                continue
            if "evilgodfahim" in link:
                skipped_self += 1
                continue

            title_raw = (
                entry.get("title", "") if isinstance(entry, dict)
                else getattr(entry, "title", "")
            ) or ""
            title       = title_raw.strip()
            source      = extract_source(link)
            final_title = f"{title}. [ {source} ]" if title else f"No Title. [ {source} ]"

            # Dedup against both persistent seen AND current master titles
            if link in all_known_links or final_title in existing_titles:
                skipped_dup += 1
                continue

            desc   = build_description(entry, link)
            pub_dt = parse_date(entry)

            new_items.append({
                "title":       final_title,
                "link":        link,
                "description": desc,
                "pubDate":     pub_dt,
            })
            all_known_links.add(link)
            existing_titles.add(final_title)
            master_seen[link] = now_iso   # mark as seen persistently
            added += 1

        print(
            f"  [OK]   {url}\n"
            f"         entries={len(feed.entries)}"
            f"  new={added}  dup={skipped_dup}"
            f"  blocked={skipped_blocked}  self={skipped_self}"
        )

    print(
        f"\n  feeds: {ok_count} ok / {warn_count} warn / {skip_count} skipped"
        f" / {len(FEEDS)} total"
    )

    # Persist seen links before trimming — so every processed link is remembered
    # even if it gets evicted from master by the MAX_ITEMS cap.
    save_master_seen(master_seen)

    all_items = existing + new_items
    all_items = [i for i in all_items if not is_blocked(i.get("link", ""))]
    all_items.sort(key=lambda x: x["pubDate"], reverse=True)
    all_items = all_items[:MAX_ITEMS]

    if not all_items:
        all_items = [{
            "title":       "No articles yet",
            "link":        "https://evilgodfahim.github.io/",
            "description": "Master feed will populate after first successful fetch.",
            "pubDate":     datetime.now(timezone.utc),
        }]

    write_rss(all_items, MASTER_FILE, title="Master Feed (Updated every 30 mins)")
    print(f"✓ feed_master.xml updated with {len(all_items)} items ({len(new_items)} new)")


# -----------------------------
# DAILY FEED UPDATE
# -----------------------------

def update_daily():
    print("[Updating daily_feed.xml with robust tracking]")
    to_zone = timezone(timedelta(hours=BD_OFFSET))

    last_data       = load_last_seen()
    last_seen_dt    = last_data["last_seen"]
    processed_links = set(last_data["processed_links"])

    lookback_dt = (last_seen_dt - timedelta(hours=LOOKBACK_HOURS)) if last_seen_dt else None

    master_items = load_existing(MASTER_FILE)
    master_items = [m for m in master_items if not is_blocked(m.get("link", ""))]

    new_items = []
    for item in master_items:
        link = item["link"]
        pub  = item["pubDate"].astimezone(to_zone)
        if link in processed_links:
            continue
        if not lookback_dt or pub > lookback_dt:
            new_items.append(item)
            processed_links.add(link)

    if not new_items:
        placeholder = [{
            "title":       "No new articles today",
            "link":        "https://evilgodfahim.github.io/",
            "description": "Daily feed will populate after first articles appear.",
            "pubDate":     datetime.now(timezone.utc),
        }]
        write_rss(placeholder, DAILY_FILE, title="Daily Feed (Updated 9 AM BD)")
        write_rss([], DAILY_FILE_2, title="Daily Feed Extra (Updated 9 AM BD)")
        save_last_seen(placeholder[0]["pubDate"], processed_links, master_items)
        return

    new_items.sort(key=lambda x: x["pubDate"], reverse=True)
    first_batch  = new_items[:100]
    second_batch = new_items[100:]

    write_rss(first_batch, DAILY_FILE, title="Daily Feed (Updated 9 AM BD)")
    write_rss(second_batch if second_batch else [], DAILY_FILE_2,
              title="Daily Feed Extra (Updated 9 AM BD)")

    last_dt = max(i["pubDate"] for i in new_items)
    save_last_seen(last_dt, processed_links, master_items)

    sources = set()
    for item in new_items:
        m = re.search(r'\[\s*(.+?)\s*\]', item.get("title", ""))
        if m:
            sources.add(m.group(1).strip())
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        for src in sorted(sources):
            f.write(src + "\n")
    print(f"✓ sources.txt written with {len(sources)} unique sources")


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
