"""Prepare a daily queue without starting renders, schedules, or uploads."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def plan(day, catalog, completed=(), count=5):
    date.fromisoformat(day)
    ids=[episode['id'] for episode in catalog]
    if len(ids)!=len(set(ids)):raise ValueError('Catalog story IDs must be unique')
    if not 1<=count<=5:raise ValueError('Phase 2 planning supports one to five episodes')
    selected=[episode for episode in catalog if episode['id'] not in set(completed)][:count]
    items=[]
    for episode in selected:
        key=hashlib.sha256(f"{day}:{episode['id']}:pip-capybara-v1".encode()).hexdigest()[:20]
        items.append({'job_id':key,'story_id':episode['id'],'title':episode['title'],
                      'renderer':episode['renderer'],'status':'ready_for_render_test' if episode['implemented'] else 'needs_renderer',
                      'seed':int(key[:8],16)})
    blockers=[]
    if len(items)<count:blockers.append('Insufficient unused original stories; do not repeat an old video to fill the quota')
    if any(item['status']=='needs_renderer' for item in items):blockers.append('Some original story concepts do not yet have implemented renderers')
    return {'date':day,'target':count,'automatic_execution':False,'youtube_uploads':False,
            'ready_for_batch_test':len(items)==count and not blockers,'blockers':blockers,'jobs':items}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--date',required=True,help='YYYY-MM-DD in the production timezone')
    p.add_argument('--ledger',type=Path,help='JSON array of already completed story IDs')
    p.add_argument('--out',type=Path,default=Path('build/daily-plan.json'))
    args=p.parse_args()
    catalog=json.loads((ROOT/'episodes/catalog.json').read_text())
    config=json.loads((ROOT/'config/production.json').read_text())
    completed=json.loads(args.ledger.read_text()) if args.ledger else []
    result=plan(args.date,catalog,completed,config['target_episodes_per_day'])
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
