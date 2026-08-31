from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def test_keyword_dictionary_has_required_columns():
    df = pd.read_csv(ROOT / 'config' / 'keyword_dictionary_v1_3.csv')
    required = {'category','term_id','canonical_term','search_variant','active'}
    assert required.issubset(df.columns)
    assert len(df) > 0

def test_dataset_registry_has_required_columns():
    df = pd.read_csv(ROOT / 'config' / 'dataset_canonical_registry_v1_4.csv')
    required = {'dataset_id','preferred_dataset_name','dataset_provider','preferred_access_url','canonical_apa_reference'}
    assert required.issubset(df.columns)
    assert len(df) > 0
