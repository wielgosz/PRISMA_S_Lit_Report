#!/usr/bin/env python3
import argparse, os, re
from pathlib import Path
import pandas as pd
import fitz
from tqdm import tqdm

def find_pdf(row, pdf_root):
    file_name=str(row.get('file_name','')).strip()
    batch=str(row.get('batch_id','')).strip()
    candidates=[]
    if batch and file_name:
        candidates += [pdf_root/batch/file_name, pdf_root/batch.replace(' ','_')/file_name]
    if file_name:
        candidates += list(pdf_root.rglob(file_name))
    for c in candidates:
        if c.exists(): return c
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--pdf-root', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    corpus=pd.read_csv(args.corpus)
    pdf_root=Path(args.pdf_root); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    qa=[]
    for _,row in tqdm(corpus.iterrows(), total=len(corpus)):
        doc_id=str(row.get('doc_id','')).strip()
        if not doc_id: continue
        pdf=find_pdf(row, pdf_root)
        if not pdf:
            qa.append({'doc_id':doc_id,'status':'pdf_not_found','file_name':row.get('file_name','')})
            continue
        text_parts=[]; page_count=0
        try:
            with fitz.open(pdf) as doc:
                page_count=len(doc)
                for i,page in enumerate(doc, start=1):
                    txt=page.get_text('text') or ''
                    text_parts.append(f'\n\n[[PAGE {i}]]\n{txt}')
            (out/f'{doc_id}.txt').write_text(''.join(text_parts), encoding='utf-8')
            qa.append({'doc_id':doc_id,'status':'extracted','file_name':row.get('file_name',''),'page_count':page_count,'text_file':f'{doc_id}.txt'})
        except Exception as e:
            qa.append({'doc_id':doc_id,'status':'extract_error','file_name':row.get('file_name',''),'error':str(e)})
    pd.DataFrame(qa).to_csv(out/'text_extraction_QA.csv', index=False)
if __name__=='__main__': main()
