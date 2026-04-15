# -*- coding: utf-8 -*-
"""Data analysis tool for statistical analysis and insights.

This tool performs statistical analysis on data and generates
natural language insights.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...constant import WORKING_DIR

logger = logging.getLogger(__name__)

# Check if pandas and numpy are available
try:
    import pandas as pd
    import numpy as np

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available, data analysis disabled")


def _parse_data(data: Union[str, List, Dict]) -> Optional[pd.DataFrame]:
    """Parse input data into a pandas DataFrame.

    Args:
        data: Input data - can be JSON string, list of dicts, or dict

    Returns:
        pandas DataFrame or None
    """
    if not PANDAS_AVAILABLE:
        return None

    try:
        if isinstance(data, str):
            # Check if it's a file path
            data_path = Path(data)
            if data_path.exists() and data_path.suffix in (".json", ".csv"):
                if data_path.suffix == ".json":
                    with open(data_path, "r", encoding="utf-8") as f:
                        data = f.read()
                else:
                    return pd.read_csv(data_path)

            # Try to parse as JSON
            data = json.loads(data)

        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Single series or multiple series
            if all(isinstance(v, list) for v in data.values()):
                return pd.DataFrame(data)
            else:
                return pd.DataFrame([data])

        return None
    except Exception as e:
        logger.warning("Failed to parse data: %s", e)
        return None


def _analyze_summary(df: pd.DataFrame) -> str:
    """Generate summary statistics.

    Args:
        df: Input DataFrame

    Returns:
        Formatted summary text
    """
    lines = ["## 数据概览\n"]
    lines.append(f"- 总记录数: {len(df):,}")
    lines.append(f"- 列数: {len(df.columns)}")
    lines.append(f"- 列名: {', '.join(df.columns.tolist())}")
    lines.append("")

    # Numeric columns summary
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        lines.append("## 数值列统计\n")
        for col in numeric_cols:
            lines.append(f"### {col}")
            lines.append(f"- 总数: {df[col].count():,}")
            lines.append(f"- 平均值: {df[col].mean():.2f}")
            lines.append(f"- 中位数: {df[col].median():.2f}")
            lines.append(f"- 标准差: {df[col].std():.2f}")
            lines.append(f"- 最小值: {df[col].min():.2f}")
            lines.append(f"- 最大值: {df[col].max():.2f}")
            lines.append("")

    return "\n".join(lines)


def _analyze_trend(df: pd.DataFrame, dimensions: Optional[List[str]] = None) -> str:
    """Analyze trends in time series data.

    Args:
        df: Input DataFrame
        dimensions: Columns to analyze for trends

    Returns:
        Formatted trend analysis text
    """
    lines = ["## 趋势分析\n"]

    if dimensions is None:
        # Auto-detect date/time columns
        date_keywords = ["date", "time", "日期", "时间", "月", "年", "日", "created", "updated"]
        date_cols = [
            col for col in df.columns
            if any(kw in col.lower() for kw in date_keywords)
        ]
        dimensions = date_cols if date_cols else [df.columns[0]] if len(df.columns) > 0 else None

    if dimensions is None:
        return "## 趋势分析\n无法分析趋势，缺少时间维度列。\n"

    # Find numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns

    lines.append(f"分析维度: {', '.join(dimensions)}\n")

    for dim_col in dimensions:
        if dim_col not in df.columns:
            continue

        lines.append(f"### 按 {dim_col} 的趋势\n")

        # Sort by dimension column
        try:
            df_sorted = df.sort_values(by=dim_col)
        except Exception:
            df_sorted = df

        for num_col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            values = df_sorted[num_col].values
            if len(values) < 2:
                continue

            # Calculate trend
            x = range(len(values))
            slope = np.polyfit(x, values, 1)[0] if len(values) > 1 else 0

            trend_direction = "上升" if slope > 0 else "下降" if slope < 0 else "平稳"
            total_change = values[-1] - values[0] if len(values) > 0 else 0
            pct_change = (total_change / values[0] * 100) if values[0] != 0 else 0

            lines.append(f"- {num_col}: {trend_direction}趋势")
            lines.append(f"  - 变化量: {total_change:+.2f}")
            lines.append(f"  - 变化率: {pct_change:+.1f}%")

        lines.append("")

    return "\n".join(lines)


def _analyze_comparison(
    df: pd.DataFrame,
    dimensions: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
) -> str:
    """Generate comparison analysis.

    Args:
        df: Input DataFrame
        dimensions: Columns to group by
        metrics: Numeric columns to compare

    Returns:
        Formatted comparison text
    """
    lines = ["## 对比分析\n"]

    # Auto-detect dimensions and metrics
    if dimensions is None:
        # Use non-numeric columns as dimensions
        non_numeric = df.select_dtypes(exclude=["number"]).columns
        dimensions = non_numeric.tolist()[:3]  # Limit to first 3

    if metrics is None:
        # Use numeric columns as metrics
        metrics = df.select_dtypes(include=["number"]).columns.tolist()

    if not dimensions or not metrics:
        return "## 对比分析\n无法进行对比分析，缺少维度或指标列。\n"

    lines.append(f"对比维度: {', '.join(dimensions)}\n")
    lines.append(f"对比指标: {', '.join(metrics)}\n\n")

    # Generate comparison for each dimension
    for dim in dimensions:
        if dim not in df.columns:
            continue

        lines.append(f"### 按 {dim} 对比\n")

        grouped = df.groupby(dim)[metrics].agg(["mean", "sum", "count"])
        grouped.columns = ["_".join(col).strip() for col in grouped.columns.values]

        # Get top 10 groups
        top_groups = grouped.head(10)

        for idx in top_groups.index:
            lines.append(f"#### {dim} = {idx}")
            for col in metrics:
                if f"{col}_mean" in top_groups.columns:
                    lines.append(f"- 平均{col}: {top_groups.loc[idx, f'{col}_mean']:.2f}")
                    lines.append(f"- 总计{col}: {top_groups.loc[idx, f'{col}_sum']:.2f}")
                    lines.append(f"- 记录数: {top_groups.loc[idx, f'{col}_count']:.0f}")
            lines.append("")

    return "\n".join(lines)


def _analyze_outlier(
    df: pd.DataFrame,
    metrics: Optional[List[str]] = None,
) -> str:
    """Detect outliers in data.

    Args:
        df: Input DataFrame
        metrics: Numeric columns to check for outliers

    Returns:
        Formatted outlier analysis text
    """
    lines = ["## 异常值检测\n"]

    if metrics is None:
        metrics = df.select_dtypes(include=["number"]).columns.tolist()

    if not metrics:
        return "## 异常值检测\n没有数值列可用于异常值检测。\n"

    lines.append("使用 IQR (四分位距) 方法检测异常值\n\n")

    for col in metrics:
        if col not in df.columns:
            continue

        values = df[col].dropna()

        if len(values) < 4:
            lines.append(f"### {col}: 数据量不足，无法检测异常值\n")
            continue

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]

        lines.append(f"### {col}")
        lines.append(f"- Q1 (25%): {q1:.2f}")
        lines.append(f"- Q3 (75%): {q3:.2f}")
        lines.append(f"- IQR: {iqr:.2f}")
        lines.append(f"- 下界: {lower_bound:.2f}")
        lines.append(f"- 上界: {upper_bound:.2f}")
        lines.append(f"- 异常值数量: {len(outliers)} ({len(outliers)/len(df)*100:.1f}%)")

        if len(outliers) > 0 and len(outliers) <= 10:
            lines.append("- 异常记录:")
            for idx, row in outliers.iterrows():
                lines.append(f"  - {col} = {row[col]:.2f}")

        lines.append("")

    return "\n".join(lines)


def _generate_insights(df: pd.DataFrame) -> str:
    """Generate key insights from data.

    Args:
        df: Input DataFrame

    Returns:
        Formatted insights text
    """
    lines = ["## 关键发现\n"]

    # Record count
    lines.append(f"1. 数据集包含 {len(df):,} 条记录，涵盖 {len(df.columns)} 个字段。")

    # Numeric insights
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        # Find max and min
        for col in numeric_cols[:3]:
            max_val = df[col].max()
            min_val = df[col].min()
            max_idx = df[col].idxmax()
            min_idx = df[col].idxmin()

            lines.append(
                f"2. {col} 范围从 {min_val:.2f} 到 {max_val:.2f}，"
                f"平均值为 {df[col].mean():.2f}。"
            )

    # Non-numeric insights
    non_numeric = df.select_dtypes(exclude=["number"]).columns
    if len(non_numeric) > 0:
        for col in non_numeric[:3]:
            top_value = df[col].value_counts().idxmax()
            top_count = df[col].value_counts().max()
            unique_count = df[col].nunique()
            lines.append(
                f"3. {col} 共有 {unique_count} 个不同值，"
                f"最常见的是 '{top_value}' ({top_count}次)。"
            )

    return "\n".join(lines)


def analyze_data(
    data: str,
    analysis_type: Literal["summary", "trend", "comparison", "outlier", "insights"] = "summary",
    dimensions: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
) -> ToolResponse:
    """Analyze data and generate statistical insights.

    This tool performs various types of statistical analysis on data
    and returns natural language insights.

    Args:
        data: Data to analyze, can be:
            - JSON string (array of objects or object with arrays)
            - CSV content
            - File path to JSON/CSV file
        analysis_type: Type of analysis to perform:
            - "summary": Basic statistics (count, mean, median, etc.)
            - "trend": Time series trend analysis
            - "comparison": Group comparison analysis
            - "outlier": Outlier detection using IQR method
            - "insights": Key findings and patterns
            Defaults to "summary".
        dimensions: List of column names to use as dimensions for grouping.
            Auto-detected if not provided.
        metrics: List of numeric column names to analyze.
            Auto-detected if not provided.

    Returns:
        ToolResponse containing the analysis results in text format
    """
    if not PANDAS_AVAILABLE:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: pandas is not available. "
                    "Please install pandas to use data analysis.",
                )
            ],
        )

    if not data or not data.strip():
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: Data cannot be empty. "
                    "Please provide data in JSON format.",
                )
            ],
        )

    try:
        # Parse data
        df = _parse_data(data)
        if df is None or df.empty:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: Failed to parse data. "
                        "Please provide valid JSON data.",
                    )
                ],
            )

        # Perform analysis based on type
        if analysis_type == "summary":
            result = _analyze_summary(df)
        elif analysis_type == "trend":
            result = _analyze_trend(df, dimensions)
        elif analysis_type == "comparison":
            result = _analyze_comparison(df, dimensions, metrics)
        elif analysis_type == "outlier":
            result = _analyze_outlier(df, metrics)
        elif analysis_type == "insights":
            result = _generate_insights(df)
        else:
            result = _analyze_summary(df)

        return ToolResponse(
            content=[TextBlock(type="text", text=result)],
        )

    except Exception as e:
        logger.error("Error analyzing data: %s", e)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Error analyzing data: {e}")],
        )
