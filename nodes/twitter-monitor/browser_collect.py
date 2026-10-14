"""Read visible X posts through the dedicated local Chrome. Never read cookies."""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.browser_guard import assert_dedicated_listener


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((args.root / 'config' / 'x-browser.json').read_text(encoding='utf-8'))
    assert_dedicated_listener(str(args.root / 'nodes' / 'twitter-monitor' / 'chrome-profile'))
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp('http://127.0.0.1:9222', timeout=10000)
        context = browser.contexts[0]
        pages = [p for p in context.pages if p.url.startswith('https://x.com/')]
        page = pages[0] if pages else context.new_page()
        rows = []
        for url in config.get('scan_urls', ['https://x.com/home'])[:3]:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            try:
                page.locator('article').first.wait_for(state='visible', timeout=15000)
            except Exception:
                body = page.locator('body').inner_text(timeout=5000).lower()
                if any(term in body for term in ('captcha', 'verify you are human', 'unusual activity')):
                    raise RuntimeError('CAPTCHA_REQUIRED')
                raise RuntimeError('MANUAL_LOGIN_OR_NO_POSTS')
            for article in page.locator('article').all()[:20]:
                text = article.inner_text(timeout=5000)
                links = article.locator('a[href*="/status/"]').all()
                href = next((a.get_attribute('href') for a in links if a.get_attribute('href')), None)
                if not href:
                    continue
                when = article.locator('time')
                published = when.first.get_attribute('datetime') if when.count() else ''
                rows.append({'title': text[:200], 'summary': text[:4000],
                    'url': 'https://x.com' + href if href.startswith('/') else href,
                    'published_at': published or '', 'source_id': 'x-browser'})
        print(json.dumps(rows, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'error': str(exc)[:200]}, ensure_ascii=False))
        raise SystemExit(2)
