---
name: sql_data_report
description: "Use this skill when the user wants to generate a data analysis report based on database queries. This includes: generating SQL from natural language questions, executing queries, analyzing results, creating visualizations, and producing formatted reports (Markdown, PDF, or Word). Trigger when user asks to 'analyze data', 'generate report', 'query database', 'create dashboard', or similar requests that involve retrieving and summarizing data from a database."
metadata:
  builtin_skill_version: "1.0"
---

> **Important:** All `scripts/` paths are relative to this skill directory.
> Run with: `cd {this_skill_dir} && python scripts/...`
> Or use the `cwd` parameter of `execute_shell_command`.

# SQL Data Report Skill

This skill generates comprehensive data analysis reports by combining:
1. SQL generation from natural language
2. Query execution
3. Data analysis and insights
4. Chart generation
5. Report creation (Markdown/PDF)

## Available Tools

### SQL Tools
- **generate_sql**: Convert natural language questions to SQL queries
  ```python
  from agentscope import ToolResponse
  # Usage via Agent toolkit
  ```
- **execute_sql**: Execute SQL queries on MySQL or Doris databases
  ```python
  result = execute_sql("SELECT * FROM orders LIMIT 10", database="mysql")
  ```

### Data Analysis Tools
- **analyze_data**: Perform statistical analysis
  - analysis_type: "summary", "trend", "comparison", "outlier", "insights"

### Visualization Tools
- **generate_chart**: Create charts from data
  - chart_type: "line", "bar", "pie", "scatter"

## Report Generation Workflow

### Step 1: Generate SQL
```python
# Use generate_sql tool to create SQL from user question
sql_result = generate_sql(
    question="查看过去一个月每天的销售总额",
    database="mysql",
    require_approval=True
)
# Extract SQL from result
```

### Step 2: Execute Query
```python
# Use execute_sql tool to run the generated query
data_result = execute_sql(sql, database="mysql")
# Get structured data for analysis
```

### Step 3: Analyze Data
```python
# Use analyze_data tool for insights
analysis_result = analyze_data(
    data=query_result_json,
    analysis_type="summary"  # or "trend", "comparison", etc.
)
```

### Step 4: Generate Charts
```python
# Use generate_chart tool to create visualizations
chart_result = generate_chart(
    data=query_result_json,
    chart_type="line",  # or "bar", "pie", "scatter"
    title="月度销售趋势"
)
```

### Step 5: Create Report
```python
# Use report generation scripts
from scripts.generate_markdown import generate_markdown_report
from scripts.generate_pdf import generate_pdf_report

# Generate Markdown report
report = generate_markdown_report(
    title="销售数据分析报告",
    summary=analysis_summary,
    insights=key_insights,
    charts=[chart_path1, chart_path2],
    conclusions=conclusions
)

# Or generate PDF report
pdf_path = generate_pdf_report(
    title="销售数据分析报告",
    summary=analysis_summary,
    insights=key_insights,
    charts=[chart_path1, chart_path2],
    conclusions=conclusions
)
```

## Report Template

```markdown
# {报告标题}
生成时间：{timestamp}

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
```

## Best Practices

1. **Always validate SQL**: Review generated SQL before execution
2. **Use appropriate chart types**:
   - Line charts for time series trends
   - Bar charts for category comparisons
   - Pie charts for proportion analysis
   - Scatter plots for correlation analysis
3. **Include data quality notes**: Mention any data limitations or assumptions
4. **Provide actionable insights**: Focus on findings that drive decisions

## Prerequisites

- **pandas**: Data manipulation and analysis
- **matplotlib**: Chart generation
- **reportlab** (optional): PDF report generation
- **pymysql**: Database connectivity
- Database credentials configured in `.env` file

## Database Configuration

Configure database connections in `.env`:

```env
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database

# Doris (optional)
DORIS_HOST=localhost
DORIS_PORT=9030
DORIS_USER=root
DORIS_PASSWORD=your_password
DORIS_DATABASE=your_database
```
