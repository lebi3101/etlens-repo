import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML
import os

def parse_sql_etl(filepath):
    with open(filepath, "r") as f:
        source = f.read()

    parsed = sqlparse.parse(source)[0]

    sources = []
    targets = []
    transformations = []

    # Get all tokens flattened
    tokens = list(parsed.flatten())
    token_values = [t.value.strip() for t in tokens]

    # Find target — INSERT INTO tablename
    for i, val in enumerate(token_values):
        if val.upper() == "INTO":
            # Skip whitespace tokens
            for j in range(i + 1, len(token_values)):
                if token_values[j].strip():
                    targets.append(token_values[j].strip())
                    break

    # Find sources — FROM and JOIN tablename
    for i, val in enumerate(token_values):
        if val.upper() in ["FROM", "JOIN"]:
            for j in range(i + 1, len(token_values)):
                if token_values[j].strip():
                    # Get the base table name without alias
                    table = token_values[j].strip().split()[0]
                    if table.upper() not in ["SELECT", "WHERE", "ON"]:
                        sources.append(table)
                    break

    # Find transformations
    keywords = ["JOIN", "WHERE", "GROUP", "HAVING",
                "ORDER", "SUM", "COUNT", "AVG", "MAX", "MIN"]
    for val in token_values:
        if val.upper() in keywords:
            transformations.append(val.lower())

    return {
        "file": os.path.basename(filepath),
        "type": "sql",
        "sources": list(set(filter(None, sources))),
        "targets": list(set(filter(None, targets))),
        "transformations": list(set(transformations))
    }

if __name__ == "__main__":
    result = parse_sql_etl("etl_samples/sample_sales.sql")
    print(result)