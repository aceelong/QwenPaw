---
name: chatbi_chart
description: "Use this skill when the user wants to generate charts/visualizations from data. This outputs ECharts-compatible Markdown code blocks that can be rendered in supported interfaces. Triggers: user asks for '图表', '可视化', '画图', '趋势图', '柱状图'."
metadata:
  builtin_skill_version: "1.0"
---

# ChatBI Chart Generation Skill

This skill generates ECharts-compatible Markdown charts from data. Output format is `echarts` code block that renders interactive charts.

## Supported Chart Types

| Chart Type | Use Case | Example |
|------------|----------|---------|
| **bar** | Category comparison, rankings | 各分公司营收排名 |
| **line** | Time series trends | 营收月度趋势 |
| **pie** | Proportion analysis | 营收占比分布 |
| **scatter** | Correlation analysis | 营收vs用户数 |

## Output Format

Output an ECharts code block in Markdown:

```markdown
```echarts
{
  "title": { "text": "图表标题" },
  "tooltip": { "trigger": "axis" },
  "xAxis": { "type": "category", "data": ["广州市", "深圳市", ...] },
  "yAxis": { "type": "value" },
  "series": [{ "type": "bar", "data": [10000, 9000, ...] }]
}
```
```

## Data Format

### Input (from query results)

```json
[
  {"地市名称": "广州市", "营业收入(万)": 10000},
  {"地市名称": "深圳市", "营业收入(万)": 9000},
  {"地市名称": "佛山市", "营业收入(万)": 8000}
]
```

## Generation Rules

### Step 1: Extract Data
- Parse the query result data
- Identify x-axis field (category) and y-axis field (value)

### Step 2: Generate ECharts JSON

**Bar Chart Template:**
```json
{
  "title": { "text": "各分公司营收排名", "left": "center" },
  "tooltip": { "trigger": "axis", "formatter": "{b}: {c} 万" },
  "grid": { "left": "3%", "right": "4%", "bottom": "3%", "containLabel": true },
  "xAxis": {
    "type": "category",
    "data": ["广州市", "深圳市", "佛山市", ...],
    "axisLabel": { "rotate": 0 }
  },
  "yAxis": { "type": "value", "name": "万元" },
  "series": [{
    "type": "bar",
    "data": [10000, 9000, 8000, ...],
    "itemStyle": { "color": "#5470C6" },
    "label": { "show": true, "position": "top", "formatter": "{c} 万" }
  }]
}
```

**Line Chart Template:**
```json
{
  "title": { "text": "月度营收趋势", "left": "center" },
  "tooltip": { "trigger": "axis" },
  "grid": { "left": "3%", "right": "4%", "bottom": "3%", "containLabel": true },
  "xAxis": {
    "type": "category",
    "data": ["202501", "202502", "202503", ...],
    "boundaryGap": false
  },
  "yAxis": { "type": "value", "name": "万元" },
  "series": [{
    "type": "line",
    "data": [8000, 8200, 8500, ...],
    "smooth": true,
    "itemStyle": { "color": "#91CC75" },
    "areaStyle": { "opacity": 0.3 }
  }]
}
```

**Pie Chart Template:**
```json
{
  "title": { "text": "营收占比分布", "left": "center" },
  "tooltip": { "trigger": "item", "formatter": "{b}: {c} ({d}%)" },
  "legend": { "orient": "vertical", "left": "left" },
  "series": [{
    "type": "pie",
    "radius": "50%",
    "data": [
      { "value": 10000, "name": "广州市" },
      { "value": 9000, "name": "深圳市" },
      { "value": 8000, "name": "佛山市" }
    ],
    "label": { "formatter": "{b}: {d}%" }
  }]
}
```

## Examples

### Example 1: Bar Chart - Revenue Ranking

**Input Data (from query):**
```
| 地市名称 | 营业收入(万) |
|----------|-------------|
| 广州市   | 10000       |
| 深圳市   | 9000        |
| 佛山市   | 8000        |
| 东莞市   | 7500        |
| 珠海市   | 6000        |
```

