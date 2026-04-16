"""
ML anomaly detection using scikit-learn IsolationForest.
Operates on Usage_Log rows: [cpu_usage, memory_usage, storage_used].
"""
import numpy as np
from sklearn.ensemble import IsolationForest
import db


def detect_anomalies() -> list:
    """
    Run IsolationForest per resource (needs >= 3 logs).
    Returns list of dicts: {log_id, resource_id, is_anomaly, anomaly_score, reason}
    """
    logs = db.query(
        "SELECT log_id, resource_id, cpu_usage, memory_usage, storage_used FROM Usage_Log ORDER BY resource_id, log_id"
    )
    if not logs:
        return []

    # Group by resource_id
    groups: dict = {}
    for row in logs:
        rid = row["resource_id"]
        groups.setdefault(rid, []).append(row)

    results = []
    for rid, rows in groups.items():
        if len(rows) < 3:
            # Not enough data — mark as unknown
            for row in rows:
                results.append({
                    "log_id": row["log_id"],
                    "resource_id": rid,
                    "is_anomaly": False,
                    "anomaly_score": 0.0,
                    "reason": "Insufficient data for anomaly detection (need ≥ 3 logs)",
                })
            continue

        X = np.array([[float(r["cpu_usage"]), float(r["memory_usage"]), float(r["storage_used"])] for r in rows])
        contamination = min(0.2, max(0.05, 1 / len(rows)))
        model = IsolationForest(contamination=contamination, random_state=42)
        preds = model.fit_predict(X)           # -1 = anomaly, 1 = normal
        scores = model.score_samples(X)        # more negative = more anomalous

        for row, pred, score in zip(rows, preds, scores):
            is_anomaly = int(pred) == -1
            reason = ""
            if is_anomaly:
                # Build a human-readable reason
                idx = rows.index(row)
                reasons = []
                mean_cpu = float(np.mean(X[:, 0]))
                mean_mem = float(np.mean(X[:, 1]))
                mean_sto = float(np.mean(X[:, 2]))
                if abs(float(row["cpu_usage"]) - mean_cpu) > 0.5 * mean_cpu:
                    reasons.append(f"CPU spike ({row['cpu_usage']}% vs avg {mean_cpu:.1f}%)")
                if abs(float(row["memory_usage"]) - mean_mem) > 0.5 * mean_mem:
                    reasons.append(f"Memory spike ({row['memory_usage']}% vs avg {mean_mem:.1f}%)")
                if abs(float(row["storage_used"]) - mean_sto) > 0.5 * mean_sto:
                    reasons.append(f"Storage spike ({row['storage_used']} GB vs avg {mean_sto:.1f} GB)")
                reason = "; ".join(reasons) if reasons else "Unusual combination of metrics"

            results.append({
                "log_id": row["log_id"],
                "resource_id": rid,
                "is_anomaly": is_anomaly,
                "anomaly_score": round(float(score), 4),
                "reason": reason,
            })

    return results
