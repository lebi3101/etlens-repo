# sample_inventory.py

import pandas as pd
import sqlite3


def determine_priority(stock_quantity):
    if stock_quantity < 20:
        return "URGENT"
    elif stock_quantity < 50:
        return "NORMAL"
    return None


def main():
    # Read CSV files
    inventory_df = pd.read_csv("data/inventory.csv")
    warehouse_df = pd.read_csv("data/warehouse.csv")

    # Merge on product_id
    merged_df = pd.merge(
        inventory_df,
        warehouse_df,
        on="product_id",
        how="inner"
    )

    # Filter low stock items
    low_stock_df = merged_df[merged_df["stock_quantity"] < 50].copy()

    # Create reorder_priority column
    low_stock_df["reorder_priority"] = low_stock_df[
        "stock_quantity"
    ].apply(determine_priority)

    # Save to SQLite
    conn = sqlite3.connect("inventory.db")

    low_stock_df.to_sql(
        "low_stock_report",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print(
        f"Successfully loaded {len(low_stock_df)} records "
        "into low_stock_report table."
    )


if __name__ == "__main__":
    main()