import pandas as pd
import json
import os
from datetime import datetime
from sklearn.model_selection import train_test_split

def make_splits(df: pd.DataFrame, stratify_col: str = 'target', test_size=0.15, val_size=0.15, random_state=42) -> dict:
    """
    Робить стратифікований поділ датасету на train, val та test.
    Пропорції за замовчуванням: 70% train / 15% val / 15% test.
    """
    df = df.dropna(subset=[stratify_col]).copy()
    temp_size = test_size + val_size
    train_df, temp_df = train_test_split(
        df, 
        test_size=temp_size, 
        random_state=random_state, 
        stratify=df[stratify_col]
    )

    relative_test_size = test_size / temp_size
    val_df, test_df = train_test_split(
        temp_df, 
        test_size=relative_test_size, 
        random_state=random_state, 
        stratify=temp_df[stratify_col]
    )
    
    return {"train": train_df, "val": val_df, "test": test_df}

def save_splits(splits: dict, sample_dir: str, docs_dir: str, random_state: int, strategy: str, stratify_col: str):
    """
    Зберігає ID рядків у .txt файли та генерує маніфест у .json.
    """
    os.makedirs(sample_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)
    
    manifest = {
        "created_at": datetime.now().isoformat(),
        "strategy": strategy,
        "stratify_column": stratify_col,
        "random_seed": random_state,
        "splits": {}
    }

    for split_name, split_df in splits.items():
        ids = split_df.index.astype(str).tolist()
        file_path = os.path.join(sample_dir, f"splits_{split_name}_ids.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ids))
    
        manifest["splits"][split_name] = {
            "size": len(ids),
            "file": f"data/sample/splits_{split_name}_ids.txt"
        }

    manifest_path = os.path.join(docs_dir, "splits_manifest_lab5.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)
