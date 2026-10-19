from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path

from .db import Database
from .models import Candidate
from .verifier import VerificationEngine


@dataclass(slots=True)
class ReportPaths:
    markdown: Path
    json: Path


class ReportGenerator:
    def __init__(self, db: Database, report_dir: Path, noise_audit=None):
        self.db = db
        self.report_dir = Path(report_dir)
        self.noise_audit = noise_audit

    def generate(self, date: str) -> ReportPaths:
        audit_snapshot = self.noise_audit.snapshot() if self.noise_audit is not None else None
        self.report_dir.mkdir(parents=True, exist_ok=True)
        # Build and revalidate one coherent database snapshot. File rendering
        # happens after release; reindex cannot swap IDs between these reads.
        with self.db.candidate_transaction():
            events = self.db.list_events()
            runs = self.db.latest_node_runs()
            for event in events:
                if event['status'] == 'CLAIMABLE':
                    result = VerificationEngine().evaluate(Candidate(event['node'], event['source'],
                        event['title'], event['primary_url']), self.db.get_evidence(event['id']))
                    if result.status.value != event['status'] or result.claim_scope != event['claim_scope']:
                        self.db.set_status(event['id'], result.status, result.reason, result.claim_scope)
                        event['status'], event['claim_scope'] = result.status.value, result.claim_scope
                event['evidence'] = [
                    {'kind': item.kind, 'url': item.url, 'checked_at': item.checked_at,
                     'excerpt': item.excerpt, 'claims': item.claims, 'provenance_key': item.provenance_key}
                    for item in self.db.get_evidence(event['id'])
                ]
            with self.db.connect() as conn:
                notices = [dict(row) for row in conn.execute('SELECT id,event_id,batch_id,channel,created_at,result,attempts FROM notifications ORDER BY id DESC LIMIT 100')]
        all_events = events
        excluded = []
        if self.noise_audit is not None:
            for event in all_events:
                event['report_audit'] = audit_snapshot.decision(event)
            excluded = [e for e in all_events if e['report_audit']['excluded']]
            events = [e for e in all_events if not e['report_audit']['excluded']]
        today_events = [event for event in events if datetime.fromisoformat(
            event['first_seen'].replace('Z', '+00:00')).astimezone(
                timezone(timedelta(hours=8))).date().isoformat() == date]
        payload = {'date': date, 'timezone': 'Asia/Shanghai', 'events': all_events, 'node_runs': runs, 'notifications': notices}
        if self.noise_audit is not None:
            payload['noise_audit'] = {'excluded': len(excluded), 'visible': len(events),
                                     'events_preserved': len(all_events), 'ledger_sha256': audit_snapshot.digest}
        json_path = self.report_dir / f'{date}-daily.json'
        md_path = self.report_dir / f'{date}-daily.md'
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

        def official_payment_risks(event):
            return [risk for risk in ('card_required', 'auto_renew')
                    if any(evidence['kind'] == 'official' and
                           evidence['claims'].get(risk) is True
                           for evidence in event['evidence'])]

        payment_risk_events = [event for event in events if official_payment_risks(event)]
        sections = [
            ('今日新发现', today_events),
            ('官方已核实、正在开放的福利', [e for e in events if e['status'] == 'CLAIMABLE']),
            ('限时高价值活动', [e for e in events if json.loads(e['metadata_json']).get('high_value')]),
            ('绑卡或自动续费风险：待人工核验', payment_risk_events),
            ('官方来源已找到、开放与条件待核验', [e for e in events if e['status'] == 'OFFICIAL_VERIFIED'
                and not official_payment_risks(e)]),
            ('需要账号核验的活动', [e for e in events if json.loads(e['metadata_json']).get('account_required') is True
                or any(item['claims'].get('account_required') is True for item in e['evidence'])]),
            ('已结束或存在风险的活动', [e for e in events if e['status'] in ('EXPIRED', 'CONFLICTED', 'FAILED')]),
        ]
        lines = [f'# WoolRadar 中文简报 — {date}', '', '> 领取资格结论仅以已保存证据为准；公开可申请不等于个人账号符合资格。',
                 '> 今日新发现指本地首次发现，不表示今天发布或重新开放；历史 RSS 条目可能已结束。', '']
        for title, rows in sections:
            lines.extend([f'## {title}', ''])
            if not rows:
                lines.extend(['- 无已核实条目', ''])
            for row in rows:
                lines.extend([
                    f"- [{row['title']}]({row['primary_url']})",
                    f"  - 状态：{row['status']}；范围：{row['claim_scope']}；来源：{row['source']}；节点：{row['node']}",
                    f"  - 原帖发布时间：{row['published_at'] or '未知'}；发现时间：{row['first_seen']}",
                ])
                risk_flags = official_payment_risks(row)
                if risk_flags:
                    labels = [label for field, label in (('card_required', '绑卡'),
                        ('auto_renew', '自动续费')) if field in risk_flags]
                    lines.append('  - 费用风险：官方证据包含' + '、'.join(labels) +
                                 '要求，须人工核验；不得视为无条件免费领取。')
                for evidence in row['evidence']:
                    if evidence['claims']:
                        lines.append(f"  - 核验时间：{evidence['checked_at']}；证据：{evidence['url']}")
                        lines.append('  - 条件与未知项：' + json.dumps(evidence['claims'], ensure_ascii=False))
        if self.noise_audit is not None:
            lines.extend(['## 历史噪声审计（原事件与证据保留）', ''])
            if not excluded:
                lines.append('- 无当前有效的排除记录')
            for row in excluded:
                audit = row['report_audit']
                lines.append(f"- [{row['title']}]({row['primary_url']})：仅排除报告正文，事件 #{row['id']}")
                lines.append('  - 审核人：' + json.dumps(audit['reviewer'], ensure_ascii=False) +
                             '；时间：' + audit['reviewed_at'] +
                             '；原因：' + json.dumps(audit['reason'], ensure_ascii=False))
            lines.append('')
        lines.extend(['## 采集节点故障与漏报情况', ''])
        if not runs:
            lines.append('- 尚无节点运行记录')
        for run in runs:
            lines.append(f"- {run['node']}: {run['status']}，采集 {run['items']} 条，错误 {run['error_code'] or '无'}")
        lines.extend(['', '## 安全边界', '', '- 本系统默认只读；未执行领取、授权、支付、发帖、点赞或账号创建。', ''])
        md_path.write_text('\n'.join(lines), encoding='utf-8')
        return ReportPaths(md_path, json_path)
