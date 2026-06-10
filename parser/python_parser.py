import ast
import os

def parse_python_etl(filepath):
    with open(filepath, "r") as f:
        source = f.read()
    tree = ast.parse(source)
    sources = []
    targets = []
    transformations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr

                # SOURCES
                if method in ["read_csv", "read_sql", "read_excel", "read_json"]:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            sources.append(arg.value)

                # TARGETS
                if method in ["to_sql", "to_csv", "to_excel"]:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            targets.append(arg.value)

                # TRANSFORMATIONS
                if method in ["merge", "join", "groupby", "filter",
                               "rename", "drop", "fillna", "dropna",
                               "apply", "map", "pivot", "melt",
                               "sort_values", "drop_duplicates", "copy"]:
                    transformations.append(method)

        # Filter conditions
        if isinstance(node, ast.Compare):
            transformations.append("filter/condition")

        # New column assignments
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    if isinstance(target.slice, ast.Constant):
                        transformations.append(f"new column: {target.slice.value}")

    return {
        "file": os.path.basename(filepath),
        "type": "python",
        "sources": list(set(sources)),
        "targets": list(set(targets)),
        "transformations": list(set(transformations))
    }

if __name__ == "__main__":
    result = parse_python_etl("etl_samples/sample_orders.py")
    print("Orders:", result)
    result2 = parse_python_etl("etl_samples/sample_hr.py")
    print("HR:", result2)