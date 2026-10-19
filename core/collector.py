from __future__ import annotations

import html
import http.client
import ipaddress
import io
import json
import os
import re
import socket
import sqlite3
from contextlib import closing
import base64
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from .config import load_keywords, load_sources
from .models import Candidate, utc_now
from .public_corpus import record_public_sample
from .verifier import VerificationEngine
from .developer_grants import is_developer_grant_lead, has_grant_application_denial
from .developer_benefits import is_explicit_developer_benefit


USER_AGENT = 'WoolRadar/7.1 (+local-read-only-monitor; contact=local-user)'


def classify_exception(exc: Exception) -> str:
    reason = getattr(exc, 'reason', None)
    if isinstance(exc, (TimeoutError, socket.timeout)) or isinstance(reason, (TimeoutError, socket.timeout)):
        return 'NETWORK_TIMEOUT'
    if isinstance(exc, ET.ParseError):
        return 'PARSE_OR_SOURCE_CHANGED'
    if isinstance(exc, urllib.error.URLError):
        return 'NETWORK_ERROR'
    return 'PARSE_OR_SOURCE_CHANGED'


def contains_keyword(text: str, keywords: list[str]) -> bool:
    # Brand/free fallback must not resurrect a closed grant from the same
    # source item. Multi-program items require separate manual adjudication.
    if has_grant_application_denial(text):
        return False
    value = text.casefold()
    brand_only = {'claude', 'gemini', 'grok', 'github', 'cursor pro'}
    strong = [keyword.casefold() for keyword in keywords if keyword.casefold() not in brand_only]

    def matches(keyword: str, sample: str = value) -> bool:
        if re.search(r'[\u4e00-\u9fff]', keyword):
            return keyword in sample
        pattern = re.escape(keyword).replace(r'\ ', r'\s+')
        if keyword.split()[-1] in {'api', 'credit', 'perk', 'coupon', 'giveaway', 'promotion'}:
            pattern += 's?'
        # Latin words may adjoin Chinese text, but not another Latin word.
        return re.search(r'(?<![a-z0-9_])' + pattern + r'(?![a-z0-9_])', sample) is not None

    # A request for a provider offering a trial is not a trial announcement.
    trial_offer = re.search(r'\bfree\s+trial\b|\b\d+[\s-]*(?:hours?|days?|weeks?|months?|years?)'
                            r'[\s-]+(?:[a-z0-9]+(?:-[a-z0-9]+)*\s+){0,3}trial\b|'
                            r'\bstart\s+(?:your\s+|a\s+)?trial\b|\btrial\s+(?:credits?|offer|available)\b', value)
    # A benefit keyword must belong to a clause asserting an available
    # offer. Requests, denials and already-closed promotions are not freebies.
    negative_offer = re.compile(
        r'\b(?:i|we)\s+(?:want|need|am\s+looking|are\s+looking|searching)\b|'
        r'\b(?:can|could|may|would)\s+(?:i|we)\b|'
        r'\bwhere\s+(?:can|do)\s+(?:i|we)\b|'
        r'\b(?:does?\s+anyone\s+know|is\s+there|are\s+there)\b|'
        r'\b(?:no\s+longer|not\s+available|discontinued|expired|has\s+ended|have\s+ended|is\s+over|are\s+over|entries\s+closed)\b|'
        r'\b(?:do|does|did)\s+not\s+(?:offer|provide|have)\b|'
        r'\b(?:don[\x27’]t|doesn[\x27’]t|didn[\x27’]t)\s+(?:offer|provide|have)\b|'
        r'\b(?:requires?|only\s+with|included\s+only\s+with)\b.{0,55}\bpaid\b')
    def available_clauses(sample: str) -> list[str]:
        clauses = []
        for sentence in re.split(r'[!?\n]|\.(?=\s|$)', sample):
            parts = sentence.split(';')
            if not negative_offer.search(sentence):
                clauses.extend(parts)
                continue
            # A trailing closure/paid restriction qualifies the same statement.
            # Only an explicit new campaign after a semicolon resets that scope.
            for part in parts[1:]:
                if (re.search(r'\b(?:new|another|replacement|different)\s+'
                              r'(?:program|campaign|promotion|offer|grant)\b', part)
                        and not negative_offer.search(part)):
                    clauses.append(part)
        return clauses

    offer_clauses = available_clauses(value)
    for clause in offer_clauses:
        if negative_offer.search(clause):
            continue
        if any(matches(keyword, clause) and (keyword != 'trial' or trial_offer)
               for keyword in strong):
            return True
    # A stated monetary credit award is a lead; it proves no personal eligibility.
    for clause in offer_clauses:
        # Fallback recognition must honor the same closed/request/paid guard
        # as direct keyword and branded matching. It cannot revive a denial.
        if negative_offer.search(clause):
            continue
        award = re.search(r'\b(?:receives?|awarded|grants?|offers?|claim|get)\s+(?:up\s+to\s+)?'
                          r'\$\s*\d[\d,]*(?:\.\d{1,2})?\s+(?:in\s+)?(?:cloud\s+|ai\s+)?credits\b', clause)
        free_start = re.search(r'\bstart\s+using\s+for\s+free\b', clause)
        coupon = (re.search(r'\b(?:special|use|apply|redeem|exclusive)\s+coupon\s+code\b', clause)
                  if 'promo code' in strong else None)
        diagnostic = (re.search(r'\bfree\s+(?:email|dns)\s+(?:testing|diagnostic)\s+tools?\b|'
                                r'\b(?:email|dns)\s+(?:testing|diagnostic)\s+tools?\s+(?:is|are)\s+free\b', clause)
                      if 'developer perks' in strong else None)
        offer = award or free_start or coupon or diagnostic
        if not offer:
            continue
        prefix, suffix = clause[:offer.start()], clause[offer.end():]
        # No card requirement / no expiry affirm the plan, not negate the CTA.
        denial_context = re.sub(r'\b(?:do\s+not|don[\x27’]t)\s+need\s+(?:a\s+)?credit\s+card\b|'
                                r'\bno\s+credit\s+card\b|\bnever\s+expires\b', '', prefix)
        if re.search(r'\b(?:can|could|may|would)\s+(?:i|we)\b|\b(?:no|not|never|don[\x27’]t|doesn[\x27’]t|cannot|can[\x27’]t)\b|'
                     r'\b(?:looking|searching)\s+for\b|\b(?:i|we)\s+(?:need|want)\b', denial_context):
            continue
        if award and (re.search(r'\bpaid\b', prefix) or re.search(r'\bfor\s+\$', suffix)):
            continue
        if diagnostic:
            if re.search(r'\b(?:is\s+there|does\s+anyone\s+know)\b', prefix):
                continue
            if (re.search(r'\bpaid\b|\b(?:buy|purchase)\b', prefix)
                    or re.search(r'\bfor\s+\$', prefix + suffix)
                    or re.search(r'\b(?:requires?|only\s+with)\b[^.!?;]{0,60}\bpaid\b', suffix)):
                continue
            if re.search(r'\b(?:no\s+longer|not\s+available|discontinued|retired)\b|\b(?:is|are)\s+not\b', suffix):
                continue
        return True
    # Developer grants are discovery leads only. They never imply a verified
    # award or account eligibility, and respect the existing keyword toggle.
    if 'developer perks' in strong and is_explicit_developer_benefit(text):
        return True
    if 'developer perks' in strong and is_developer_grant_lead(text):
        return True
    if not any(matches(brand) for brand in brand_only):
        return False
    # "free RAM" is an operating-system metric, not a price/benefit promise.
    promotion_text = re.sub(r'\bfree\s+(?:ram|memory|disk\s+space)\b'
                            r'(?!\s+(?:upgrade|upgrades|bonus|allocation)\b)', '', value)
    promo_cues = (
        'free', 'giveaway', 'credit', 'credits', 'perk', 'perks', 'trial', 'promo', 'promotion', 'coupon', 'redeem',
        '免费', '赠金', '兑换码', '限量', '抽奖', '羊毛', '送码', '优惠',
    )
    # Brand-only matching must not undo the same closed/request/paid gate.
    return any(
        any(matches(cue, clause) and (cue != 'trial' or trial_offer)
            for cue in promo_cues)
        for clause in available_clauses(promotion_text)
        if not negative_offer.search(clause))


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1].lower()


