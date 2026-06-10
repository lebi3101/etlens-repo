import pandas as pd
import sqlite3

conn = sqlite3.connect("database/etl_docs.db")

df = pd.read_csv("data/orders.csv")
df = df[df["amount"] > 1000]
df = df.rename(columns={"amt": "amount", "cust": "customer_id"})
df["processed"] = True
df.to_sql("big_orders", conn, if_exists="replace", index=False)

conn.close()