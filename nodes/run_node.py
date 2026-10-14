from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(default_node: str | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', default=default_node, required=default_node is None)
    parser.add_argument('--root', type=Path, default=Path(__file__).parents[1])
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from core.collector import collect_for_node, write_collection
    from core.pipeline import Pipeline

    result = collect_for_node(root, args.node, force=args.force)
    items_path, status_path = write_collection(root, result)
    Pipeline(root).ingest_node(args.node)
    failed = sum(1 for source in result.sources if source.status == 'FAILED')
    print(f'node={args.node} candidates={len(result.candidates)} failed_sources={failed}')
    print(f'items={items_path}')
    print(f'status={status_path}')
    return 2 if failed and not result.candidates else 0


if __name__ == '__main__':
    raise SystemExit(main())