**Output:**
```markdown
```echarts
{
  "title": { "text": "各分公司营收排名", "left": "center" },
  "tooltip": { "trigger": "axis", "formatter": "{b}: {c} 万" },
  "grid": { "left": "3%", "right": "4%", "bottom": "3%", "containLabel": true },
  "xAxis": {
    "type": "category",
    "data": ["广州市", "深圳市", "佛山市", "东莞市", "珠海市"]
  },
  "yAxis": { "type": "value", "name": "万元" },
  "series": [{
    "type": "bar",
    "data": [10000, 9000, 8000, 7500, 6000],
    "itemStyle": { "color": "#5470C6" },
    "label": { "show": true, "position": "top", "formatter": "{c}" }
  }]
}
```
```

### Example 2: Line Chart - Monthly Trend

**Input Data:**
```
| 年月   | 营收(万) |
|--------|----------|
| 202501 | 8000     |
| 202502 | 8200     |
| 202503 | 8500     |
| 202504 | 8800     |
| 202505 | 9000     |
```

**Output:**
```markdown
```echarts
{
  "title": { "text": "2025年月度营收趋势", "left": "center" },
  "tooltip": { "trigger": "axis" },
  "grid": { "left": "3%", "right": "4%", "bottom": "3%", "containLabel": true },
  "xAxis": {
    "type": "category",
    "data": ["202501", "202502", "202503", "202504", "202505"],
    "boundaryGap": false
  },
  "yAxis": { "type": "value", "name": "万元" },
  "series": [{
    "type": "line",
    "data": [8000, 8200, 8500, 8800, 9000],
    "smooth": true,
    "itemStyle": { "color": "#91CC75" },
    "areaStyle": { "opacity": 0.3 },
    "label": { "show": true, "position": "top" }
  }]
}
```
```

### Example 3: Pie Chart - Proportion

**Input Data:**
```
| 地市 | 营收占比 |
|------|----------|
| 广州 | 30       |
| 深圳 | 25       |
| 佛山 | 15       |
| 其他 | 30       |
```

**Output:**
```markdown
```echarts
{
  "title": { "text": "营收占比分布", "left": "center" },
  "tooltip": { "trigger": "item", "formatter": "{b}: {c}% ({d}%)" },
  "legend": { "orient": "vertical", "left": "left", "top": "middle" },
  "series": [{
    "type": "pie",
    "radius": ["40%", "70%"],
    "avoidLabelOverlap": false,
    "itemStyle": { "borderRadius": 10, "borderColor": "#fff", "borderWidth": 2 },
    "label": { "show": false, "position": "center" },
    "emphasis": {
      "label": { "show": true, "fontSize": 20, "fontWeight": "bold" }
    },
    "data": [
      { "value": 30, "name": "广州" },
      { "value": 25, "name": "深圳" },
      { "value": 15, "name": "佛山" },
      { "value": 30, "name": "其他" }
    ]
  }]
}
```
```

## Color Palette

Use these colors for series:
- Bar: `#5470C6` (蓝色)
- Line: `#91CC75` (绿色)
- Pie: `["#5470C6", "#91CC75", "#FAC858", "#EE6666", "#73C0DE", "#3BA272", "#FC8452", "#9A60B4", "#EA7CCC"]`

## Best Practices

1. **Use appropriate chart types**:
   - Rankings → bar
   - Trends → line
   - Proportions → pie

2. **Limit data points**: Pie charts max 8-10 items, show "其他" for remainder

3. **Add labels**: Always show value labels on bars/top of line points

4. **Include units**: In title or yAxis name (万元/万户)

5. **Chinese text**: Ensure all labels use Chinese characters

## Important Notes

- **Output ONLY the echarts code block**, no additional text
- **No actual image generation** - output JSON for ECharts rendering
- **Always use code block** with `\`\`\`echarts` syntax
- **Valid JSON** - ensure proper quotes and commas