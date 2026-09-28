import pandas as pd
from pathlib import Path

DATA=Path(__file__).parents[1]/"data"/"cpgrams_snapshot.csv"
df=pd.read_csv(DATA)

age_cols=["pending_0_60","pending_61_180","pending_181_365","pending_over_365"]
df["pending_check"]=df[age_cols].sum(axis=1)
df["pending_match"]=df["pending_check"].eq(df["pending_total"])
df["disposal_rate"]=df["disposed"].div(df["received"].replace(0,pd.NA)).mul(100)
df["pressure_index"]=(df["received"]+df["pending_total"])/df["disposed"].clip(lower=1)

print("rows:",len(df))
print("pending validation:",df["pending_match"].all())
print("\nTop pending workload:")
print(df.nlargest(10,"pending_total")[["state_ut","pending_total","disposal_rate"]].to_string(index=False))
