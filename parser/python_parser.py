import ast
import os
import re

def parse_python_etl(filepath):
    with open(filepath, "r") as f:
        source = f.read()

    tree = ast.parse(source)
    sources = []
    targets = []
    transformations = []

    # ── 1. CONFIG DICT DETECTION ─────────────────────────
    # Handles PIPELINE_CONFIG style — finds string values
    # inside dicts that look like file paths
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                # Direct string values that are file paths
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    val = value.value
                    if any(val.endswith(ext) for ext in
                           [".csv", ".sql", ".json", ".xlsx", ".parquet"]):
                        sources.append(val)
                # Nested dict values (like sources: {name: path})
                if isinstance(value, ast.Dict):
                    for v in value.values:
                        if isinstance(v, ast.Constant) and isinstance(v.value, str):
                            val = v.value
                            if any(val.endswith(ext) for ext in
                                   [".csv", ".sql", ".json",
                                    ".xlsx", ".parquet"]):
                                sources.append(val)

    # ── 2. FUNCTION CALLS ─────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr

                # SOURCES — direct string argument
                if method in ["read_csv", "read_sql", "read_excel",
                               "read_json", "read_parquet"]:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            sources.append(arg.value)
                    # Also check keyword arguments
                    for kw in node.keywords:
                        if kw.arg in ["filepath_or_buffer", "path", "path_or_buf"]:
                            if isinstance(kw.value, ast.Constant):
                                sources.append(kw.value.value)

                # TARGETS
                if method in ["to_sql", "to_csv", "to_excel", "to_parquet"]:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            targets.append(arg.value)
                    for kw in node.keywords:
                        if kw.arg in ["name", "path", "path_or_buf"]:
                            if isinstance(kw.value, ast.Constant):
                                targets.append(kw.value.value)

                # TRANSFORMATIONS
                if method in ["merge", "join", "groupby", "filter",
                               "rename", "drop", "fillna", "dropna",
                               "apply", "map", "pivot", "melt",
                               "sort_values", "drop_duplicates",
                               "copy", "agg", "aggregate",
                               "reset_index", "set_index",
                               "drop_duplicates", "explode"]:
                    transformations.append(method)

            # Handle sqlite3.connect("db.db") as target
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "connect":
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and \
                           isinstance(arg.value, str) and \
                           arg.value.endswith(".db"):
                            targets.append(arg.value)

    # ── 3. DECORATED FUNCTIONS ────────────────────────────
    # Handles @timer def extract_employees(): return pd.read_csv(...)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Attribute):
                        method = subnode.func.attr
                        if method in ["read_csv", "read_sql",
                                      "read_excel", "read_json"]:
                            for arg in subnode.args:
                                if isinstance(arg, ast.Constant):
                                    sources.append(arg.value)

    # ── 4. CLASS METHOD DETECTION ─────────────────────────
    # Handles class-based ETL like SalesETLPipeline
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in ast.walk(node):
                if isinstance(item, ast.Call):
                    if isinstance(item.func, ast.Attribute):
                        method = item.func.attr
                        if method in ["read_csv", "read_sql",
                                      "read_excel", "read_json"]:
                            for arg in item.args:
                                if isinstance(arg, ast.Constant):
                                    sources.append(arg.value)
                        if method in ["to_sql", "to_csv", "to_excel"]:
                            for arg in item.args:
                                if isinstance(arg, ast.Constant):
                                    targets.append(arg.value)

    # ── 5. FILTER CONDITIONS ──────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            transformations.append("filter/condition")

    # ── 6. NEW COLUMN ASSIGNMENTS ─────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    if isinstance(target.slice, ast.Constant):
                        transformations.append(
                            f"new column: {target.slice.value}"
                        )

    # ── 7. REGEX FALLBACK ─────────────────────────────────
    # Catches anything AST missed — reads raw source text
    csv_matches = re.findall(r'read_csv\(["\']([^"\']+)["\']\)', source)
    excel_matches = re.findall(r'read_excel\(["\']([^"\']+)["\']\)', source)
    json_matches = re.findall(r'read_json\(["\']([^"\']+)["\']\)', source)
    sql_matches = re.findall(r'read_sql\(["\']([^"\']+)["\']\)', source)
    tosql_matches = re.findall(r'to_sql\(["\']([^"\']+)["\']\)', source)
    tocsv_matches = re.findall(r'to_csv\(["\']([^"\']+)["\']\)', source)

    sources.extend(csv_matches + excel_matches +
                   json_matches + sql_matches)
    targets.extend(tosql_matches + tocsv_matches)

    # ── CLEAN AND RETURN ──────────────────────────────────
    # Remove empty strings and duplicates
    sources = list(set([s for s in sources if s and s.strip()]))
    targets = list(set([t for t in targets if t and t.strip()]))
    transformations = list(set(
        [t for t in transformations if t and t.strip()]
    ))

    return {
        "file": os.path.basename(filepath),
        "type": "python",
        "sources": sources,
        "targets": targets,
        "transformations": transformations
    }


if __name__ == "__main__":
    import sys
    files = [
        "etl_samples/sample_orders.py",
        "etl_samples/sample_hr.py",
    ]
    for f in files:
        if os.path.exists(f):
            result = parse_python_etl(f)
            print(f"\n{result['file']}:")
            print(f"  Sources: {result['sources']}")
            print(f"  Targets: {result['targets']}")
            print(f"  Transformations: {result['transformations']}")