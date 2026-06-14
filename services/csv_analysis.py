import pandas as pd

df = pd.read_csv(
    r"C:\Users\Shruti Somvanshi\Downloads\Expenses Export.csv"
)

print("\n===== ROWS WITH MISSING DATA =====")
print(df[df.isnull().any(axis=1)])

print("\n===== NON STANDARD NAMES =====")
print(df["paid_by"].unique())

print("\n===== NEGATIVE OR ZERO AMOUNTS =====")

for idx, row in df.iterrows():
    try:
        amount = float(str(row["amount"]).replace(",", ""))

        if amount <= 0:
            print(idx, row["description"], amount)

    except Exception as e:
        print(f"Error parsing row {idx}: {e}")

print("\n===== USD EXPENSES =====")
print(df[df["currency"] == "USD"])

print("\n===== NON-EQUAL SPLITS =====")
print(
    df[df["split_type"] != "equal"][
        [
            "description",
            "split_type",
            "split_details"
        ]
    ]
)