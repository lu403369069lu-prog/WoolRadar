"""Pure policy for an authenticated official usage snapshot. No network or AI."""
def policy(snapshot):
    snapshot=snapshot if isinstance(snapshot,dict) else {}
    remaining=[]
    for name in ('primary','secondary'):
        window=snapshot.get(name)
        value=window.get('usedPercent') if isinstance(window,dict) else None
        if type(value) in (int,float) and 0 <= value <= 100:
            remaining.append(100-value)
    percent=min(remaining) if remaining else None
    if snapshot.get('limit_reached') is True or percent == 0:
        stage='quota_paused'
    elif percent is None:
        stage='unknown'
    elif percent <= 10:
        stage='quota_critical'
    elif percent <= 20:
        stage='quota_risk'
    else:
        stage='normal'
    return {'stage':stage,'remaining_percent':percent,
            'allow_new_model_tasks':stage in ('normal','unknown'),
            'allow_large_task':stage=='normal',
            'checkpoint_required':stage!='normal',
            'auto_resume_permitted':False,
            'provider_switch_permitted':False}
