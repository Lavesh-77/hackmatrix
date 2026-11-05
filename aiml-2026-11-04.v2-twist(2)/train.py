"""Fit a baseline using only a chosen public training file; split locally first."""
import argparse
import gzip
import json
from pathlib import Path
from features import fit
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', default='training.json.gz')
    parser.add_argument('--output', default='starter_model.json')
    args = parser.parse_args()
    cases = json.loads(gzip.decompress(Path(args.data).read_bytes()))
    model = fit(cases, lambda domain, observation: observation)
    Path(args.output).write_text(json.dumps(model)+'\n')
