#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全国の地域政治ニュースを複数のRSSフィードから収集し、
静的なHTMLページ (index.html) を生成するスクリプト。

GitHub Actions から定期実行されることを想定しています。
"""

import feedparser
import html
import json
import os
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

JST = timezone(timedelta(hours=9))

# 収集対象のRSSフィード (name, url)
FEEDS = [
    ("NHKニュース 政治", "https://www3.nhk.or.jp/rss/news/cat4.xml"),
    ("Yahoo!ニュース 国内", "https://news.yahoo.co.jp/rss/topics/domestic.xml"),
    ("Google ニュース検索:地方議会", "https://news.google.com/rss/search?q=%E5%9C%B0%E6%96%B9%E8%AD%B0%E4%BC%9A%20when:1d&hl=ja&gl=JP&ceid=JP:ja"),
    ("Google ニュース検索:知事", "https://news.google.com/rss/search?q=%E7%9F%A5%E4%BA%8B%20when:1d&hl=ja&gl=JP&ceid=JP:ja"),
    ("Google ニュース検索:市長選", "https://news.google.com/rss/search?q=%E5%B8%82%E9%95%B7%E9%81%B8%20OR%20%E7%9F%A5%E4%BA%8B%E9%81%B8%20OR%20%E7%9F%A5%E4%BA%8B%E9%81%B8%E6%8C%99%20when:2d&hl=ja&gl=JP&ceid=JP:ja"),
]

MAX_ITEMS_PER_FEED = 20
MAX_TOTAL_ITEMS = 80
OUTPUT_FILE = "index.html"
DATA_FILE = "news_data.json"


def parse_date(entry):
    """RSSエントリから日時(JST)を取得。失敗したら None。"""
    for key in ("published", "updated", "pubDate"):
        val = entry.get(key)
        if val:
            try:
                dt = parsedate_to_datetime(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(JST)
            except Exception:
                pass
    if entry.get("published_parsed"):
        try:
            import calendar
            ts = calendar.timegm(entry["published_parsed"])
            return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(JST)
        except Exception:
            pass
    return None


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return text.strip()


def fetch_all():
    items = []
    seen_links = set()
    for source_name, url in FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[WARN] {source_name} の取得に失敗: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= MAX_ITEMS_PER_FEED:
                break
            link = entry.get("link", "").strip()
            title = clean_text(entry.get("title", ""))
            if not link or not title:
                continue
            if link in seen_links:
                continue
            seen_links.add(link)

            summary = clean_text(entry.get("summary", "") or entry.get("description", ""))
            if len(summary) > 200:
                summary = summary[:200] + "…"

            dt = parse_date(entry)

            items.append({
                "source": source_name,
                "title": title,
                "link": link,
                "summary": summary,
                "date": dt.isoformat() if dt else None,
                "date_display": dt.strftime("%Y/%m/%d %H:%M") if dt else "日時不明",
                "sort_key": dt.timestamp() if dt else 0,
            })
            count += 1

    items.sort(key=lambda x: x["sort_key"], reverse=True)
    return items[:MAX_TOTAL_ITEMS]


def render_html(items, generated_at):
    cards = []
    for it in items:
        cards.append(f"""
        <article class="card">
          <div class="card-meta">
            <span class="source">{html.escape(it['source'])}</span>
            <span class="date">{html.escape(it['date_display'])}</span>
          </div>
          <h2 class="title"><a href="{html.escape(it['link'])}" target="_blank" rel="noopener noreferrer">{html.escape(it['title'])}</a></h2>
          <p class="summary">{html.escape(it['summary'])}</p>
        </article>""")

    cards_html = "\n".join(cards) if cards else "<p class='empty'>現在取得できるニュースがありません。しばらくしてから再度更新されます。</p>"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全国 地域政治ニュースまとめ</title>
<meta name="description" content="全国の地域政治ニュースを自動収集してまとめるサイトです。">
<style>
  :root {{
    --bg: #f4f5f7;
    --card-bg: #ffffff;
    --accent: #1a3a6b;
    --accent-light: #2f5fa8;
    --text: #1c1f24;
    --muted: #6b7280;
    --border: #e5e7eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Hiragino Sans", "Yu Gothic", "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
  }}
  header {{
    background: linear-gradient(135deg, var(--accent), var(--accent-light));
    color: #fff;
    padding: 2.5rem 1.5rem 2rem;
    text-align: center;
  }}
  header h1 {{
    margin: 0 0 0.5rem;
    font-size: 1.8rem;
    letter-spacing: 0.02em;
  }}
  header p {{
    margin: 0;
    opacity: 0.9;
    font-size: 0.9rem;
  }}
  main {{
    max-width: 860px;
    margin: 0 auto;
    padding: 1.5rem 1rem 4rem;
  }}
  .updated {{
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    margin: 1rem 0 2rem;
  }}
  .grid {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
  }}
  .card:hover {{
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    transform: translateY(-2px);
  }}
  .card-meta {{
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: var(--muted);
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
    gap: 0.4rem;
  }}
  .source {{
    background: #eef2fb;
    color: var(--accent);
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-weight: 600;
  }}
  .title {{
    font-size: 1.05rem;
    margin: 0 0 0.5rem;
  }}
  .title a {{
    color: var(--text);
    text-decoration: none;
  }}
  .title a:hover {{
    color: var(--accent-light);
    text-decoration: underline;
  }}
  .summary {{
    margin: 0;
    font-size: 0.9rem;
    color: #444;
  }}
  .empty {{
    text-align: center;
    color: var(--muted);
  }}
  footer {{
    text-align: center;
    padding: 2rem 1rem 3rem;
    color: var(--muted);
    font-size: 0.78rem;
  }}
  footer a {{ color: var(--accent-light); }}
</style>
</head>
<body>
<header>
  <h1>🗳️ 全国 地域政治ニュースまとめ</h1>
  <p>複数のニュースソースから地域・地方政治のニュースを自動収集しています</p>
</header>
<main>
  <p class="updated">最終更新: {html.escape(generated_at)}（日本時間）｜自動更新（GitHub Actions）</p>
  <div class="grid">
    {cards_html}
  </div>
</main>
<footer>
  このサイトはRSSフィードから自動収集した見出し・要約のみを表示しています。詳細は各リンク先の元記事をご確認ください。<br>
  Powered by GitHub Actions + GitHub Pages
</footer>
</body>
</html>
"""


def main():
    items = fetch_all()
    now_jst = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M")

    html_out = render_html(items, now_jst)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_out)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"generated_at": now_jst, "items": items}, f, ensure_ascii=False, indent=2)

    print(f"生成完了: {len(items)}件のニュースを {OUTPUT_FILE} に出力しました。")


if __name__ == "__main__":
    main()
