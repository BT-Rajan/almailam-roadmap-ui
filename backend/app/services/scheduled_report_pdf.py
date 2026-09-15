"""Renders whichever report a ScheduledReport is configured for
(business_summary/financial_summary/project_status) into a PDF -- the
attachment scheduled_report_service.run_due_schedules emails out.

Deliberately its own small HTML->PDF template rather than reusing
pdf_render.render_agreement_pdf: that one is RTL/Arabic-first (see its
own docstring), built for a single merged legal document body. This is
a plain LTR/English tabular business report (metrics and status
breakdowns), so it gets its own compact template instead of forcing
those through the wrong shape. Both go through the same WeasyPrint
HTML->PDF engine (see that module's docstring for why WeasyPrint at
all, and the system-library dependency that implies).

Every section here is built from data report_service.py already
computes for the on-screen Reports dashboard/API (see api/reports.py) --
this module is only responsible for turning that same data into a
printable/emailable page, not for computing it a second way.
"""

from datetime import date, datetime, timedelta
import re

from sqlalchemy.orm import Session
from weasyprint import HTML

from app.core.exceptions import ValidationAppError
from app.models.project import Project
from app.models.scheduled_report import ScheduledReport
from app.services import company_service, report_service

DEFAULT_BRAND_COLOR = "#3995BE"
_HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{3}\Z|#[0-9A-Fa-f]{6}\Z")


def _safe_brand_color(value: str | None) -> str:
    """brand_color gets interpolated straight into a <style> block below,
    unescaped (it's meant to be a CSS color token, not text content), so
    anything not shaped like a real hex color -- most importantly
    anything containing '}' that could close the CSS rule early and
    inject arbitrary markup into an emailed PDF -- falls back to the
    default instead. CompanySettingsIn.brandColor validates this same
    shape at save time now, but this stays as a second check against
    whatever a row already had before that validation existed."""
    if value and _HEX_COLOR_RE.fullmatch(value):
        return value
    return DEFAULT_BRAND_COLOR


PERIOD_LABELS = {
    "last_7_days": "Last 7 Days",
    "last_30_days": "Last 30 Days",
    "this_month": "This Month",
    "last_month": "Last Month",
    "this_quarter": "This Quarter",
    "this_year": "This Year",
}


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_value(value) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _metric_rows(metrics: list[dict]) -> list[tuple[str, str]]:
    rows = []
    for metric in metrics:
        value_str = _format_value(metric.get("value"))
        unit = metric.get("unit")
        rows.append((metric["label"], f"{value_str} {unit}" if unit else value_str))
    return rows


def _chart_rows(items: list[dict]) -> list[tuple[str, str]]:
    return [(item["label"], str(item["value"])) for item in items] or [("No data recorded", "")]


def _period_bounds(period: str, today: date) -> tuple[date, date]:
    """The rolling window a period label maps to, computed relative to
    `today` (the run date) -- so the same schedule's "Last 30 Days"
    section keeps sliding forward every time it fires, rather than
    freezing on whatever dates existed when the schedule was created."""
    if period == "last_7_days":
        return today - timedelta(days=6), today
    if period == "last_30_days":
        return today - timedelta(days=29), today
    if period == "this_month":
        return today.replace(day=1), today
    if period == "last_month":
        last_month_end = today.replace(day=1) - timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end
    if period == "this_quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return date(today.year, quarter_start_month, 1), today
    if period == "this_year":
        return date(today.year, 1, 1), today
    raise ValidationAppError(f"Unknown report period: {period}.")


def _business_summary_sections(db: Session) -> tuple[str, list[dict]]:
    sections = [
        {"heading": "Key Metrics", "rows": _metric_rows(report_service.summary_metrics(db))},
        {"heading": "Projects by Status", "rows": _chart_rows(report_service.projects_by_status(db))},
        {"heading": "Tasks by Status", "rows": _chart_rows(report_service.tasks_by_status(db))},
        {"heading": "Documents by Status", "rows": _chart_rows(report_service.documents_by_status(db))},
        {"heading": "Permit Applications by Stage", "rows": _chart_rows(report_service.submissions_by_status(db))},
        {"heading": "Quotations by Status", "rows": _chart_rows(report_service.quotations_by_status(db))},
        {"heading": "Contracts by Status", "rows": _chart_rows(report_service.contracts_by_status(db))},
    ]
    return "Business Summary Report", sections


