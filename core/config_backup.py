"""Fingerprint-checked rollback of public, read-only configuration only."""
import argparse
import hashlib
import json
import os
import uuid
from pathlib import Path


FILES = ('sources.yaml', 'keywords.json', 'official-trace.json', 'security-policy.json')


def validate(payloads):
    values = {name: json.loads(content.decode('utf-8-sig')) for name, content in payloads.items()}
    policy = values['security-policy.json']
    required = ('allow_claim', 'allow_payment', 'allow_posting', 'allow_cookie_export',
                'allow_challenge_bypass', 'allow_account_creation', 'telegram_send_enabled')
    if any(policy.get(key) is not False for key in required):
        raise ValueError('READ_ONLY_POLICY_REQUIRED')
    for source in values['sources.yaml']['sources']:
        if source.get('kind') in ('browser', 'reddit_oauth') and source.get('enabled') is not False:
            raise ValueError('MANUAL_AUTH_SOURCES_MUST_REMAIN_DISABLED')
        if source.get('challenge_bypass'):
            raise ValueError('CHALLENGE_BYPASS_REJECTED')


def backup_config(root):
    root = Path(root).resolve()
    payloads = {name: (root / 'config' / name).read_bytes() for name in FILES}
    validate(payloads)
    return write_snapshot(root, payloads)


def write_snapshot(root, payloads, rescue_only=False):
    destination = root / 'evidence/config-backups' / uuid.uuid4().hex
    destination.mkdir(parents=True)
    manifest = {'schema_version': 1, 'rescue_only': rescue_only, 'files': {}, 'missing_files': [name for name in FILES if name not in payloads]}
    for name, content in payloads.items():
        (destination / name).write_bytes(content)
        manifest['files'][name] = hashlib.sha256(content).hexdigest()
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return destination


def restore_config(root, backup, dry_run=False):
    root, backup = Path(root).resolve(), Path(backup).resolve()
    allowed = (root / 'evidence/config-backups').resolve()
    if not backup.is_relative_to(allowed) or backup == allowed:
        raise ValueError('PROJECT_CONFIG_BACKUP_REQUIRED')
    manifest = json.loads((backup / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1 or manifest.get('rescue_only'):
        raise ValueError('VALIDATED_CONFIG_SNAPSHOT_REQUIRED')
    if set(manifest['files']) != set(FILES):
        raise ValueError('CONFIG_BACKUP_FILE_SET_MISMATCH')
    payloads = {name: (backup / name).read_bytes() for name in FILES}
    for name, content in payloads.items():
        if hashlib.sha256(content).hexdigest() != manifest['files'][name]:
            raise ValueError('CONFIG_BACKUP_HASH_MISMATCH')
    validate(payloads)
    if dry_run:
        return {'dry_run': True, 'files': list(FILES)}
    current = {name: (root / 'config' / name).read_bytes() for name in FILES if (root / 'config' / name).exists()}
    rescue = write_snapshot(root, current, rescue_only=True)
    for name, content in payloads.items():
        target = root / 'config' / name
        temporary = target.with_name(name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            temporary.write_bytes(content)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return {'restored': list(FILES), 'rescue_backup': str(rescue)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path('C:/WoolRadar'))
    parser.add_argument('command', choices=('backup', 'restore'))
    parser.add_argument('--backup', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.command == 'backup':
        print(backup_config(args.root))
    elif args.backup is None:
        parser.error('--backup required for restore')
    else:
        print(json.dumps(restore_config(args.root, args.backup, args.dry_run)))
