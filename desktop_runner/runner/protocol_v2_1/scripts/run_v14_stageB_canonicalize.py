#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--stageA', required=True)
    ap.add_argument('--registry', required=True)
    ap.add_argument('--crosswalk', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    raw=pd.read_csv(args.stageA)
    registry=pd.read_csv(args.registry)
    cross=pd.read_csv(args.crosswalk)
    key_col='original_or_normalized_candidate' if 'original_or_normalized_candidate' in cross.columns else cross.columns[0]
    cross['_key']=cross[key_col].astype(str).str.strip().str.lower()
    raw['_key']=raw['normalized_candidate_string'].astype(str).str.strip().str.lower()
    mapped=raw.merge(cross, on='_key', how='left', suffixes=('','_crosswalk'))
    mapped=mapped.merge(registry, on='dataset_id', how='left', suffixes=('','_registry'))
    mapped.to_csv(out/'Dataset_Mentions_StageB_Mapped.csv', index=False)
    registry.to_csv(out/'Dataset_Canonical_Registry.csv', index=False)
    cross.drop(columns=['_key']).to_csv(out/'Dataset_Name_Crosswalk.csv', index=False)
    qa=mapped[mapped['dataset_id'].isna()].groupby('normalized_candidate_string').agg(rows=('mention_id','count'),docs=('doc_id','nunique')).reset_index().sort_values('rows',ascending=False)
    qa.to_csv(out/'Dataset_QA_Review_Queue.csv', index=False)
if __name__=='__main__': main()
