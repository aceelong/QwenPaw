---
name: chatbi_report
description: "Use this skill when the user asks about business data queries for the Guangdong Broadcasting Network (广电广东) and wants a complete data analysis report. This provides the workflow overview for chaining three sub-skills together. Triggers: any mention of '营收', '用户数', '各分公司', '全省', combined with '报告', '分析', '图表'."
metadata:
  builtin_skill_version: "1.0"
---

# ChatBI Report Skill (工作流总览)

This skill provides the complete data analysis workflow by orchestrating three specialized sub-skills:

## Workflow Overview

```
┌─────────────────┐
│   用户问题       │
│  (营收/用户数)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│  chatbi_query   │ -> │ chatbi_chart    │
│  (查询数据)     │    │  (生成图表)      │
└─────────────────┘    └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ chatbi_report_final│
                        │  (生成报告)      │
                        └─────────────────┘
```

## 三个子技能

### 1. [chatbi_query](chatbi_query/SKILL.md)
- **功能**: 将自然语言转换为 SQL 并执行查询
- **表**: `ai_ads.ads_chatbi_summary_sta_level`
- **工具**: `execute_sql` from `src/qwenpaw/agents/tools/sql_execute.py`
- **触发**: 用户询问营收、用户数、排名等业务数据
- **输出**: 格式化查询结果

### 2. [chatbi_chart](chatbi_chart/SKILL.md)
- **功能**: 从数据生成可视化图表
- **工具**: `generate_chart` from `src/qwenpaw/agents/tools/generate_chart.py`
- **触发**: 用户要求"图表"、"可视化"、"画图"
- **支持**: bar, line, pie, scatter

### 3. [chatbi_report_final](chatbi_report_final/SKILL.md)
- **功能**: 生成完整的 Markdown/PDF 报告
- **工具**: `generate_markdown_report` from skill scripts
- **触发**: 用户要求"生成报告"、"输出报告"
- **输出**: 完整分析报告

## 使用场景

| 用户需求 | 使用技能 |
|---------|---------|
| 查询数据看结果 | chatbi_query |
| 需要图表可视化 | chatbi_query + chatbi_chart |
| 需要完整报告 | 完整流程: chatbi_query + chatbi_chart + chatbi_report_final |

## 完整工作流示例

### 用户输入
```
生成2025年各分公司营收排名报告，包含图表和分析
```

### 步骤1: 查询数据 (chatbi_query)
```sql
SELECT 年月, 地市名称, 指标名称, 指标值 / 10000 AS `营业收入(万)`,
       (指标值 / 考核目标值) * 100 AS `考核完成率`,
       ROW_NUMBER() OVER (ORDER BY 指标值 DESC) AS `排名`
FROM ai_ads.ads_chatbi_summary_sta_level
WHERE 统计维度 = '地市' AND 年月 = '202512'
AND 指标名称 IN ('营业收入(考核)','营业总收入','营业收入(含预出账)')
ORDER BY 指标值 DESC;
```
返回格式化查询结果

### 步骤2: 生成图表 (chatbi_chart)
```python
generate_chart(
    data=query_results,
    chart_type="bar",
    title="各分公司营收排名",
    x_column="地市名称",
    y_columns=["营业收入(万)"]
)
```

### 步骤3: 生成报告 (chatbi_report_final)
```python
generate_markdown_report(
    title="广电广东2025年营收分析报告",
    summary="数据概览内容...",
    insights="关键发现...",
    charts=["图表路径"],
    conclusions="结论与建议..."
)
```

## 数据库配置

在 `.env` 中配置:
```env
MYSQL_HOST=your_host
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_ads
```

## 依赖

- **pymysql**: 数据库连接
- **pandas**: 数据处理
- **matplotlib**: 图表生成
- **reportlab** (可选): PDF 报告生成