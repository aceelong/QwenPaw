---
name: chatbi_query
description: "Use this skill when the user wants to query business data for the Guangdong Broadcasting Network (广电广东). This generates SQL from natural language questions, executes the SQL on MySQL/Doris database, and returns formatted query results. Triggers: any mention of 营收, 用户数, 各分公司, 全省, 地市, 业务区, or similar business data queries."
metadata:
  builtin_skill_version: "1.0"
---

# ChatBI Query Skill

This skill generates SQL from natural language and executes it on the database in one workflow.

## Workflow

```
用户问题 -> 生成SQL -> 执行SQL -> 返回结果
```

## Step 1: SQL Generation

### Table Overview

**Table:** `ai_ads.ads_chatbi_summary_sta_level`

**Description:** Pre-aggregated wide table — each record is uniquely aggregated by (year-month + dimension + level + indicator). Stores various business, user, and financial metrics aggregated by city or business district dimensions.

### Key Columns

#### Filter Fields
| Field | Type | Format | Description |
|-------|------|--------|-------------|
| 年月 | VARCHAR(6) | YYYYMM | Filter field, e.g., `202501` |

#### Dimension Fields
| Field | Type | Description |
|-------|------|-------------|
| 统计维度 | VARCHAR(200) | Data aggregation dimension. Values: `全省`, `地市`, `业务区`, `支公司`, `大网格`, `片区`, `片区中心`, `网格` |
| 地市名称 | VARCHAR(200) | 20 cities in Guangdong + 全省 |
| 业务区名称 | VARCHAR(200) | Secondary organization unit name |
| 第三层级名称 | VARCHAR(200) | Finest granularity business unit |
| 指标名称 | VARCHAR(200) | Indicator whitelist field (**strict match required**) |

#### Metric Fields
| Field | Type | Description |
|-------|------|-------------|
| 指标值 | DECIMAL(18,6) | Current period actual value, **accumulated monthly for the year** |
| 上期指标值 | DECIMAL(18,6) | MoM value |
| 去年同期值 | DECIMAL(18,6) | YoY value |
| 考核目标值 | DECIMAL(28,6) | Current period target |

### Dimension Mapping Rules

| Dimension | Condition | SQL Fragment |
|-----------|-----------|--------------|
| **全省** | User mentions "全省"/"全省汇总" | `WHERE 统计维度 = '全省'` |
| **地市** | User mentions city name or "各分公司" | `WHERE 统计维度 = '地市' AND 地市名称 IN (...)` |
| **业务区** | User mentions business district name | `WHERE 统计维度 = '业务区' AND 业务区名称 IN (...)` |
| **第三层级** | User mentions grid/branch | `WHERE 统计维度 IN ('网格','社区网格','支公司',...) AND 第三层级名称 IN (...)` |

### Date Handling Rules

> Current date: `2026-01-31`

| Priority | Scenario | Logic | Example |
|----------|----------|-------|---------|
| 1 | Historical year (< 2026) | Take December only | `2024年` → `年月 = '202412'` |
| 2 | Current year + "各月" | Range query | `2026年各月` → `202601`~`202612` |
| 3 | "上月" | Previous month | `2026-01` → `202512` |
| 4 | No date specified | Default to previous month | `2026-01-31` → `202512` |

### Indicator Alias Mapping

| Alias | Actual Indicator (Whitelist) |
|-------|------------------------------|
| **营收** | 营业收入(25版考核)、营业总收入、营业收入(含预出账) |
| **用户数** | 数字主机缴费用户数(25版)、宽带缴费用户数、5G在用用户数、5G在网用户数 |

### City Name Enumeration

| Alias | Standard Value |
|-------|----------------|
| 潮州分公司 | 潮州市 |
| 阳江分公司 | 阳江市 |
| 河源分公司 | 河源市 |
| 广州公司 / 广州广电 | 珠江数码 |
| 直属 / 直属公司 | 广东有线 |
| 广州市 / 广州 / 大广州 | 广州市 |
| ... | ... |

### SQL Generation Rules

| Requirement | Description |
|-------------|-------------|
| Pure SQL only | Start with `SELECT`, no explanations |
| Date format | `YYYYMM` (e.g., `202512`) |
| Field aliases | Use **backticks** (e.g., `` `营业收入` ``) |
| Unit conversion | Default to `/ 10000` for "万" |

### SQL Example

**Input:** 各分公司2025年营收排名

```sql
SELECT 年月, 地市名称, 指标名称, 指标值 / 10000 AS `营业收入(万)`, 上期指标值 / 10000 AS `上期营业收入(万)`, 去年同期值 / 10000 AS `去年同期营业收入(万)`, 考核目标值 / 10000 AS `考核目标值(万)`, (指标值 / 考核目标值) * 100 AS `考核完成率`, ROW_NUMBER() OVER (ORDER BY 指标值 DESC) AS `排名` FROM ai_ads.ads_chatbi_summary_sta_level WHERE 统计维度 = '地市' AND 年月 = '202512' AND 指标名称 IN ('营业收入(25版考核)','营业总收入','营业收入(含预出账)') ORDER BY 指标值 DESC;
```

## Step 2: SQL Execution

Use the `execute_sql` tool from `src/qwenpaw/agents/tools/sql_execute.py`:

```python
result = execute_sql(
    sql="SELECT ...",
    database="mysql",  # or "doris"
    timeout=30.0
)
```

### Configuration

Database credentials in `.env`:
```env
MYSQL_HOST=your_host
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_ads
```

## Return Format

The tool returns a formatted table:
```
年月    | 地市名称 | 指标名称      | 指标值(万) | ... 
--------|----------|--------------|------------| ---
202512  | 广州市   | 营业收入(考核) | 10000.00   | ...
202512  | 深圳市   | 营业收入(考核) | 9000.00    | ...

(2 rows affected)
```

## Prerequisites

- **pymysql**: Database connectivity
- Database credentials configured in `.env`