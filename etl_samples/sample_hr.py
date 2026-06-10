import pandas as pd
import sqlite3

conn = sqlite3.connect("database/etl_docs.db")

employees = pd.read_csv("data/employees.csv")
attendance = pd.read_csv("data/attendance.csv")

merged = pd.merge(employees, attendance, on="emp_id")
merged = merged[merged["days_present"] >= 20]
merged["bonus"] = merged["salary"] * 0.10

merged.to_sql("hr_report", conn, if_exists="replace", index=False)
conn.close()