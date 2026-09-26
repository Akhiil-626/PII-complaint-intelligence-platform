import pandas as pd
df = pd.read_csv("data/processed/complaints_small.csv")
print(df.groupby("Product")["Issue"].nunique())
print(df["Issue"].value_counts().head(20))