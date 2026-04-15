# -*- coding: utf-8 -*-
"""Markdown report generation for SQL data reports."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Try to import reportlab for PDF support
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_markdown_report(
    title: str,
    summary: str,
    insights: Optional[str] = None,
    trend_analysis: Optional[str] = None,
    charts: Optional[List[str]] = None,
    conclusions: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """Generate a Markdown report from analysis results.

    Args:
        title: Report title
        summary: Data summary section
        insights: Key insights section
        trend_analysis: Trend analysis section
        charts: List of chart image paths to include
        conclusions: Conclusions and recommendations
        output_path: Optional path to save the report

    Returns:
        Generated Markdown report content
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# {title}",
        f"\n**生成时间**: {timestamp}\n",
        "---",
        "\n## 数据概览\n",
        summary,
    ]

    if insights:
        lines.extend(["\n## 关键发现\n", insights])

    if trend_analysis:
        lines.extend(["\n## 趋势分析\n", trend_analysis])

    if charts:
        lines.extend(["\n## 图表\n"])
        for i, chart_path in enumerate(charts, 1):
            if os.path.exists(chart_path):
                chart_filename = os.path.basename(chart_path)
                lines.append(f"\n### 图表 {i}\n")
                lines.append(f"![Chart {i}]({chart_path})\n")

    if conclusions:
        lines.extend(["\n## 结论与建议\n", conclusions])

    lines.append("\n---\n")
    lines.append(f"\n*报告生成时间: {timestamp}*\n")

    report_content = "\n".join(lines)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)

    return report_content


def generate_pdf_report(
    title: str,
    summary: str,
    insights: Optional[str] = None,
    trend_analysis: Optional[str] = None,
    charts: Optional[List[str]] = None,
    conclusions: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Optional[str]:
    """Generate a PDF report from analysis results.

    Args:
        title: Report title
        summary: Data summary section
        insights: Key insights section
        trend_analysis: Trend analysis section
        charts: List of chart image paths to include
        conclusions: Conclusions and recommendations
        output_path: Optional path to save the report

    Returns:
        Path to generated PDF file or None if reportlab is not available
    """
    if not REPORTLAB_AVAILABLE:
        print("Warning: reportlab not available, PDF generation disabled")
        return None

    if not output_path:
        from ....constant import WORKING_DIR

        output_dir = Path(WORKING_DIR) / ".qwenpaw" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Timestamp
    timestamp_style = styles["Normal"]
    timestamp_style.alignment = TA_CENTER
    story.append(
        Paragraph(
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            timestamp_style,
        )
    )
    story.append(Spacer(1, 0.5 * inch))

    # Summary
    heading_style = styles["Heading2"]
    body_style = styles["Normal"]

    story.append(Paragraph("数据概览", heading_style))
    story.append(Paragraph(summary.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 0.3 * inch))

    # Insights
    if insights:
        story.append(Paragraph("关键发现", heading_style))
        story.append(Paragraph(insights.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 0.3 * inch))

    # Trend analysis
    if trend_analysis:
        story.append(Paragraph("趋势分析", heading_style))
        story.append(Paragraph(trend_analysis.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 0.3 * inch))

    # Charts
    if charts:
        story.append(Paragraph("图表", heading_style))
        for chart_path in charts:
            if os.path.exists(chart_path):
                img = Image(chart_path, width=5 * inch, height=3 * inch)
                story.append(img)
                story.append(Spacer(1, 0.2 * inch))

    # Conclusions
    if conclusions:
        story.append(Paragraph("结论与建议", heading_style))
        story.append(Paragraph(conclusions.replace("\n", "<br/>"), body_style))

    doc.build(story)
    return str(output_path)


if __name__ == "__main__":
    # Test the report generation
    sample_report = generate_markdown_report(
        title="销售数据分析报告",
        summary="- 总记录数: 1,000\n- 总销售额: ¥500,000",
        insights="- 销售额呈上升趋势\n- 周末销售最高",
        conclusions="- 建议增加周末库存",
        output_path=".qwenpaw/test_report.md",
    )
    print("Markdown report generated:")
    print(sample_report)
