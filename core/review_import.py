"""Import deliberately authored public-page review records, not website commands."""
from pathlib import Path
from .models import Candidate, Evidence
from .pipeline import Pipeline
from .official_trace import validate_public_reference


def import_public_review(root: Path, payload: dict) -> list[dict]:
    if payload.get('method') != 'normal_browser_read':
        raise ValueError('EXPLICIT_PUBLIC_REVIEW_REQUIRED')
    if not validate_public_reference(payload.get('url', ''), {'mlh.com', 'www.mlh.com'}):
        raise ValueError('MLH_PUBLIC_REVIEW_URL_REQUIRED')
    pipeline = Pipeline(root)
    results = []
    for record in payload['records']:
        candidate = Candidate('openmagpie', 'MLH 官方公开复核', record['title'], payload['url'],
            summary=record['excerpt'], source_kind='official',
            metadata={'official': True, 'manual_public_review': True,
                      'account_required': record['claims'].get('account_required', False)})
        stored = pipeline.db.upsert_candidate(candidate)
        if stored.notify:
            pipeline.notifications.enqueue(stored.event_id, '', 'local-discovery',
                f"【公开页面人工复核入库；开放与资格未确认】{candidate.title}\n{candidate.url}")
        evidence = Evidence('official', payload['url'], 'mlh-prizes-public-page',
            checked_at=payload['checked_at'], excerpt=record['excerpt'],
            claims={**record['claims'], 'method': 'normal_browser_read'})
        results.append(pipeline.apply_evidence(stored.event_id, [evidence]))
    pipeline.notifications.flush(pipeline.notification_policy(), local_dir=Path(root) / 'reports' / 'notifications')
    return results
