"""Calculate subscription due dates and terminal alerts."""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

import pandas as pd


GHOST_TERMS = ("ghost", "trial", "obscure", "unknown")


def calculate_alerts(
    detected_subscriptions: Iterable[dict],
    reference_date: pd.Timestamp | None = None,
) -> list[dict]:
    """Add next-billing dates and alert classifications to subscriptions."""
    if reference_date is None:
        reference_date = pd.Timestamp.now().normalize()
    else:
        reference_date = pd.Timestamp(reference_date).normalize()

    alerts: list[dict] = []
    for subscription in detected_subscriptions:
        record = dict(subscription)
        last_date = pd.Timestamp(record["last_transaction_date"]).normalize()
        interval = float(record["average_interval"])
        next_billing_date = last_date + timedelta(days=round(interval))
        days_until = (next_billing_date - reference_date).days

        merchant_lower = str(record["merchant"]).lower()
        is_ghost = (
            any(term in merchant_lower for term in GHOST_TERMS)
            or int(record["transaction_count"]) <= 4
        )

        record["next_billing_date"] = next_billing_date
        record["days_until"] = int(days_until)
        record["upcoming"] = 0 <= days_until <= 5
        record["ghost_subscription"] = bool(is_ghost)
        alerts.append(record)

    alerts.sort(key=lambda alert: (alert["next_billing_date"], alert["merchant"]))
    return alerts


def format_report(alerts: Iterable[dict]) -> str:
    """Build a concise text report for detected subscriptions and alerts."""
    alerts = list(alerts)
    if not alerts:
        return "No recurring subscriptions detected."

    report_rows: list[list[object]] = []
    alert_messages: list[str] = []

    for alert in alerts:
        report_rows.append(
            [
                alert["merchant"],
                f'₹{float(alert["average_amount"]):,.2f}',
                f'{float(alert["average_interval"]):.1f} days',
                pd.Timestamp(alert["last_transaction_date"]).strftime("%Y-%m-%d"),
                pd.Timestamp(alert["next_billing_date"]).strftime("%Y-%m-%d"),
                alert["transaction_count"],
            ]
        )

        if alert["upcoming"]:
            amount = float(alert["average_amount"])
            alert_messages.append(
                f'UPCOMING CHARGE ALERT: {alert["merchant"]} — ₹{amount:,.2f} '
                f'due {pd.Timestamp(alert["next_billing_date"]).strftime("%Y-%m-%d")} '
                f'({alert["days_until"]} days)'
            )
        if alert["ghost_subscription"]:
            alert_messages.append(
                f'GHOST SUBSCRIPTION: {alert["merchant"]} — low-frequency or '
                "obscure recurring charge"
            )

    table = pd.DataFrame(
        report_rows,
        columns=[
            "Merchant",
            "Avg Amount",
            "Avg Interval",
            "Last Charge",
            "Next Charge",
            "Transactions",
        ],
    )
    sections = ["DETECTED SUBSCRIPTIONS", table.to_string(index=False)]
    if alert_messages:
        sections.extend(["", "PREDICTIVE ALERTS", *alert_messages])
    else:
        sections.extend(["", "PREDICTIVE ALERTS", "No upcoming charges within 5 days."])
    return "\n".join(sections)
