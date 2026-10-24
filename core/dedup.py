from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta
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
    'get', 'token', 'tokens',
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
    # Title normalization intentionally preserves compact specs such as 1GB.
    # Decode those only for generic-offer classification so branded keys keep
    # their historical spelling and cross-post identity.
    expanded = set()
    for token in tokens:
        compact = re.fullmatch(r'([0-9]+)(gb|mb|tb)', token)
        if compact:
            expanded.update(compact.groups())
        else:
            expanded.add(token)
    if not expanded & GENERIC_OFFER_TOKENS:
        return False
    # Generic numeric benefits and years cannot establish vendor identity.
    # Preserve the year in the offer title while also scoping by source URL.
    if not any(token.isdigit() or token in GENERIC_RESOURCE_UNITS for token in expanded):
        return False
    return all(token in GENERIC_OFFER_TOKENS or token in GENERIC_RESOURCE_UNITS
               or token.isdigit() for token in expanded)


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
        # In generic offers, "1 GB" and "1GB" describe the same resource.
        # Normalize only this path: branded cross-post historical keys stay intact.
        raw_title = unicodedata.normalize('NFKC', candidate.metadata.get('campaign_title', candidate.title))
        compact_specs = re.sub(r'\b([0-9]+)\s+(gb|mb|tb)\b', r'\1\2', raw_title, flags=re.I)
        normalized = normalize_title(compact_specs) + '|' + normalize_url(candidate.url)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:24]


def _unsafe_review_url(value: object) -> bool:
    # urlsplit/strip can silently discard CR/LF/TAB and leading controls.
    # This would change the identity of a manually approved campaign member.
    return (not isinstance(value, str) or value != value.strip() or any(
        unicodedata.category(ch) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'} for ch in value))


def _unsafe_review_title(value: object) -> bool:
    # A normalized title must not silently erase invisible or directional
    # text changes when binding an article to a manually reviewed campaign.
    return not isinstance(value, str) or any(
        unicodedata.category(ch) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'} for ch in value)


def reviewed_campaign_url(review, member_url: str, title: str | None = None) -> str | None:
    if not isinstance(review, dict) or review.get('method') != 'normal_browser_read':
        return None
    if _unsafe_review_url(member_url):
        return None
    members = review.get('member_urls')
    if (not isinstance(members, list) or not 2 <= len(members) <= 20
            or any(_unsafe_review_url(value) for value in members)):
        return None
    normalized_members = {normalize_url(value) for value in members}
    # A tracking variation or repeated URL is still only one article.
    # Never grant reviewed campaign identity without distinct source members.
    if len(normalized_members) != len(members) or normalize_url(member_url) not in normalized_members:
        return None
    titles = review.get('member_titles')
    if (not isinstance(titles, dict)
            or not all(not _unsafe_review_title(titles.get(url)) and titles[url].strip()
                       for url in members)):
        return None
    if title is not None:
        if _unsafe_review_title(title):
            return None
        known = next(titles[url] for url in members if normalize_url(url) == normalize_url(member_url))
        if normalize_title(title) != normalize_title(known):
            return None
    try:
        url = review.get('campaign_url', '')
        if _unsafe_review_url(url):
            return None
        parsed = urlsplit(url)
        if review.get('review_kind') == 'official_campaign_v2' and parsed.hostname != 'gleam.io':
            return _reviewed_official_identity(review, parsed)
        if (parsed.scheme != 'https' or parsed.hostname != 'gleam.io' or parsed.username or parsed.password
                or parsed.port not in (None, 443) or parsed.query or parsed.fragment
                or not re.fullmatch(r'/[A-Za-z0-9]{5}', parsed.path)):
            return None
        return 'https://gleam.io' + parsed.path
    except (TypeError, ValueError):
        return None


def _reviewed_official_identity(review, parsed) -> str | None:
    """Identity from an explicit local review, never proof of offer eligibility.

    Audit fields record the operator assertion; they are not authenticated by
    this parser. Import only reviewed local files through the existing CLI.
    """
    hosts = review.get('official_hosts')
    if (not isinstance(hosts,list) or not 1 <= len(hosts) <= 20
            or not all(isinstance(h,str) and re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*\.[a-z]{2,63}',h) for h in hosts)
            or parsed.scheme != 'https' or parsed.hostname not in hosts
            or parsed.netloc != parsed.hostname or parsed.query or parsed.fragment
            or not re.fullmatch(r'/[A-Za-z0-9][A-Za-z0-9/_-]{2,200}',parsed.path)
            or '//' in parsed.path):
        return None
    actor,reason,checked=review.get('reviewer'),review.get('reason'),review.get('reviewed_at')
    if (not isinstance(actor,str) or not 1 <= len(actor.strip()) <= 100
            or not isinstance(reason,str) or not 10 <= len(reason.strip()) <= 1000
            or not isinstance(checked,str)):
        return None
    try:
        timestamp=datetime.fromisoformat(checked.replace('Z','+00:00'))
        if timestamp.tzinfo is None or timestamp > datetime.now(timezone.utc)+timedelta(minutes=5):
            return None
    except (TypeError,ValueError):
        return None
    return 'https://' + parsed.hostname + parsed.path