def _child_text(node: ET.Element, names: set[str]) -> str:
    for child in list(node):
        if _local_name(child.tag) in names:
            if _local_name(child.tag) == 'link' and child.attrib.get('href'):
                return child.attrib['href'].strip()
            return ''.join(child.itertext()).strip()
    return ''


def parse_feed(payload: bytes, source_id: str) -> list[dict]:
    root = ET.fromstring(payload)
    if _local_name(root.tag) not in {'rss', 'feed', 'rdf'}:
        raise ValueError('RSS_LAYOUT_CHANGED_OR_NOT_FEED')
    rows = []
    for node in root.iter():
        if _local_name(node.tag) not in {'item', 'entry'}:
            continue
        title = html.unescape(_child_text(node, {'title'}))
        url = _child_text(node, {'link'})
        summary = html.unescape(_child_text(node, {'description', 'summary', 'content'}))
        published = _child_text(node, {'pubdate', 'published', 'updated', 'date'})
        if title and url:
            rows.append({'title': title, 'url': url, 'summary': re.sub('<[^>]+>', ' ', summary),
                         'published_at': published, 'source_id': source_id,
                         'official_references': extract_references(summary, url)})
    return rows


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = ''
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self._href = dict(attrs).get('href', '')
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self._href:
            text = ' '.join(' '.join(self._text).split())
            if text:
                self.links.append((text, self._href))
            self._href = ''
            self._text = []


