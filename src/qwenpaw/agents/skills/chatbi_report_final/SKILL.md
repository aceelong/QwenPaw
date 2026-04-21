---
name: chatbi_report_final
description: "Use this skill when the user wants to generate a comprehensive data analysis report. This includes: creating Markdown/PDF reports with data overview, key insights, trend analysis, charts, and conclusions. Triggers: user asks for '生成报告', '输出报告', '分析报告'."
metadata:
  builtin_skill_version: "1.0"
---

# ChatBI Report Generation Skill

This skill generates comprehensive data analysis reports (Markdown/PDF) from query results and charts.

## Tools

### generate_markdown_report

From `src/qwenpaw/agents/skills/chatbi_report/scripts/generate_markdown.py`

```python
from scripts.generate_markdown import generate_markdown_report

report = generate_markdown_report(
    title="报告标题",
    summary="数据概览",
    insights="关键发现",
    trend_analysis="趋势分析",
    charts=["图表路径1", "图表路径2"],
    conclusions="结论与建议",
    output_path="输出路径.md"
)
```

### generate_pdf_report (Optional)

```python
from scripts.generate_markdown import generate_pdf_report

pdf_path = generate_pdf_report(
    title="报告标题",
    summary="数据概览",
    insights="关键发现",
    charts=["图表路径1"],
    conclusions="结论与建议",
    output_path="输出路径.pdf"
)
```

## Report Template

```markdown
# {报告标题}
生成时间：{timestamp}

---

## 数据概览
{summary_stats}

## 关键发现
{key_insights}

## 趋势分析
{trend_analysis}

## 图表
{chart_images}

## 结论与建议
{conclusions}

---
*报告生成时间: {timestamp}*
```

## Report Sections

### 1. 数据概览 (Data Overview)
- Total records count
- Key metrics summary (total, average, max, min)
- Date range of data
- Data source info

### 2. 关键发现 (Key Insights)
- Top performers identification
- Significant changes (YoY, MoM)
- Outliers or anomalies
- Key patterns observed

### 3. 趋势分析 (Trend Analysis)
- Time series trends
- Period-over-period comparisons
- Growth rates
- Seasonal patterns

### 4. 图表 (Charts)
- Include relevant visualizations
- Reference chart file paths

### 5. 结论与建议 (Conclusions)
- Summary of findings
- Recommendations based on data
- Action items if applicable

## Usage Example

### Step 1: Prepare Data
After executing SQL and generating charts, gather:
- Query results (for summary stats)
- Chart paths
- Key metrics from analysis

### Step 2: Generate Report

```python
# Example: Revenue analysis report

# Calculate summary
total_revenue = sum([r["营业收入(万)"] for r in data])
avg_revenue = total_revenue / len(data)
top_city = max(data, key=lambda x: x["营业收入(万)"])

summary = f"""
- 数据时间: 2025年12月
- 统计维度: 地市
- 总记录数: {len(data)}
- 全省营收总计: {total_revenue:.2f} 万
- 平均营收: {avg_revenue:.2f} 万
- 最高营收: {top_city["地市名称"]} ({top_city["营业收入(万)"]} 万)
"""

insights = f"""
- 广州市营收最高，达 {top_city["营业收入(万)"]} 万
- 前三名城市营收占全省约 60%
- 同比增长率: {top_city.get("同比增长率", "N/A")}
"""

conclusions = """
1. 广州、深圳、佛山为营收前三名
2. 建议关注营收增速较低的地市
3. 可考虑优化资源配置向高增长区域倾斜
"""

# Generate report
report = generate_markdown_report(
    title="广电广东2025年12月营收分析报告",
    summary=summary,
    insights=insights,
    trend_analysis="",
    charts=["/path/to/revenue_chart.png"],
    conclusions=conclusions,
    output_path=".qwenpaw/reports/revenue_report.md"
)
```

## Output

The generated report includes:
- Clean Markdown formatting
- Proper headings and sections
- Embedded chart images (if paths valid)
- Timestamp
- Summary statistics

## Prerequisites

- **pandas**: Data manipulation
- **reportlab** (for PDF): Optional, if not available only Markdown is generated

## Best Practices

1. **Include actionable insights**: Focus on findings that drive decisions
2. **Use visual aids**: Include relevant charts
3. **Provide context**: Include date range, dimension info
4. **Be concise**: Use bullet points for readability
5. **Add recommendations**: Conclude with actionable suggestions