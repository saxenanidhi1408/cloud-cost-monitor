import pandas as pd
import numpy as np

r = np.random.default_rng(1)
d = pd.date_range("2026-10-01", periods=40)
rows = [(x, s, r.uniform(5, 30)) for x in d for s in ["EC2", "S3", "RDS", "VPC"]]
df = pd.DataFrame(rows, columns=["date", "service", "cost"])

df.loc[(df.date == d[25]) & (df.service == "RDS"), "cost"] += 250

df.to_csv("test_billing.csv", index=False)
print("done")