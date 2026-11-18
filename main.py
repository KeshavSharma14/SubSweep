"""SubSweep MVP entry point."""

from __future__ import annotations

from pathlib import Path

from src.generate_data import DATA_PATH as GENERATED_DATA_PATH
from src.generate_data import generate_transactions
from src.detector import DATA_PATH as DETECTOR_DATA_PATH
from src.detector import detect_subscriptions
from src.alerts import calculate_alerts, format_report


def main() -> None:
    data_path = Path(GENERATED_DATA_PATH)
    if not data_path.exists():
        print("Generating synthetic transaction data...")
        frame = generate_transactions(data_path)
        print(f"Created {len(frame)} transactions at {data_path}")

    detected, transactions = detect_subscriptions(DETECTOR_DATA_PATH)
    print(f"\nAnalyzed {len(transactions)} transactions.")
    latest_dataset_date = transactions["date"].max()
    alerts = calculate_alerts(detected, reference_date=latest_dataset_date)
    print("\n" + format_report(alerts))


if __name__ == "__main__":
    main()
