from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .collector import collect_for_node, write_collection
from .db import Database
from .models import Evidence
from .orchestrator import NODES, run_all
from .pipeline import Pipeline
from .report import ReportGenerator


def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description='WoolRadar 7.1 core')
    parser.add_argument('--root', type=Path, default=Path(r'C:\WoolRadar'))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    node_parser = sub.add_parser('run-node')
    node_parser.add_argument('node', choices=NODES)
    node_parser.add_argument('--force', action='store_true')
    all_parser = sub.add_parser('run-all')
    all_parser.add_argument('--force', action='store_true')
    ingest_parser = sub.add_parser('ingest')
    ingest_parser.add_argument('node', choices=NODES)
    report_parser = sub.add_parser('report')
    report_parser.add_argument('--date', default=date.today().isoformat())
    verify_parser = sub.add_parser('verify-file')
    verify_parser.add_argument('path', type=Path)
    status_parser = sub.add_parser('status')
    status_parser.add_argument('--summary', action='store_true')
    sub.add_parser('reindex')
    sub.add_parser('flush-notifications')
    trace_parser = sub.add_parser('trace-official')
    trace_parser.add_argument('event_id', type=int)
    review_parser = sub.add_parser('import-public-review')
    review_parser.add_argument('path', type=Path)
    campaign_parser = sub.add_parser('review-campaign')
    campaign_parser.add_argument('path', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()

    if args.command == 'review-campaign':
        payload = json.loads(args.path.read_text(encoding='utf-8'))
        pipeline = Pipeline(root)
        result = pipeline.db.review_campaign(payload)
        for event in pipeline.db.list_events():
            metadata = json.loads(event['metadata_json'])
            if metadata.get('campaign_review', {}).get('campaign_url') == payload.get('campaign_url'):
                pipeline.apply_evidence(event['id'], [])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == 'import-public-review':
        from .review_import import import_public_review
        payload = json.loads(args.path.read_text(encoding='utf-8'))
        print(json.dumps(import_public_review(root, payload), ensure_ascii=False, indent=2))
        return 0

    if args.command == 'trace-official':
        from .official_trace import OfficialTracer
        print(json.dumps(OfficialTracer(root).trace(args.event_id), ensure_ascii=False, indent=2))
        return 0

    if args.command == 'init':
        db = Database(root / 'data' / 'woolradar.db')
        print(db.path)
        return 0
    if args.command == 'reindex':
        pipeline = Pipeline(root)
        result = pipeline.db.reindex()
        for event in pipeline.db.list_events():
            pipeline.apply_evidence(event['id'], [])
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == 'flush-notifications':
        pipeline = Pipeline(root)
        print(json.dumps(pipeline.notifications.flush(pipeline.notification_policy(),
            local_dir=root / 'reports' / 'notifications'), ensure_ascii=False))
        return 0
    if args.command == 'run-node':
        result = collect_for_node(root, args.node, force=args.force)
        write_collection(root, result)
        print(json.dumps(Pipeline(root).ingest_node(args.node), ensure_ascii=False))
        return 0
    if args.command == 'run-all':
        results = run_all(root, force=args.force)
        print(json.dumps([{'node': r.node, 'exit_code': r.exit_code, 'stdout': r.stdout,
                           'stderr': r.stderr} for r in results], ensure_ascii=False, indent=2))
        return 0 if all(result.exit_code in (0, 2) for result in results) else 1
    if args.command == 'ingest':
        print(json.dumps(Pipeline(root).ingest_node(args.node), ensure_ascii=False))
        return 0
    if args.command == 'report':
        paths = ReportGenerator(Database(root / 'data' / 'woolradar.db'), root / 'reports').generate(args.date)
        print(paths.markdown)
        print(paths.json)
        return 0
    if args.command == 'verify-file':
        payload = json.loads(args.path.read_text(encoding='utf-8'))
        evidence = [Evidence(**item) for item in payload.get('evidence', [])]
        print(json.dumps(Pipeline(root).apply_evidence(int(payload['event_id']), evidence),
                         ensure_ascii=False, indent=2))
        return 0
    if args.command == 'status':
        db = Database(root / 'data' / 'woolradar.db')
        if args.summary:
            from .diagnostics import status_summary
            print(json.dumps(status_summary(db), ensure_ascii=False, indent=2))
            return 0
        print(json.dumps({'nodes': db.latest_node_runs(), 'events': db.list_events()}, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
