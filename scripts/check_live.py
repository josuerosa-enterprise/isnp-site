#!/usr/bin/env python3
"""Verify deployed pages and shared assets against this exact checkout (network required)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://www.institutodesaudedonortedopara.com'
paths = [node.text.removeprefix(ORIGIN) for node in ET.parse(ROOT/'sitemap.xml').findall('.//{*}loc')]
paths += ['/styles.css','/news.css','/app.js','/assets/fonts/inter-latin.woff2','/robots.txt','/sitemap.xml']

def verify(path):
    expected = ROOT / (path.lstrip('/') or 'index.html')
    with urlopen(Request(ORIGIN+path, headers={'Cache-Control':'no-cache','User-Agent':'ISNP-site-check/1.0'}), timeout=60) as response:
        actual = response.read()
        assert response.status == 200, path+': HTTP status'
        assert 'noindex' not in response.headers.get('X-Robots-Tag','').lower(), path+': noindex header'
        assert response.url == ORIGIN+path, path+': unexpected redirect'
        assert actual == expected.read_bytes(), path+': published bytes differ from checkout'
        return f'PASS {path} — HTTP 200; {len(actual):,} bytes match the checkout'

with ThreadPoolExecutor(max_workers=4) as pool:
    for message in pool.map(verify, paths): print(message, flush=True)
try:
    urlopen(ORIGIN+'/isnp-validation-missing-page-20261013.html', timeout=60)
except HTTPError as error:
    assert error.code == 404, f'Expected 404, received {error.code}'
    print('PASS missing page returns HTTP 404')
else:
    raise SystemExit('Expected HTTP 404 for a nonexistent page')
