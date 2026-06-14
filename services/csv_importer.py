import pandas as pd

from database.database import SessionLocal

from database.models import (
    ImportLog,
    Anomaly
)

from services.anomaly_detector import detect_anomalies


def import_csv(file_path):

    db = SessionLocal()

    try:

        df = pd.read_csv(file_path)

        total_rows = len(df)

        anomalies = detect_anomalies(df)

        imported_rows = total_rows

        # -----------------------
        # SAVE ANOMALIES
        # -----------------------

        for anomaly in anomalies:

            anomaly_record = Anomaly(
                row_number=anomaly.get("row_number"),
                anomaly_type=anomaly.get("type"),
                severity=anomaly.get("severity"),
                description=anomaly.get("description"),
                action_taken=anomaly.get("action"),
                status="PENDING"
            )

            db.add(anomaly_record)

        db.commit()

        # -----------------------
        # IMPORT LOG
        # -----------------------

        log = ImportLog(
            file_name=file_path.split("/")[-1],
            total_rows=total_rows,
            imported_rows=imported_rows,
            anomalies_found=len(anomalies)
        )

        db.add(log)
        db.commit()

        return {
            "success": True,
            "rows": total_rows,
            "imported_rows": imported_rows,
            "anomalies": anomalies
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

    finally:

        db.close()