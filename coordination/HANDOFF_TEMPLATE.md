# Cross-agent evidence handoff template
Use in the owning technical Issue, not all three Issues. Omit sensitive absolute paths and secrets.

- event_key: `project/task_id/head_sha/event_type`
- project / issue:
- task_id / owner / execution_surface:
- state: proposed | claimed | in_progress | evidence_ready | independently_reviewed | done | blocked | quota_paused | needs_approval | superseded
- base_sha / head_sha (full 40-char SHA, or **unavailable**):
- changed_paths / PR URL:
- commands, platform, runtime, exit codes:
- test numerator and denominator / skipped:
- minimal positive and negative cases:
- evidence file and sanitized hash:
- observed result (facts only):
- proposed interpretation (clearly marked):
- not_verified:
- next_owner / next_step:
- permission_needed:
- codex_quota: available | warning | exhausted | unknown

Evidence classes: A=independent runnable confirmation; B=existing command log plus hash; C=static code examination; D=reported history or hypothesis. Never promote C/D to A.