def parse_html_links(payload: bytes, base_url: str, source_id: str) -> list[dict]:
    parser = _LinkParser()
    parser.feed(payload.decode('utf-8', errors='replace'))
    return [{'title': title, 'url': urllib.parse.urljoin(base_url, href), 'summary': '',
             'published_at': '', 'source_id': source_id} for title, href in parser.links]


def extract_references(text: str, base_url: str) -> list[str]:
    parser = _LinkParser()
    parser.feed(text)
    links = [href for _, href in parser.links] + re.findall(r'https://[^\s<>"\']+', text)
    references = []
    for link in links:
        parsed = urllib.parse.urlsplit(urllib.parse.urljoin(base_url, link.rstrip('.,);')))
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            continue
        clean = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
        if clean not in references:
            references.append(clean)
    return references[:10]


def row_allowed(row: dict, source: dict) -> bool:
    """Apply declarative URL and topic boundaries to noisy public sources."""
    url = row.get('url', '')
    parsed = urllib.parse.urlparse(url)
    excluded_hosts = {host.casefold() for host in source.get('exclude_hosts', [])}
    if parsed.hostname and parsed.hostname.casefold() in excluded_hosts:
        return False
    allowed_hosts = {host.casefold() for host in source.get('allowed_hosts', [])}
    allowed_schemes = source.get('allowed_schemes', ['http', 'https'])
    if allowed_hosts and (not parsed.hostname or parsed.hostname.casefold() not in allowed_hosts
            or parsed.scheme not in allowed_schemes
            or parsed.username is not None or parsed.password is not None):
        return False
    required_text = source.get('required_text_regex')
    if required_text and not re.search(required_text,
            row.get('title', '') + ' ' + row.get('summary', ''), re.I):
        return False
    include = source.get('include_path_regex')
    if include and not re.search(include, parsed.path):
        return False
    exclude = source.get('exclude_path_regex')
    return not (exclude and re.search(exclude, parsed.path))


def build_candidate(row: dict, source: dict, node: str) -> Candidate:
    metadata = {'source_id': source['id'], 'official': bool(source.get('official'))}
    metadata['official_references'] = row.get('official_references') or extract_references(row.get('summary', ''), row['url'])
    batch = ''
    title = row['title']
    # Only an explicit numeric marker in an official source title qualifies.
    # Only a year immediately attached to that marker identifies an annual
    # batch. Publication dates and unrelated title numbers cannot supply it.
    marker = re.search(r'\b(?:batch|round)\s*#?\s*(\d+)\b|第\s*(\d+)\s*批', title, re.I)
    if source.get('official') and marker:
        number = marker.group(1) or marker.group(2)
        batch = 'explicit:' + source['id'] + ':' + number
        prefix = title[:marker.start()]
        year = re.search(r'(?<![a-zA-Z0-9])(20\d{2})\s*(?:年\s*)?$', prefix)
        if year and re.search(r'(?:[$￥¥€£₹]|\b(?:USD|EUR|CNY|RMB|GBP)|价值|金额)\s*$', prefix[:year.start()], re.I):
            year = None
        metadata['campaign_title'] = prefix + title[marker.end():]
        metadata['batch_evidence'] = {'marker': marker.group(), 'url': row['url'],
            'method': 'explicit_official_title', 'current_open': 'unknown'}
        if year:
            batch = 'explicit:' + source['id'] + ':' + year.group(1) + ':' + number
            metadata['campaign_title'] = prefix[:year.start()] + title[marker.end():]
            metadata['batch_evidence']['year'] = year.group(1)
            metadata['batch_evidence']['marker'] = title[year.start():marker.end()]
    return Candidate(node=node, source=source['platform'], title=title, url=row['url'],
        published_at=row.get('published_at', ''), summary=row.get('summary', ''), batch_id=batch,
        source_kind='official' if source.get('official') else 'community', metadata=metadata)


@dataclass(slots=True)
class SourceRun:
    source_id: str
    status: str
    items: int = 0
    error_code: str = ''
    detail: str = ''


@dataclass(slots=True)
class CollectionResult:
    node: str
    candidates: list[Candidate] = field(default_factory=list)
    sources: list[SourceRun] = field(default_factory=list)


