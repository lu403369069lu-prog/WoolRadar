from __future__ import annotations

import json
from pathlib import Path


def load_sources(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('schema_version') != 1 or not isinstance(payload.get('sources'), list):
        raise ValueError('Unsupported sources.yaml schema')
    return payload['sources']


def load_keywords(path: Path) -> list[str]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return [str(item) for item in payload.get('keywords', [])]

