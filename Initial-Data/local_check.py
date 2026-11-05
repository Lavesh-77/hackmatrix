"""Public-only formula checker; this does not replace the isolated official runtime."""
import gzip
import importlib.util
import json
from pathlib import Path


def evaluate(cases,solution,scales):
    results=[]
    for case in cases:
        observation=case['observation'];response=solution.decide(observation,None);action=response['action']
        predictions=action['predictions'];ids=observation['customers'];selected=action['selected']
        if set(predictions)!=set(ids):raise ValueError('Predict every eligible customer')
        if len(selected)!=observation['budget'] or len(set(selected))!=len(selected) or not set(selected)<=set(ids):raise ValueError('Invalid fixed-budget selection')
        import math
        for pred in predictions.values():
            if set(pred)!={'probability','value'}:raise ValueError('Invalid prediction fields')
            for field,maximum in [('probability',1),('value',2000)]:
                x=pred[field]
                if isinstance(x,bool) or not isinstance(x,(int,float)) or not 0<=x<=maximum or not math.isfinite(x):raise ValueError('Invalid prediction')
        n=len(ids);brier=sum((predictions[k]['probability']-case['targets'][k][0])**2 for k in ids)/n
        mse=sum((predictions[k]['value']-case['targets'][k][1])**2 for k in ids)/n
        oracle=sum(sorted((t[1] for t in case['targets'].values()),reverse=True)[:observation['budget']])
        actual=sum(case['targets'][k][1] for k in selected);capture=actual/oracle if oracle else 1
        results.append({'n':n,'score':40*(1-brier)+30*(1-mse/2000**2)+30*capture,'brier':brier,'value_mse':mse,'capture':capture})
    n=sum(r['n'] for r in results)
    return {k:sum(r[k]*r['n'] for r in results)/n for k in ['score','brier','value_mse','capture']}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--solution',default='starter.py');p.add_argument('--data',default='practice.json.gz');p.add_argument('--scoring',default='scoring.json');args=p.parse_args()
    spec=importlib.util.spec_from_file_location('student',args.solution);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    cases=json.loads(gzip.decompress(Path(args.data).read_bytes()));scales=json.loads(Path(args.scoring).read_text())['scales']
    print(json.dumps(evaluate(cases,module,scales),indent=2))
