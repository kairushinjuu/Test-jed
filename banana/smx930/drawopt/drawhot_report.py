#!/usr/bin/env python3
"""Parse bounded v0.16 sampled draw setup phases from game logs (not GPU simulation)."""
import argparse,json,re,statistics
from pathlib import Path
RG=re.compile(r'draw-hot us: prepare ([\d.]+), hazards ([\d.]+), pass ([\d.]+), texmask ([\d.]+), key ([\d.]+)')
PH=('prepare','hazards','pass','texmask','key')

def analyze(log):
    samples=[]
    for line in log.splitlines():
        m=RG.search(line)
        if m: samples.append(dict(zip(PH,map(float,m.groups()))))
    med={n:round(statistics.median(s[n] for s in samples),3) for n in PH} if samples else None
    ranked=sorted(med, key=med.get,reverse=True) if med else []
    return {'sample_windows':len(samples),'median_microseconds_per_sampled_draw_by_phase':med,'largest_median_phase':ranked[0] if ranked else None,
            'note':'CPU sampled-draw phase means; warmup and scene transitions are not matched. Reported values are not sustained FPS.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    s=json.dumps(analyze(a.log.read_text(errors='replace')),indent=2)
    if a.output:a.output.write_text(s+'\n')
    print(s)