class RequestBudget:
    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.state_dir / 'request-budget.db'
        with closing(sqlite3.connect(self.db_path, timeout=30)) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS budget (key TEXT PRIMARY KEY, until_epoch REAL, pause_reason TEXT)')
            conn.execute('CREATE TABLE IF NOT EXISTS http_requests (host TEXT, requested_at REAL)')
            conn.execute('CREATE INDEX IF NOT EXISTS http_requests_host_time ON http_requests(host,requested_at)')
            conn.execute('CREATE TABLE IF NOT EXISTS hn_checkpoint (source TEXT, item_id TEXT, fetched_at REAL, payload TEXT, PRIMARY KEY(source,item_id))')
            conn.execute('CREATE TABLE IF NOT EXISTS hn_scan (source TEXT PRIMARY KEY, started_at REAL, item_ids TEXT)')
            conn.commit()

    def hn_scan_ids(self, source: str, ids: list | None = None, complete: bool = False):
        with closing(sqlite3.connect(self.db_path, timeout=30)) as conn:
            conn.execute('DELETE FROM hn_scan WHERE started_at<=?', (time.time() - 86400,))
            if complete:
                conn.execute('DELETE FROM hn_scan WHERE source=?', (source,))
            elif ids is not None:
                conn.execute('INSERT OR REPLACE INTO hn_scan VALUES(?,?,?)', (source, time.time(), json.dumps(ids)))
            row = conn.execute('SELECT item_ids FROM hn_scan WHERE source=?', (source,)).fetchone()
            conn.commit()
            return json.loads(row[0]) if row else None

    def hn_item(self, source: str, item_id: str, item: dict | None = None):
        with closing(sqlite3.connect(self.db_path, timeout=30)) as conn:
            conn.execute('DELETE FROM hn_checkpoint WHERE fetched_at<=?', (time.time() - 86400,))
            if item is not None:
                conn.execute('INSERT OR REPLACE INTO hn_checkpoint VALUES(?,?,?,?)',
                             (source, str(item_id), time.time(), json.dumps(item)))
            row = conn.execute('SELECT payload FROM hn_checkpoint WHERE source=? AND item_id=?', (source, str(item_id))).fetchone()
            conn.commit()
            return json.loads(row[0]) if row else None

    def acquire_http(self, url: str, max_per_hour: int = 60) -> bool:
        host = urllib.parse.urlparse(url).hostname
        if not host:
            raise ValueError('HTTP_HOST_REQUIRED')
        now = time.time()
        with closing(sqlite3.connect(self.db_path, timeout=30)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('SELECT until_epoch,pause_reason FROM budget WHERE key=?', ('host:' + host,)).fetchone()
            if row and row[1] and (row[0] == 0 or now < row[0]):
                raise SourcePaused(row[1])
            conn.execute('DELETE FROM http_requests WHERE requested_at<=?', (now - 3600,))
            count, latest = conn.execute('SELECT COUNT(*),MAX(requested_at) FROM http_requests WHERE host=?', (host,)).fetchone()
            if count >= max_per_hour or (latest is not None and now - latest < 2):
                conn.commit()
                return False
            conn.execute('INSERT INTO http_requests VALUES(?,?)', (host, now))
            conn.commit()
            return True

    def pause(self, source: dict, reason: str, seconds: int | None = None):
        until = time.time() + seconds if seconds is not None else 0
        with closing(sqlite3.connect(self.db_path, timeout=30)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute('INSERT OR REPLACE INTO budget VALUES(?,?,?)', (source['id'], until, reason))
            host = urllib.parse.urlparse(source.get('endpoint', '')).hostname
            if host:
                prior = conn.execute('SELECT until_epoch,pause_reason FROM budget WHERE key=?', ('host:' + host,)).fetchone()
                stronger = prior and prior[1] and (prior[0] == 0 or (until != 0 and prior[0] >= until))
                if not stronger:
                    conn.execute('INSERT OR REPLACE INTO budget VALUES(?,?,?)', ('host:' + host, until, reason))
            conn.commit()

    def sync_host_pauses(self, sources: list[dict]):
        # Upgrade existing source-only pauses without clearing any barrier.
        with closing(sqlite3.connect(self.db_path, timeout=30)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            for source in sources:
                row = conn.execute('SELECT until_epoch,pause_reason FROM budget WHERE key=?', (source['id'],)).fetchone()
                host = urllib.parse.urlparse(source.get('endpoint', '')).hostname
                if not host or not row or not row[1] or (row[0] != 0 and row[0] <= time.time()):
                    continue
                prior = conn.execute('SELECT until_epoch,pause_reason FROM budget WHERE key=?', ('host:' + host,)).fetchone()
                if prior and prior[1] and (prior[0] == 0 or (row[0] != 0 and prior[0] >= row[0])):
                    continue
                conn.execute('INSERT OR REPLACE INTO budget VALUES(?,?,?)', ('host:' + host, row[0], row[1]))
            conn.commit()

    def acquire(self, source: dict, force: bool = False) -> bool:
        now = time.time()
        host = 'host:' + (urllib.parse.urlparse(source.get('endpoint', '')).hostname or source['id'])
        with closing(sqlite3.connect(self.db_path, timeout=30)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('SELECT until_epoch,pause_reason FROM budget WHERE key=?', (source['id'],)).fetchone()
            if row and row[1] and (row[0] == 0 or now < row[0]):
                raise SourcePaused(row[1])
            if row and now < row[0] and not force:
                return False
            host_row = conn.execute('SELECT until_epoch,pause_reason FROM budget WHERE key=?', (host,)).fetchone()
            if host_row and host_row[1] and (host_row[0] == 0 or now < host_row[0]):
                raise SourcePaused(host_row[1])
            if host_row and now < host_row[0]:
                return False  # Even a forced scan never bypasses the shared host budget.
            conn.execute('INSERT OR REPLACE INTO budget VALUES(?,?,?)',
                (source['id'], now + int(source.get('interval_minutes', 60)) * 60, ''))
            conn.execute('INSERT OR REPLACE INTO budget VALUES(?,?,?)', (host, now + 60, ''))
            conn.commit()
            return True


def _request(url: str, accept: str, budget: RequestBudget | None = None) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': accept})
    payload = budgeted_read(request, budget)
    if VerificationEngine.classify_fetch_failure(200, payload[:65536].decode('utf-8', errors='replace')) == 'CAPTCHA_REQUIRED':
        raise SourcePaused('CAPTCHA_REQUIRED')
    return payload


def _safe_public_fetch_url(url: str) -> bool:
    """Conservatively reject direct-to-private and ambiguous network targets.

    This is a URL syntax barrier, not a DNS rebinding defense: the actual
    resolved peer still requires enforcement at the network boundary.
    """
    try:
        parsed = urllib.parse.urlsplit(url)
        host = parsed.hostname
        if (parsed.scheme != 'https' or not host or parsed.username is not None
                or parsed.password is not None or '\\' in url or any(ord(ch) < 32 for ch in url)):
            return False
        if parsed.port is not None and not (1 <= parsed.port <= 65535):
            return False
        host = host.casefold().rstrip('.')
        if (not host or host == 'localhost' or host.endswith(('.localhost', '.local', '.internal'))
                or re.fullmatch(r'(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*', host)):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return True
    except (TypeError, ValueError):
        return False


def _connect_public_peer(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Resolve once, reject every nonpublic answer and connect to that exact IP.

    ``socket.create_connection`` resolves again, so a separate DNS precheck
    would leave a rebinding window between validation and the actual connect.
    """
    host, port = address
    endpoints = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not endpoints or any(not ipaddress.ip_address(item[4][0]).is_global for item in endpoints):
        raise SourcePaused('NON_PUBLIC_RESOLVED_PEER')
    last_error = None
    for family, socktype, proto, _, peer in endpoints:
        sock = None
        try:
            sock = socket.socket(family, socktype, proto)
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(peer)
            return sock
        except OSError as exc:
            last_error = exc
            if sock is not None:
                sock.close()
    if last_error is not None:
        raise last_error
    raise SourcePaused('NON_PUBLIC_RESOLVED_PEER')


class _PublicPeerHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        # A configured proxy owns the CONNECT tunnel and its destination DNS.
        # This guard protects direct origin connections; proxy enforcement
        # needs its own independent network-boundary acceptance.
        if not self._tunnel_host:
            self._create_connection = _connect_public_peer
        super().connect()


class _PublicPeerHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(_PublicPeerHTTPSConnection, request, context=self._context)


def budgeted_read(request, budget: RequestBudget | None = None, max_bytes: int = 2_000_000, validate=None) -> bytes:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    # Never use urllib's automatic redirects: those bypass the per-hop checks
    # below even when the caller didn't provide a request budget.
    opener = None
    for hop in range(6):
        url = request.full_url
        if not _safe_public_fetch_url(url) or (validate is not None and not validate(url)):
            raise SourcePaused('UNAPPROVED_REFERENCE_URL')
        if budget is not None and not budget.acquire_http(url):
            raise SourcePaused('REQUEST_BUDGET')
        if opener is None:
            # Explicitly disable environment proxies: a CONNECT proxy resolves
            # the origin itself and would bypass the pinned-public-peer check.
            opener = urllib.request.build_opener(NoRedirect(), urllib.request.ProxyHandler({}),
                                                 _PublicPeerHTTPSHandler())
        try:
            with opener.open(request, timeout=20) as response:
                payload = response.read(max_bytes)
            if budget is not None and VerificationEngine.classify_fetch_failure(200, payload[:65536].decode('utf-8', errors='replace')) == 'CAPTCHA_REQUIRED':
                budget.pause({'id': 'http-host:' + urllib.parse.urlsplit(url).hostname, 'endpoint': url}, 'CAPTCHA_REQUIRED')
                raise SourcePaused('CAPTCHA_REQUIRED')
            return payload
        except urllib.error.HTTPError as exc:
            if budget is not None and exc.code not in (301, 302, 303, 307, 308):
                body = exc.read(65536)
                if exc.fp is not None:
                    exc.fp.close()
                exc.fp = io.BytesIO(body)
                code = VerificationEngine.classify_fetch_failure(exc.code, body.decode('utf-8', errors='replace'))
                try:
                    retry = max(1800, int(exc.headers.get('Retry-After', '1800')))
                except ValueError:
                    retry = 3600
                if exc.code in (403, 429) or code == 'CAPTCHA_REQUIRED':
                    budget.pause({'id': 'http-host:' + urllib.parse.urlsplit(url).hostname, 'endpoint': url}, code, retry if code == 'RATE_LIMITED_429' else None)
            if exc.code not in (301, 302, 303, 307, 308):
                raise
            destination = urllib.parse.urljoin(url, exc.headers.get('Location', ''))
            exc.close()
            parsed = urllib.parse.urlsplit(destination)
            if request.data is not None or request.has_header('Authorization'):
                raise SourcePaused('AUTHENTICATED_REDIRECT_REJECTED')
            if (not _safe_public_fetch_url(destination)
                    or re.search(r'/(login|signin|signup|oauth|authorize|checkout|redeem)(/|$)', urllib.parse.unquote(parsed.path), re.I)):
                raise SourcePaused('UNAPPROVED_REFERENCE_REDIRECT')
            time.sleep(2)
            request = urllib.request.Request(destination, headers={'User-Agent': USER_AGENT, 'Accept': request.get_header('Accept', 'text/html')})
    raise ValueError('REDIRECT_LIMIT')


def _fetch_hn(source: dict, limit: int = 20, budget: RequestBudget | None = None) -> list[dict]:
    ids = budget.hn_scan_ids(source['id']) if budget is not None else None
    if ids is None:
        ids = json.loads(_request(source['endpoint'], 'application/json', budget))[:limit]
        if budget is not None:
            budget.hn_scan_ids(source['id'], ids)
    rows = []
    for item_id in ids:
        url = f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json'
        item = budget.hn_item(source['id'], str(item_id)) if budget is not None else None
        if item is None:
            if budget is not None:
                time.sleep(2)
            item = json.loads(_request(url, 'application/json', budget))
            if budget is not None and isinstance(item, dict):
                budget.hn_item(source['id'], str(item_id), item)
        if item and item.get('title'):
            rows.append({'title': item['title'], 'url': item.get('url') or f'https://news.ycombinator.com/item?id={item_id}',
                         'summary': item.get('text', ''), 'published_at': str(item.get('time', '')),
                         'source_id': source['id']})
    if budget is not None:
        budget.hn_scan_ids(source['id'], complete=True)
    return rows


def _fetch_source(source: dict, budget: RequestBudget | None = None) -> list[dict]:
    if source['kind'] == 'rss':
        return parse_feed(_request(source['endpoint'], 'application/rss+xml, application/atom+xml, application/xml, text/xml', budget), source['id'])
    if source['kind'] == 'html':
        rows = parse_html_links(_request(source['endpoint'], 'text/html', budget), source['endpoint'], source['id'])
        if not rows:
            raise ValueError('HTML_LAYOUT_CHANGED_OR_EMPTY')
        return rows
    if source['kind'] == 'hn_api':
        return _fetch_hn(source, budget=budget)
    raise ValueError(f"unsupported source kind: {source['kind']}")


class SourcePaused(Exception):
    def __init__(self, reason: str, retry_seconds: int | None = None):
        super().__init__(reason)
        self.retry_seconds = retry_seconds


def fetch_reddit_oauth(root: Path, source: dict, budget: RequestBudget | None = None) -> list[dict]:
    credentials_path = root / 'nodes' / 'clawradar' / 'credentials.json'
    if not credentials_path.exists():
        raise SourcePaused('OAUTH_CONFIGURATION_REQUIRED')
    credentials = json.loads(credentials_path.read_text(encoding='utf-8'))
    mode = credentials.get('auth_mode', 'refresh_token')
    if mode not in ('refresh_token', 'application_only'):
        raise SourcePaused('OAUTH_AUTH_MODE_UNSUPPORTED')
    required = ('client_id', 'client_secret') if mode == 'application_only' else ('client_id', 'refresh_token')
    if any(not isinstance(credentials.get(key), str) or not credentials[key].strip()
           or credentials[key].startswith('FILL_') for key in required):
        raise SourcePaused('OAUTH_CONFIGURATION_REQUIRED')
    if not isinstance(credentials.get('client_secret', ''), str):
        raise SourcePaused('OAUTH_CONFIGURATION_REQUIRED')
    auth = base64.b64encode((credentials['client_id'] + ':' + credentials.get('client_secret', '')).encode()).decode()
    agent = credentials.get('user_agent', USER_AGENT)
    grant = {'grant_type': 'client_credentials'} if mode == 'application_only' else {
        'grant_type': 'refresh_token', 'refresh_token': credentials['refresh_token']}
    # Direct callers receive the same guarded transport as scheduled collectors.
    # In particular, Basic/Bearer credentials must never follow an HTTP redirect.
    if budget is None:
        budget = RequestBudget(root / 'data' / 'source-state')
    request = urllib.request.Request('https://www.reddit.com/api/v1/access_token',
        data=urllib.parse.urlencode(grant).encode(),
        headers={'Authorization': 'Basic ' + auth, 'User-Agent': agent})
    try:
        token = json.loads(budgeted_read(request, budget))
    except urllib.error.HTTPError as exc:
        if exc.code == 429 or exc.code >= 500:
            raise
        exc.close()
        prefix = 'OAUTH_APPLICATION_AUTH_FAILED_' if mode == 'application_only' else 'OAUTH_REFRESH_FAILED_'
        raise SourcePaused(prefix + str(exc.code)) from None
    scopes = token.get('scope', '').split()
    # App-only wildcard has no user account context. User tokens must explicitly
    # grant read; neither flow exposes any write or private-data endpoint here.
    permitted = 'read' in scopes or (mode == 'application_only' and scopes == ['*'])
    if not token.get('access_token') or not permitted:
        raise SourcePaused('OAUTH_READ_SCOPE_REQUIRED')
    url = 'https://oauth.reddit.com/r/freebies+vps+webhosting/hot?limit=50&raw_json=1'
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token['access_token'],
        'User-Agent': agent, 'Accept': 'application/json'})
    payload = json.loads(budgeted_read(request, budget))
    rows = []
    for entry in payload.get('data', {}).get('children', []):
        post = entry.get('data', {})
        rows.append({'title': post.get('title', ''), 'summary': post.get('selftext', ''),
            'url': 'https://www.reddit.com' + post.get('permalink', ''),
            'published_at': datetime.fromtimestamp(post.get('created_utc', 0), timezone.utc).isoformat(),
            'source_id': source['id']})
    return rows


def fetch_x_browser(root: Path) -> list[dict]:
    python = root / 'nodes' / 'twitter-monitor' / 'upstream' / '.venv' / 'Scripts' / 'python.exe'
    script = root / 'nodes' / 'twitter-monitor' / 'browser_collect.py'
    result = subprocess.run([str(python), str(script), '--root', str(root)],
        capture_output=True, text=True, encoding='utf-8', timeout=150,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise SourcePaused('BROWSER_COLLECTOR_UNAVAILABLE') from None
    if result.returncode != 0 or isinstance(payload, dict):
        message = payload.get('error', '') if isinstance(payload, dict) else ''
        reason = 'CAPTCHA_REQUIRED' if 'CAPTCHA_REQUIRED' in message else 'MANUAL_LOGIN_OR_BROWSER_REQUIRED'
        raise SourcePaused(reason)
    return payload


def fetch_digest_rss(root: Path, source: dict) -> list[dict]:
    python = root / 'nodes' / 'digest-ai-agent' / 'upstream' / '.venv' / 'Scripts' / 'python.exe'
    script = root / 'nodes' / 'digest-ai-agent' / 'rss_collect.py'
    result = subprocess.run([str(python), '-X', 'utf8', str(script), source['endpoint'], str(root)],
        capture_output=True, text=True, encoding='utf-8', timeout=40,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    payload = json.loads(result.stdout)
    if result.returncode != 0:
        error = payload.get('error', {})
        code = error.get('error_code', 'UPSTREAM_RSS_FAILED')
        if code in ('BLOCKED_403', 'RATE_LIMITED_429', 'CAPTCHA_REQUIRED', 'REQUEST_BUDGET'):
            raise SourcePaused(code, error.get('retry_seconds'))
        raise ValueError('UPSTREAM_RSS_FAILED')
    return payload['rows']


def collect_for_node(root: Path, node: str, force: bool = False) -> CollectionResult:
    root = Path(root)
    sources = [item for item in load_sources(root / 'config' / 'sources.yaml') if item['owner_node'] == node]
    keywords = load_keywords(root / 'config' / 'keywords.json')
    budget = RequestBudget(root / 'data' / 'source-state')
    budget.sync_host_pauses(load_sources(root / 'config' / 'sources.yaml'))
    result = CollectionResult(node)

    for source in sources:
        if not source.get('enabled', True):
            result.sources.append(SourceRun(source['id'], 'SKIPPED', error_code='SOURCE_DISABLED',
                                            detail='Disabled by configuration; no request attempted'))
            continue
        try:
            if not budget.acquire(source, force=force):
                result.sources.append(SourceRun(source['id'], 'SKIPPED', error_code='REQUEST_BUDGET'))
                continue
            if source['kind'] == 'browser':
                rows = fetch_x_browser(root)
            elif source['kind'] == 'reddit_oauth':
                rows = fetch_reddit_oauth(root, source, budget)
            elif node == 'digest-ai-agent' and source['kind'] == 'rss':
                rows = fetch_digest_rss(root, source)
            else:
                rows = _fetch_source(source, budget)
            matched = 0
            accepted = []
            for row in rows:
                accepted.append(False)
                if not row_allowed(row, source):
                    continue
                searchable = f"{row['title']} {row.get('summary', '')}"
                if not contains_keyword(searchable, keywords):
                    continue
                matched += 1
                accepted[-1] = True
                result.candidates.append(build_candidate(row, source, node))
            detail = f'fetched={len(rows)}'
            try:
                sample = record_public_sample(root, node, source, rows, accepted)
                if sample is not None:
                    detail += f';sampled={min(len(rows),500)}'
            except (OSError, ValueError, TypeError) as exc:
                detail += ';corpus_error=' + type(exc).__name__
            result.sources.append(SourceRun(source['id'], 'OK', items=matched, detail=detail))
        except SourcePaused as exc:
            if str(exc) == 'REQUEST_BUDGET':
                result.sources.append(SourceRun(source['id'], 'SKIPPED', error_code=str(exc)))
                continue
            if str(exc) != 'RATE_LIMITED_429' or exc.retry_seconds is not None:
                budget.pause(source, str(exc), exc.retry_seconds if str(exc) == 'RATE_LIMITED_429' else None)
            result.sources.append(SourceRun(source['id'], 'PAUSED', error_code=str(exc)))
        except urllib.error.HTTPError as exc:
            body = exc.read(4096).decode('utf-8', errors='replace')
            code = VerificationEngine.classify_fetch_failure(exc.code, body)
            if exc.code == 429:
                try:
                    retry = max(1800, int(exc.headers.get('Retry-After', '1800')))
                except ValueError:
                    retry = 3600
                budget.pause(source, code, retry)
            elif exc.code == 403 or code == 'CAPTCHA_REQUIRED':
                budget.pause(source, code)
            state = 'PAUSED' if exc.code in (403, 429) or code == 'CAPTCHA_REQUIRED' else 'FAILED'
            result.sources.append(SourceRun(source['id'], state, error_code=code, detail=f'HTTP {exc.code}'))
        except Exception as exc:
            result.sources.append(SourceRun(source['id'], 'FAILED', error_code=classify_exception(exc), detail=str(exc)))
    return result


def write_collection(root: Path, result: CollectionResult) -> tuple[Path, Path]:
    root = Path(root)
    inbox = root / 'data' / 'inbox'
    status_dir = root / 'data' / 'status'
    inbox.mkdir(parents=True, exist_ok=True)
    status_dir.mkdir(parents=True, exist_ok=True)
    items_path = inbox / f'{result.node}.jsonl'
    status_path = status_dir / f'{result.node}.json'
    items_path.write_text(''.join(json.dumps(item.to_dict(), ensure_ascii=False) + '\n' for item in result.candidates), encoding='utf-8')
    status_path.write_text(json.dumps({
        'node': result.node, 'finished_at': utc_now(), 'candidate_count': len(result.candidates),
        'sources': [source.__dict__ if hasattr(source, '__dict__') else {
            'source_id': source.source_id, 'status': source.status, 'items': source.items,
            'error_code': source.error_code, 'detail': source.detail,
        } for source in result.sources],
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    return items_path, status_path
