"""Detect recurring payments with Ward hierarchical clustering."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "mock_transactions.csv"


def _load_transactions(data_path: Path | str = DATA_PATH) -> pd.DataFrame:
    frame = pd.read_csv(data_path)
    required = {"transaction_id", "merchant", "amount", "date"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required transaction columns: {sorted(missing)}")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["amount"] = pd.to_numeric(frame["amount"], errors="raise")
    return frame.sort_values(["merchant", "date", "transaction_id"]).reset_index(drop=True)


def detect_subscriptions(
    data_path: Path | str = DATA_PATH,
    distance_threshold: float = 1.5,
) -> tuple[list[dict], pd.DataFrame]:
    """
    Detect recurring, low-variance merchant charges.

    Features are amount and elapsed days since the previous transaction from
    the same merchant. A cluster is retained only when it has at least three
    charges, a roughly monthly interval, and a stable amount.
    """
    transactions = _load_transactions(data_path)
    transactions["days_since_previous"] = (
        transactions.groupby("merchant", sort=False)["date"].diff().dt.days.fillna(0)
    )

    if transactions.empty:
        return [], transactions

    detected: list[dict] = []

    for merchant, merchant_transactions in transactions.groupby("merchant", sort=True):
        merchant_transactions = merchant_transactions.sort_values("date").copy()
        if len(merchant_transactions) < 3:
            continue

        features = merchant_transactions[["amount", "days_since_previous"]].to_numpy()
        normalized = StandardScaler().fit_transform(features)
        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            linkage="ward",
        )
        merchant_transactions["cluster"] = model.fit_predict(normalized)

        for cluster_id, cluster in merchant_transactions.groupby("cluster"):
            if len(cluster) < 3:
                continue

            dates = cluster["date"].sort_values()
            intervals = dates.diff().dt.days.dropna().to_numpy()
            if len(intervals) < 2:
                continue

            average_interval = float(np.mean(intervals))
            interval_variance = float(np.var(intervals))
            interval_std = float(np.std(intervals))
            amount_mean = float(cluster["amount"].mean())
            amount_std = float(cluster["amount"].std(ddof=0))
            amount_cv = amount_std / amount_mean if amount_mean else float("inf")

            # A true recurring payment should be approximately monthly, not
            # merely repeated at random times, and should have stable pricing.
            if (
                28.0 <= average_interval <= 32.0
                and interval_variance <= 9.0
                and interval_std <= 3.0
                and amount_cv <= 0.08
            ):
                detected.append(
                    {
                        "merchant": str(merchant),
                        "average_amount": round(amount_mean, 2),
                        "average_interval": round(average_interval, 1),
                        "interval_std": round(interval_std, 2),
                        "transaction_count": int(len(cluster)),
                        "last_transaction_date": dates.iloc[-1],
                        "cluster_id": int(cluster_id),
                    }
                )

    detected.sort(key=lambda subscription: subscription["merchant"])
    return detected, transactions


def detect_recurring_subscriptions(
    data_path: Path | str = DATA_PATH,
) -> list[dict]:
    """Compatibility-friendly detector API returning only subscription records."""
    detected, _ = detect_subscriptions(data_path)
    return detected
