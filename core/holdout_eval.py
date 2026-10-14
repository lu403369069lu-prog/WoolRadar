"""Read-only, fail-closed evaluation of frozen public-corpus holdout labels.

This measures candidate retrieval and conditional pairwise dedup, not claimability,
account eligibility, source uptime, or the recall of unobserved platform posts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def pair_count(value: int) -> int:
    return value * (value - 1) // 2


def fraction(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def evaluate(root: Path, labels_path: Path, expected_code_ref: str | None = None) -> dict:
    from .collector import build_candidate
    from .config import load_sources
    from .dedup import canonical_key

    labels = json.loads(Path(labels_path).read_text(encoding='utf-8'))
    if labels.get('schema_version') != 1 or labels.get('split') != 'holdout':
        raise ValueError('HOLDOUT_SCHEMA_OR_SPLIT_REQUIRED')
    declared_ref = labels.get('frozen_code_ref')
    if not isinstance(declared_ref, str) or not declared_ref.strip():
        raise ValueError('FROZEN_CODE_REF_REQUIRED')
    # A human-readable declaration is not an attestation of the executed code.
    # Callers seeking a frozen-code evaluation must supply an independently
    # verified checkout commit; do not silently trust labels alone.
    if expected_code_ref is not None:
        if not re.fullmatch(r'[0-9a-fA-F]{40}', expected_code_ref):
            raise ValueError('EXPECTED_CODE_REF_MUST_BE_FULL_SHA')
        if declared_ref.lower() != expected_code_ref.lower():
            raise ValueError('FROZEN_CODE_REF_MISMATCH')
    snapshots = labels.get('snapshots')
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError('NONEMPTY_HOLDOUT_SNAPSHOTS_REQUIRED')
    sources = {s['id']: s for s in load_sources(Path(root) / 'config' / 'sources.yaml')}
    counts = Counter()
    predictions = []
    sources_seen = set()
    details = []
    for entry in snapshots:
        sid = entry.get('source_id')
        if (not isinstance(sid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', sid)
                or sid in sources_seen or sid not in sources):
            raise ValueError('DUPLICATE_OR_UNKNOWN_SOURCE_ID')
        sources_seen.add(sid)
        filename = Path(root) / 'data' / 'public-corpus' / (sid + '.json')
        data = filename.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry.get('sha256'):
            raise ValueError('CORPUS_SNAPSHOT_DIGEST_MISMATCH')
        snapshot = json.loads(data)
        rows = snapshot.get('rows')
        if (snapshot.get('schema_version') != 1 or snapshot.get('source_id') != sid
                or snapshot.get('sampled_at') != entry.get('sampled_at')
                or snapshot.get('rows_truncated') is not False
                or not isinstance(rows, list) or snapshot.get('fetched_count') != len(rows)
                or snapshot.get('stored_count') != len(rows)):
            raise ValueError('INCOMPLETE_OR_MISMATCHED_CORPUS')
        annotations = entry.get('labels')
        if not isinstance(annotations, list) or len(annotations) != len(rows):
            raise ValueError('EVERY_SAMPLED_ROW_REQUIRES_ONE_LABEL')
        by_index = {}
        for label in annotations:
            index = label.get('index')
            if type(index) is not int or index < 0 or index >= len(rows) or index in by_index:
                raise ValueError('INVALID_OR_DUPLICATED_ROW_INDEX')
            if 'offer' not in label or (label['offer'] is not None and type(label['offer']) is not bool):
                raise ValueError('LABEL_MUST_BE_BOOLEAN_OR_NULL')
            if label.get('offer') is True and not (isinstance(label.get('campaign_id'), str)
                                                  and label['campaign_id'].strip()):
                raise ValueError('POSITIVE_OFFER_REQUIRES_CAMPAIGN_ID')
            by_index[index] = label
        for index, row in enumerate(rows):
            if not isinstance(row.get('accepted'), bool):
                raise ValueError('CORPUS_ACCEPTED_MUST_BE_BOOLEAN')
            label = by_index[index]
            truth = label['offer']
            if truth is None:
                counts['unknown'] += 1
                continue
            counts['labeled'] += 1
            selected = row['accepted']
            if selected and truth:
                counts['tp'] += 1
                candidate = build_candidate(row, sources[sid], sources[sid]['owner_node'])
                predictions.append((canonical_key(candidate), candidate.batch_id, label['campaign_id']))
            elif selected:
                counts['fp'] += 1
            elif truth:
                counts['fn'] += 1
            else:
                counts['tn'] += 1
        details.append({'source_id': sid, 'fetched_count': len(rows), 'labeled_count': len(rows)
                        - sum(label['offer'] is None for label in annotations)})
    pred_counts = Counter((key, batch) for key, batch, _ in predictions)
    truth_counts = Counter(campaign for _, _, campaign in predictions)
    joint_counts = Counter(predictions)
    # Actual pair matches: identical predicted identity AND identical adjudicated campaign.
    tp_pairs = sum(pair_count(n) for n in joint_counts.values())
    predicted_pairs = sum(pair_count(n) for n in pred_counts.values())
    true_pairs = sum(pair_count(n) for n in truth_counts.values())
    result = {
        'frozen_code_ref': labels['frozen_code_ref'],
        'sample_sources': len(details), 'sources': details,
        'counts': {name: counts[name] for name in ('labeled', 'unknown', 'tp', 'fp', 'fn', 'tn')},
        'lead_precision': fraction(counts['tp'], counts['tp'] + counts['fp']),
        'lead_recall': fraction(counts['tp'], counts['tp'] + counts['fn']),
        'dedup_population': 'true-positive, selected leads only',
        'dedup_pairs': {'true_positive': tp_pairs, 'predicted': predicted_pairs,
                        'true': true_pairs, 'false_merge': predicted_pairs - tp_pairs,
                        'false_split': true_pairs - tp_pairs},
        'dedup_pair_precision': fraction(tp_pairs, predicted_pairs),
        'dedup_pair_recall': fraction(tp_pairs, true_pairs),
        'limitations': ('Frozen bounded public-corpus rows only; no platform-wide recall, '
                        'no claim eligibility, no unverifiable 95% assertion. Independence '
                        'of annotations must be externally audited.'),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path, help='isolated snapshot root, not production')
    parser.add_argument('--labels', required=True, type=Path, help='locally curated holdout labels JSON')
    parser.add_argument('--expected-code-ref', required=True, help='independently verified full checkout commit SHA; a clean checkout must be checked separately')
    args = parser.parse_args()
    print(json.dumps(evaluate(args.root, args.labels, expected_code_ref=args.expected_code_ref), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