def _financial_summary_sections(db: Session, period: str | None) -> tuple[str, list[dict]]:
    period = period or "last_30_days"
    start_date, end_date = _period_bounds(period, date.today())
    summary = report_service.financial_period_summary(db, start_date, end_date)
    multi_currency = len(summary["byCurrency"]) > 1
    rows = [("Period", f"{summary['startDate']} to {summary['endDate']}")]
    for entry in summary["byCurrency"]:
        suffix = f" ({entry['currency']})" if multi_currency else ""
        rows.append((f"Payments Received{suffix}", f"{_format_value(entry['totalReceived'])} {entry['currency']}"))
        rows.append((f"Total Billed (fell due in period){suffix}", f"{_format_value(entry['totalDue'])} {entry['currency']}"))
        rows.append((f"Outstanding (unpaid, of what's billed){suffix}", f"{_format_value(entry['totalOutstanding'])} {entry['currency']}"))
        rows.append((f"Overdue (unpaid and past due){suffix}", f"{_format_value(entry['totalOverdue'])} {entry['currency']}"))
    rows.append(("Number of Payments", str(summary["paymentCount"])))
    title = f"Financial Summary Report \u2014 {PERIOD_LABELS.get(period, period)}"
    return title, [{"heading": "Financial Summary", "rows": rows}]


def _project_status_sections(db: Session, project_id: int | None) -> tuple[str, list[dict]]:
    # deleted_at IS NULL matches every other "does this project exist"
    # query in the app (see Project's own model comment) -- without it,
    # a schedule pointed at a project that's since been soft-deleted
    # would keep firing and emailing a report for a project the rest of
    # the app already treats as gone, despite this function's own error
    # message below saying otherwise.
    project = (
        db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
        if project_id
        else None
    )
    if project is None:
        raise ValidationAppError("The project configured for this scheduled report no longer exists.")
    sections_data = report_service.project_report(db, project)
    sections = [{"heading": section["title"], "rows": _metric_rows(section["metrics"])} for section in sections_data]
    title = f"Project Report \u2014 {project.project_no} ({project.project_name})"
    return title, sections


def _section_html(section: dict) -> str:
    rows_html = "".join(
        f'<tr><td class="label">{_escape_html(label)}</td><td class="value">{_escape_html(value)}</td></tr>'
        for label, value in section["rows"]
    )
    return f'<h2>{_escape_html(section["heading"])}</h2><table>{rows_html}</table>'


def _wrap_html(company_name: str, tagline: str, brand_color: str, title: str, sections: list[dict], run_at: datetime) -> str:
    body = "".join(_section_html(section) for section in sections)
    generated = run_at.strftime("%d %b %Y, %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: 'DejaVu Sans', Arial, sans-serif; color: #1a1a2e; font-size: 11pt; }}
  .company-name {{ font-size: 17pt; font-weight: 700; margin: 0; color: {brand_color}; }}
  .tagline {{ color: #666; font-size: 9pt; margin: 2px 0 18px; }}
  .report-title {{ font-size: 14pt; font-weight: 600; margin: 0 0 18px; border-bottom: 2px solid {brand_color}; padding-bottom: 8px; }}
  h2 {{ font-size: 11.5pt; margin: 18px 0 6px; color: {brand_color}; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 4px; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #eee; font-size: 10pt; }}
  td.label {{ color: #444; }}
  td.value {{ text-align: right; font-weight: 600; white-space: nowrap; }}
  .footer {{ margin-top: 28px; font-size: 8pt; color: #999; border-top: 1px solid #eee; padding-top: 8px; }}
</style>
</head>
<body>
  <p class="company-name">{_escape_html(company_name)}</p>
  <p class="tagline">{_escape_html(tagline)}</p>
  <p class="report-title">{_escape_html(title)}</p>
  {body}
  <p class="footer">Generated automatically by ServiceOS on {generated}.</p>
</body>
</html>"""


def render(db: Session, schedule: ScheduledReport, run_at: datetime) -> tuple[bytes, str, str]:
    """Returns (pdf_bytes, attachment_filename, report_title) -- the
    title doubles as the email subject's default source (see
    scheduled_report_service._build_email)."""
    if schedule.report_type == "business_summary":
        title, sections = _business_summary_sections(db)
    elif schedule.report_type == "financial_summary":
        title, sections = _financial_summary_sections(db, schedule.period)
    elif schedule.report_type == "project_status":
        title, sections = _project_status_sections(db, schedule.project_id)
    else:
        raise ValidationAppError(f"Unknown report type: {schedule.report_type}.")

    company = company_service.get_settings(db)
    html = _wrap_html(company.company_name, company.tagline, _safe_brand_color(company.brand_color), title, sections, run_at)
    pdf_bytes = HTML(string=html).write_pdf()
    filename = f"{schedule.report_type}-{run_at.strftime('%Y%m%d-%H%M')}.pdf"
    return pdf_bytes, filename, title
