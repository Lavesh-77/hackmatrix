"""Frozen downstream learners. All choices and hyperparameters are preregistered."""
from datetime import datetime
import math
import numpy as np

FEATURE_NAMES = ('recency', 'invoice_frequency', 'recent_value', 'older_value',
                 'basket_value', 'return_ratio', 'cadence', 'tenure', 'observed_gap')
RIDGE = 10.0


def matrix(obs):
    ids = obs['customers']
    if 'prepared_features' in obs:
        features = obs['prepared_features']
        if not isinstance(features, dict) or set(features) != set(ids):
            raise ValueError('Feature customer identity mismatch')
        result = np.asarray([features[c] for c in ids], dtype=float)
        if result.shape != (len(ids), 9) or not np.isfinite(result).all():
            raise ValueError('Expected nine finite causal features per customer')
        return result
    snapshot = datetime.fromisoformat(obs['snapshot'])
    grouped = {cid: [] for cid in ids}
    for r in obs['transactions']['rows']:
        if r[6] in grouped and obs.get('history_start', '') <= r[4] < obs['observed_until']:
            grouped[r[6]].append(r)
    result = []
    for cid in ids:
        orders, ages, recent, older, returns = {}, {}, 0., 0., 0.
        for r in grouped[cid]:
            inv, _, _, quantity, date, price = r[:6]
            if quantity is None or price is None:
                continue
            amount = quantity * price
            if quantity < 0 or str(inv).upper().startswith('C'):
                returns += abs(amount)
                continue
            if quantity <= 0 or price <= 0 or inv is None:
                continue
            age = (snapshot - datetime.fromisoformat(date)).total_seconds() / 86400
            orders[inv] = orders.get(inv, 0.) + amount
            ages[inv] = min(age, ages.get(inv, 9999.))
            if age <= 30:
                recent += amount
            else:
                older += amount
        age_list = sorted(ages.values())
        gaps = [b-a for a, b in zip(age_list, age_list[1:])]
        gap = (snapshot-datetime.fromisoformat(obs['observed_until'])).total_seconds()/86400
        values = [min(age_list) if age_list else 180., len(orders), recent, older,
                  sum(orders.values())/max(1, len(orders)), returns/max(1., sum(orders.values())),
                  sum(gaps)/len(gaps) if gaps else 90., max(age_list) if age_list else 180., gap]
        result.append(values)
    array = np.asarray(result, dtype=float)
    if array.shape != (len(ids), 9) or not np.isfinite(array).all():
        raise ValueError('Invalid causal features')
    return array


def _vector(obs):
    array = matrix(obs).copy()
    for i in (1, 2, 3, 4):
        array[:, i] = np.log1p(np.maximum(0., array[:, i]))
    return np.clip(array, -1e6, 1e6)


def fit(cases, processor):
    xs, ys = [], []
    for case in cases:
        obs = processor('aiml', case['observation'])
        if obs['customers'] != case['observation']['customers']:
            raise ValueError('Processor changed eligible customers')
        xs.append(_vector(obs))
        ys.extend([[case['targets'][c][0], case['targets'][c][1]/2000.] for c in obs['customers']])
    x, y = np.concatenate(xs), np.asarray(ys, dtype=float)
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-8] = 1.
    x = np.column_stack([np.ones(len(x)), (x-mean)/scale])
    penalty = np.eye(10)*RIDGE
    penalty[0, 0] = 0.
    coefficients = np.linalg.solve(x.T@x+penalty, x.T@y)
    return {'mean': mean.tolist(), 'scale': scale.tolist(), 'coefficients': coefficients.tolist()}


def predict(obs, model):
    x = (_vector(obs)-np.asarray(model['mean']))/np.asarray(model['scale'])
    estimates = np.clip(np.column_stack([np.ones(len(x)), x])@np.asarray(model['coefficients']), 0., 1.)
    predictions = {c: {'probability': float(p[0]), 'value': float(p[1]*2000.)} for c, p in zip(obs['customers'], estimates)}
    selected = sorted(predictions, key=lambda c: (-predictions[c]['value'], c))[:obs['budget']]
    return {'predictions': predictions, 'selected': selected}
