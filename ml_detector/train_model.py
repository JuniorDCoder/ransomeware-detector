import argparse
import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def load_dataset(path: Optional[str]) -> pd.DataFrame:
    if path and os.path.exists(path):
        return pd.read_csv(path)

    # Fallback synthetic dataset
    rng = np.random.default_rng(42)
    size = rng.integers(1024, 10_000_000, 500)
    entropy = rng.uniform(4.0, 8.0, 500)
    ext_exe = rng.integers(0, 2, 500)
    ext_script = rng.integers(0, 2, 500)
    label = ((entropy > 7.2) & ((ext_exe == 1) | (ext_script == 1))).astype(int)

    return pd.DataFrame(
        {
            "size": size,
            "entropy": entropy,
            "ext_exe": ext_exe,
            "ext_script": ext_script,
            "label": label,
        }
    )


def train_model(dataset_path: Optional[str], output_path: str) -> None:
    df = load_dataset(dataset_path)
    X = df[["size", "entropy", "ext_exe", "ext_script"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds))

    joblib.dump(model, output_path)
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", help="Path to CSV dataset", default=None)
    parser.add_argument("--out", help="Output model path", default="models/ransomware_model.joblib")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    train_model(args.data, args.out)
