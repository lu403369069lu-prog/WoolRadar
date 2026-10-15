from __future__ import annotations
from datetime import datetime, timezone, timedelta
import re

from .models import Candidate, Evidence, Status, VerificationResult


class VerificationEngine:
    def evaluate(self, candidate: Candidate, evidence: list[Evidence]) -> VerificationResult:
        groups: list[set[str]] = []
        for item in evidence:
            keys = {'url:' + item.url}
            if item.provenance_key:
                keys.add('provenance:' + item.provenance_key)
            overlaps = [group for group in groups if group & keys]
            for group in overlaps:
                keys.update(group)
                groups.remove(group)
            groups.append(keys)
        provenance = groups
        official = [item for item in evidence if item.kind == 'official']
        conflicting = any(item.claims.get('conflict') for item in evidence)
        # Free-form eligibility descriptions can add detail without disagreeing.
        # Compare explicit conditions; retain narrative for human review.
        fields = ('open', 'public', 'card_required', 'auto_renew', 'region', 'account_required')
        for name in fields:
            values = {repr(item.claims[name]) for item in evidence
                      if name in item.claims and item.claims[name] is not None and item.claims[name] != 'unknown'}
            conflicting = conflicting or len(values) > 1
        constraints = [item.claims.get('eligibility_constraints', {}) for item in evidence]
        constraints = [value for value in constraints if isinstance(value, dict)]
        for name in {key for value in constraints for key in value}:
            values = {repr(value[name]) for value in constraints
                      if name in value and value[name] not in (None, 'unknown')}
            conflicting = conflicting or len(values) > 1
        expired = any(item.claims.get('open') is False for item in official)
        ambiguous_expiry = False
        now = datetime.now(timezone.utc)
        for item in official:
            deadline = item.claims.get('expires_at')
            if deadline in (None, '', 'unknown'):
                continue
            try:
                ends = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                if ends.tzinfo is None:
                    raise ValueError('EXPIRY_TIMEZONE_REQUIRED')
                expired = expired or ends <= now
            except (ValueError, TypeError, AttributeError):
                ambiguous_expiry = True
        unknown_capacity = not any(
            isinstance(item.claims.get('remaining'), (int, float))
            and not isinstance(item.claims.get('remaining'), bool)
            and item.claims['remaining'] >= 0 for item in official
        )

        if conflicting:
            return VerificationResult(Status.CONFLICTED, '官方与社区证据存在冲突', len(provenance),
                                      unknown_capacity=unknown_capacity)
        if expired:
            return VerificationResult(Status.EXPIRED, '官方证据显示活动已结束', len(provenance),
                                      unknown_capacity=unknown_capacity)
        for item in official:
            remaining = item.claims.get('remaining')
            if isinstance(remaining, bool) or not isinstance(remaining, (int, float)) or remaining != 0:
                continue
            try:
                checked = datetime.fromisoformat(item.checked_at.replace('Z', '+00:00'))
                age = now - checked
                fresh_zero = timedelta(0) <= age <= timedelta(hours=24)
            except (ValueError, TypeError, AttributeError):
                fresh_zero = False
            if fresh_zero:
                return VerificationResult(Status.OFFICIAL_VERIFIED, '近期官方证据显示剩余名额为0，尚无可领取库存',
                                          len(provenance), unknown_capacity=False)
        for item in official:
            try:
                checked = datetime.fromisoformat(item.checked_at.replace('Z', '+00:00'))
                age = datetime.now(timezone.utc) - checked
                fresh = timedelta(0) <= age <= timedelta(hours=24)
            except (ValueError, TypeError):
                fresh = False
            if fresh and not ambiguous_expiry and item.claims.get('open') is True and item.claims.get('public') is True:
                # A public announcement cannot establish eligibility of the
                # user's account. No authorized account-proof workflow exists
                # yet, so imported promotion flags must never upgrade scope.
                scope = 'PUBLIC_APPLICATION'
                return VerificationResult(Status.CLAIMABLE, '官方证据支持当前公开申请', len(provenance),
                                          claim_scope=scope, unknown_capacity=unknown_capacity)
        if official:
            reason = '官方到期时间缺少明确格式或时区，尚不能确认可领取' if ambiguous_expiry else '已找到官方来源，但可领取性尚未证实'
            return VerificationResult(Status.OFFICIAL_VERIFIED, reason,
                                      len(provenance), unknown_capacity=unknown_capacity)
        corroborated = False
        for name in fields:
            supporting_groups = set()
            for item in evidence:
                if name not in item.claims or item.claims[name] in (None, 'unknown'):
                    continue
                for index, group in enumerate(groups):
                    if 'url:' + item.url in group:
                        supporting_groups.add(index)
            corroborated = corroborated or len(supporting_groups) >= 2
        if len(provenance) >= 2 and corroborated:
            return VerificationResult(Status.CROSS_CHECKED, '至少两个独立来源相互印证', len(provenance))
        if evidence:
            return VerificationResult(Status.UNKNOWN, '只有单一或转载来源，缺少官方证据', len(provenance))
        return VerificationResult(Status.DISCOVERED, '仅发现候选，尚未核验', 0)

    @staticmethod
    def classify_fetch_failure(status_code: int | None, body: str) -> str:
        sample = body.lower()
        # A normal site may load reCAPTCHA for an unrelated form. Library names
        # alone do not establish that the requested page is a challenge.
        visible = re.sub(r'<(script|style)\b[^>]*>.*?</\1\s*>', '', sample, flags=re.S)
        visible = re.sub(r'<[^>]+>', ' ', visible)
        strong = ('cf-chl-', 'challenge-platform')
        prompts = ('verify you are human', 'complete the captcha', 'solve the captcha',
                   '人机验证', '请完成验证码')
        if any(term in sample for term in strong) or any(term in visible for term in prompts):
            return 'CAPTCHA_REQUIRED'
        if status_code == 429:
            return 'RATE_LIMITED_429'
        if status_code == 403:
            return 'BLOCKED_403'
        if status_code is None:
            return 'NETWORK_ERROR'
        return f'HTTP_{status_code}'
