"""Generate reproducible synthetic transaction data for SubSweep."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import random

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "mock_transactions.csv"


def generate_transactions(output_path: Path = DATA_PATH, seed: int = 42) -> pd.DataFrame:
    """Create roughly 200 realistic transactions, including recurring subscriptions."""
    rng = random.Random(seed)
    today = date.today()
    six_months_ago = today - timedelta(days=183)
    rows: list[dict] = []

    subscriptions = [
        ("Netflix", 649.00),
        ("Spotify", 119.00),
        ("Cloud Storage", 130.00),
        ("Gym Membership", 1500.00),
        ("Ghost SaaS Trial", 999.00),
    ]

    # Anchor the final charge near a month before today so the demo always
    # produces at least one upcoming payment in the next five days.
    for subscription_index, (merchant, amount) in enumerate(subscriptions):
        charge_count = 7
        anchor_offset = 26 + (subscription_index % 4)
        last_charge = today - timedelta(days=anchor_offset)
        dates = [last_charge]

        for charge_number in range(1, charge_count):
            interval = 30 + rng.choice([-1, 0, 0, 0, 1])
            previous = dates[-1]
            dates.append(previous - timedelta(days=interval))

        for charge_number, charge_date in enumerate(reversed(dates)):
            rows.append(
                {
                    "transaction_id": f"T{len(rows) + 1:05d}",
                    "merchant": merchant,
                    "amount": amount,
                    "date": charge_date.isoformat(),
                }
            )

    one_off_merchants = {
        "Swiggy": (180, 850),
        "Zomato": (220, 950),
        "Uber": (180, 900),
        "Grocery Store": (350, 2200),
        "Coffee House": (120, 450),
    }

    target_one_off_count = 170
    while sum(row["merchant"] in one_off_merchants for row in rows) < target_one_off_count:
        merchant = rng.choice(list(one_off_merchants))
        low, high = one_off_merchants[merchant]
        transaction_date = six_months_ago + timedelta(
            days=rng.randint(0, (today - six_months_ago).days)
        )
        rows.append(
            {
                "transaction_id": f"T{len(rows) + 1:05d}",
                "merchant": merchant,
                "amount": round(rng.uniform(low, high), 2),
                "date": transaction_date.isoformat(),
            }
        )

    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values(["date", "merchant", "transaction_id"]).reset_index(drop=True)
    frame["transaction_id"] = [f"T{i:05d}" for i in range(1, len(frame) + 1)]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


if __name__ == "__main__":
    transactions = generate_transactions()
    print(f"Generated {len(transactions)} transactions at {DATA_PATH}")
