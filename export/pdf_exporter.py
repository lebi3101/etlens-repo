import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class ETLReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_fill_color(52, 73, 94)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "ETL Script Documentation Report", ln=True, fill=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(189, 195, 199)
        self.set_text_color(0)
        self.cell(0, 9, title, ln=True, fill=True)
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Arial", size=10)
        self.set_text_color(0)
        # Clean non-latin characters
        clean = text.encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 7, clean)
        self.ln(2)

    def add_script_section(self, filename, parsed, documentation, business_purpose, impact):
        self.add_page()

        # File header
        self.set_font("Arial", "B", 13)
        self.set_text_color(52, 73, 94)
        self.cell(0, 10, f"Script: {filename}", ln=True)
        self.ln(2)

        # Parsed info
        self.section_title("Parsed Information")
        self.body_text(
            f"Type: {parsed.get('type', 'N/A').upper()}\n"
            f"Sources: {', '.join(parsed.get('sources', [])) or 'N/A'}\n"
            f"Targets: {', '.join(parsed.get('targets', [])) or 'N/A'}\n"
            f"Transformations: {', '.join(parsed.get('transformations', [])) or 'N/A'}"
        )

        # Documentation
        self.section_title("Auto-Generated Documentation")
        self.body_text(documentation or "Not generated.")

        # Business purpose
        self.section_title("Business Purpose")
        self.body_text(business_purpose or "Not generated.")

        # Impact analysis
        self.section_title("Impact Analysis")
        self.body_text(
            f"Risk Level: {impact.get('risk_level', 'N/A')}\n"
            f"Reason: {impact.get('risk_reason', 'N/A')}\n"
            f"Depends on: {impact.get('upstream_dependencies') or 'None'}\n"
            f"Writes to: {impact.get('direct_outputs') or 'None'}\n"
            f"Affected scripts if fails: {impact.get('affected_scripts') or 'None'}"
        )


def generate_pdf_report(
    all_parsed: list,
    docs: dict,
    business: dict,
    impact_reports: dict,
    output_filename: str = "etl_report.pdf"
) -> str:
    """
    Generates a full PDF report for all ETL scripts.

    Returns:
        Path to the saved PDF file
    """
    pdf = ETLReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for parsed in all_parsed:
        fname = parsed["file"]
        pdf.add_script_section(
            filename=fname,
            parsed=parsed,
            documentation=docs.get(fname, "Not generated."),
            business_purpose=business.get(fname, "Not generated."),
            impact=impact_reports.get(fname, {})
        )

    output_path = os.path.join(REPORTS_DIR, output_filename)
    pdf.output(output_path)
    print(f"  PDF saved: {output_path}")
    return output_path


if __name__ == "__main__":
    from parser.python_parser import parse_python_etl
    from parser.sql_parser import parse_sql_etl
    from impact.impact_analysis import analyze_all_scripts

    print("Testing PDF Export...\n")

    parsed_orders = parse_python_etl("etl_samples/sample_orders.py")
    parsed_hr = parse_python_etl("etl_samples/sample_hr.py")
    parsed_sales = parse_sql_etl("etl_samples/sample_sales.sql")
    all_parsed = [parsed_orders, parsed_hr, parsed_sales]

    # Use hardcoded docs to avoid LLM timeout
    docs = {
        "sample_orders.py": "Reads orders CSV, filters high-value orders above 1000, saves to big_orders table.",
        "sample_hr.py": "Merges employee and attendance data, calculates bonus, saves to hr_report table.",
        "sample_sales.sql": "Joins orders and customers, summarizes total sales per customer into sales_summary."
    }
    business = {
        "sample_orders.py": "Helps the sales team track high-value orders for priority processing.",
        "sample_hr.py": "Enables HR to calculate bonuses and monitor attendance automatically.",
        "sample_sales.sql": "Provides sales leadership with customer-level revenue summaries."
    }

    impact_reports, _ = analyze_all_scripts(all_parsed)

    path = generate_pdf_report(all_parsed, docs, business, impact_reports)
    print(f"✅ PDF report generated: {path}")