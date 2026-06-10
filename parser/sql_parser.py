import sqlparse
import os
import re

def parse_sql_etl(filepath):
    with open(filepath, "r") as f:
        source = f.read()

    sources = []
    targets = []
    transformations = []

    # ── 1. TARGETS ────────────────────────────────────────
    # Handles:
    # INSERT INTO tablename
    # CREATE TABLE tablename AS
    # CREATE TABLE IF NOT EXISTS tablename

    # INSERT INTO
    insert_matches = re.findall(
        r'INSERT\s+INTO\s+(\w+)', source, re.IGNORECASE
    )
    targets.extend(insert_matches)

    # CREATE TABLE ... AS SELECT (target is the created table)
    create_matches = re.findall(
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
        source, re.IGNORECASE
    )
    targets.extend(create_matches)

    # ── 2. SOURCES ────────────────────────────────────────
    # Handles FROM, JOIN, inside CTEs and subqueries

    # All FROM clauses
    from_matches = re.findall(
        r'\bFROM\s+(\w+)', source, re.IGNORECASE
    )
    sources.extend(from_matches)

    # All JOIN clauses
    join_matches = re.findall(
        r'\bJOIN\s+(\w+)', source, re.IGNORECASE
    )
    sources.extend(join_matches)

    # ── 3. REMOVE STAGING TABLES FROM SOURCES ─────────────
    # Staging tables created in same script should not be
    # listed as external sources
    internal_tables = set([t.lower() for t in targets])

    # Also remove CTE names — they are not real sources
    cte_names = re.findall(
        r'WITH\s+(\w+)\s+AS\s*\(', source, re.IGNORECASE
    )
    # Find all CTE block names
    all_cte_names = re.findall(
        r'(\w+)\s+AS\s*\(', source, re.IGNORECASE
    )
    internal_tables.update([c.lower() for c in cte_names])
    internal_tables.update([c.lower() for c in all_cte_names])

    # Filter sources — keep only real external sources
    sources = [
        s for s in sources
        if s.lower() not in internal_tables
        and s.upper() not in [
            "SELECT", "WHERE", "ON", "SET",
            "NULL", "NOT", "EXISTS"
        ]
        and not s.isdigit()
    ]

    # ── 4. TRANSFORMATIONS ────────────────────────────────
    keywords = {
        "JOIN": "join",
        "LEFT JOIN": "left join",
        "WHERE": "filter/condition",
        "GROUP BY": "group by",
        "HAVING": "having",
        "ORDER BY": "order by",
        "SUM": "aggregation: sum",
        "COUNT": "aggregation: count",
        "AVG": "aggregation: avg",
        "MAX": "aggregation: max",
        "MIN": "aggregation: min",
        "CASE": "case/conditional",
        "COALESCE": "null handling",
        "NTILE": "window function",
        "ROW_NUMBER": "window function",
        "RANK": "window function",
        "OVER": "window function",
        "PARTITION BY": "partition",
        "DISTINCT": "deduplication",
        "UPPER": "string transform",
        "LOWER": "string transform",
        "TRIM": "string transform",
        "ROUND": "numeric transform",
        "CAST": "type casting",
        "WITH": "CTE/subquery",
    }

    source_upper = source.upper()
    for keyword, label in keywords.items():
        if keyword in source_upper:
            transformations.append(label)

    # ── CLEAN AND RETURN ──────────────────────────────────
    sources = list(set([s.strip() for s in sources if s.strip()]))
    targets = list(set([t.strip() for t in targets if t.strip()]))
    transformations = list(set(transformations))

    return {
        "file": os.path.basename(filepath),
        "type": "sql",
        "sources": sources,
        "targets": targets,
        "transformations": transformations
    }


if __name__ == "__main__":
    files = [
        "etl_samples/sample_sales.sql",
    ]
    for f in files:
        if os.path.exists(f):
            result = parse_sql_etl(f)
            print(f"\n{result['file']}:")
            print(f"  Sources: {result['sources']}")
            print(f"  Targets: {result['targets']}")
            print(f"  Transformations: {result['transformations']}")