"""Small local health summaries; do not expose raw source/evidence payloads."""
from .models import utc_now


def status_summary(db):
    with db.connect() as conn:
        states = {row[0]: row[1] for row in conn.execute(
            'SELECT status,count(*) FROM events GROUP BY status')}
        notices = {row[0]: row[1] for row in conn.execute(
            'SELECT result,count(*) FROM notifications GROUP BY result')}
    fields = ('node', 'finished_at', 'status', 'items', 'error_code')
    return {'checked_at': utc_now(), 'event_count': sum(states.values()),
            'event_states': states, 'notification_states': notices,
            'nodes': [{key: row[key] for key in fields} for row in db.latest_node_runs()],
            'warning': '任务正常退出不等于真实采集；items与来源错误须一起查看。休眠关机期间不采集。'}
