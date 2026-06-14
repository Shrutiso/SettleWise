import pandas as pd

from anomaly_detector import detect_anomalies

df = pd.read_csv(
    r"C:\Users\Shruti Somvanshi\Downloads\Expenses Export.csv"
)

results = detect_anomalies(df)

print("\n===== ANOMALIES =====\n")

for item in results:
    print(item)

print(
    f"\nTotal anomalies found: {len(results)}"
)