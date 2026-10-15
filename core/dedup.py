from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import Candidate


STOP_TOKENS = {
    'a', 'an', 'and', 'the', 'for', 'to', 'of', 'free', 'giveaway', 'promo', 'promotion',
    '福利', '活动', '免费', '抽奖', '赠送', '限量', '的', '与', '和', 'x',
    'by', 'are', 'giving', 'away', 'lets', 'let', 'talk',
}

# Generic benefit words do not identify a provider or a campaign. A bounded
# fallback avoids joining unrelated offers solely on an uninformative title.
GENERIC_OFFER_TOKENS = {
    'api', 'credit', 'credits', 'cloud', 'vps', 'server', 'servers', 'hosting',
    'developer', 'developers', 'perk', 'perks', 'offer', 'offers', 'trial', 'plan', 'ai',
    '额度', '赠金', '服务器', '优惠',
}


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    # Only explicit tracking fields are disposable. Prefix deletion silently
    # collapsed distinct source_campaign/reference_id variants into one offer.
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not (k.lower().startswith('utm_') or k.lower() in {'ref', 'source'})]
    # Sorting different keys avoids duplicate events for equivalent URLs,
    # while stable sorting preserves the order of repeated values per key.
    query.sort(key=lambda item: item[0])
    path = re.sub(r'/+$', '', parts.path) or '/'
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ''))


def normalize_title(title: str) -> str:
    text = unicodedata.normalize('NFKC', title).lower().replace('×', ' x ')
    text = re.sub(r'\b(\d+)x\b', r'\1', text)
    text = text.replace('免费', ' free ').replace('抽奖', ' giveaway ').replace('赠送', ' giveaway ')
    tokens = re.findall(r'[a-z0-9]+|[\u4e00-\u9fff]+', text)
    kept = sorted(set(token for token in tokens if token not in STOP_TOKENS and (len(token) > 1 or token.isdigit())))
    return ' '.join(kept)


# A resource size is not a vendor or a campaign identifier. Only treat sizes
# as generic when every other word is a generic benefit term. A year-like
# number can identify a particular promotion batch and must not be erased.
GENERIC_RESOURCE_UNITS = {'gb', 'mb', 'tb'}


def _generic_resource_title(tokens: set[str]) -> bool:
    if not tokens & GENERIC_RESOURCE_UNITS or not tokens & GENERIC_OFFER_TOKENS:
        return False
    if any(token.isdigit() and 1900 <= int(token) <= 2100 for token in tokens):
        return False
    return all(token in GENERIC_OFFER_TOKENS or token in GENERIC_RESOURCE_UNITS
               or token.isdigit() for token in tokens)


def canonical_key(candidate: Candidate) -> str:
    reviewed = reviewed_campaign_url(candidate.metadata.get('campaign_review'), candidate.url, candidate.title)
    if reviewed:
        return hashlib.sha256(('reviewed-public-campaign:' + reviewed).encode('utf-8')).hexdigest()[:24]
    normalized = normalize_title(candidate.metadata.get('campaign_title', candidate.title))
    tokens = set(normalized.split())
    if not normalized or tokens <= GENERIC_OFFER_TOKENS:
        # Preserve the legacy key for old URL-only generic titles.
        normalized = normalize_url(candidate.url)
    elif _generic_resource_title(tokens):
        # Preserve distinct resource sizes on the same offer page as well as
        # vendor identity. Tracking-only URL variants remain equivalent.
        normalized = normalized + '|' + normalize_url(candidate.url)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:24]


def reviewed_campaign_url(review, member_url: str, title: str | None = None) -> str | None:
    if not isinstance(review, dict) or review.get('method') != 'normal_browser_read':
        return None
    members = review.get('member_urls')
    if not isinstance(members, list) or not 2 <= len(members) <= 20 or not all(isinstance(value, str) for value in members):
        return None
    if normalize_url(member_url) not in {normalize_url(value) for value in members}:
        return None
    titles = review.get('member_titles')
    if not isinstance(titles, dict) or not all(isinstance(titles.get(url), str) and titles[url].strip() for url in members):
        return None
    if title is not None:
        known = next(titles[url] for url in members if normalize_url(url) == normalize_url(member_url))
        if normalize_title(title) != normalize_title(known):
            return None
    try:
        url = review.get('campaign_url', '')
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or parsed.hostname != 'gleam.io' or parsed.username or parsed.password
                or parsed.port not in (None, 443) or parsed.query or parsed.fragment
                or not re.fullmatch(r'/[A-Za-z0-9]{5}', parsed.path)):
            return None
        return 'https://gleam.io' + parsed.path
    except (TypeError, ValueError):
        return None
