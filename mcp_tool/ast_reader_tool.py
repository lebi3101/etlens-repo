import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.tools import BaseTool
from parser.python_parser import parse_python_etl
from parser.sql_parser import parse_sql_etl
from pydantic import BaseModel, Field
from typing import Type
import json


# Input schema for the tool
class ETLFileInput(BaseModel):
    filepath: str = Field(
        description="The full path to the ETL file to be read and parsed"
    )


# The actual MCP Tool
class ASTReaderTool(BaseTool):
    name: str = "ast_etl_reader"
    description: str = """
    Use this tool to read and parse any ETL script file.
    Supports both Python (.py) and SQL (.sql) files.
    Input should be the full file path.
    Returns extracted sources, targets, and transformations from the ETL file.
    """
    args_schema: Type[BaseModel] = ETLFileInput

    def _run(self, filepath: str) -> str:
        try:
            if not os.path.exists(filepath):
                return json.dumps({
                    "error": f"File not found: {filepath}"
                })

            ext = os.path.splitext(filepath)[1].lower()

            if ext == ".py":
                result = parse_python_etl(filepath)
            elif ext == ".sql":
                result = parse_sql_etl(filepath)
            else:
                return json.dumps({
                    "error": f"Unsupported file type: {ext}. Only .py and .sql supported."
                })

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    def _arun(self, filepath: str):
        raise NotImplementedError("Async not supported")


# Test the tool directly
if __name__ == "__main__":
    tool = ASTReaderTool()

    print("Testing with Python ETL file...")
    result = tool._run("etl_samples/sample_orders.py")
    print(result)

    print("\nTesting with SQL ETL file...")
    result = tool._run("etl_samples/sample_sales.sql")
    print(result)

    print("\nTesting with invalid file...")
    result = tool._run("etl_samples/nonexistent.py")
    print(result)