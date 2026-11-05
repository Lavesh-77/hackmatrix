"""Baseline only; replace preparation, features or model as you choose."""
import json
from pathlib import Path
from features import predict
_MODEL = None

def decide(observation, state):
    global _MODEL
    if _MODEL is None:
        _MODEL = json.loads(Path(__file__).with_name('starter_model.json').read_text())
    return {'action': predict(observation, _MODEL), 'state': {}}
