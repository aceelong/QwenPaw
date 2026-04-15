# -*- coding: utf-8 -*-
"""Chart generation tool for data visualization.

This tool generates charts (line, bar, pie, scatter) from data
and saves them as image files.
"""

import base64
import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...constant import WORKING_DIR

logger = logging.getLogger(__name__)

# Check if matplotlib is available
try:
    import matplotlib
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
    # Configure matplotlib for non-interactive backend
    matplotlib.use("Agg")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib or pandas not available, chart generation disabled")

# Configure Chinese font support
CHINESE_FONTS = [
    "SimHei",
    "Microsoft YaHei",
    "PingFang SC",
    "Heiti SC",
    "WenQuanYi Micro Hei",
    "Noto Sans CJK SC",
]


def _setup_chinese_font():
    """Setup Chinese font for matplotlib."""
    if not MATPLOTLIB_AVAILABLE:
        return

    plt.rcParams["font.sans-serif"] = CHINESE_FONTS + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_setup_chinese_font()


def _parse_data(data: Union[str, List, Dict]) -> Optional[pd.DataFrame]:
    """Parse input data into a pandas DataFrame.

    Args:
        data: Input data - can be JSON string, list of dicts, or dict

    Returns:
        pandas DataFrame or None
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        if isinstance(data, str):
            # Try to parse as JSON
            data = json.loads(data)

        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Single series or multiple series
            if all(isinstance(v, list) for v in data.values()):
                # Multiple series
                return pd.DataFrame(data)
            else:
                # Single series
                return pd.DataFrame([data])

        return None
    except Exception as e:
        logger.warning("Failed to parse data: %s", e)
        return None


def _auto_detect_chart_type(
    df: pd.DataFrame,
    suggested_type: Optional[str] = None,
) -> str:
    """Auto-detect the best chart type based on data.

    Args:
        df: Input DataFrame
        suggested_type: User-suggested chart type

    Returns:
        Chart type string
    """
    if suggested_type and suggested_type in ("line", "bar", "pie", "scatter"):
        return suggested_type

    if df is None or df.empty:
        return "bar"

    # Auto-detect based on data characteristics
    columns = df.columns.tolist()

    # If there's a date/time column, suggest line chart
    date_keywords = ["date", "time", "日期", "时间", "月", "年", "日"]
    for col in columns:
        if any(kw in col.lower() for kw in date_keywords):
            return "line"

    # If there's only one numeric column and one category column, suggest bar or pie
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_cols) == 1 and len(columns) == 2:
        return "bar"

    # Default to bar
    return "bar"


def _generate_line_chart(
    df: pd.DataFrame,
    title: str,
    x_column: Optional[str] = None,
    y_columns: Optional[List[str]] = None,
) -> BytesIO:
    """Generate a line chart.

    Args:
        df: Input DataFrame
        title: Chart title
        x_column: Column to use for x-axis
        y_columns: Columns to use for y-axis

    Returns:
        BytesIO object with PNG image
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    if x_column and x_column in df.columns:
        x_data = df[x_column]
    else:
        x_data = range(len(df))

    if y_columns:
        for col in y_columns:
            if col in df.columns:
                ax.plot(x_data, df[col], marker="o", label=col, linewidth=2)
    else:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        for col in numeric_cols:
            ax.plot(x_data, df[col], marker="o", label=col, linewidth=2)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(x_column or "Index", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf


def _generate_bar_chart(
    df: pd.DataFrame,
    title: str,
    x_column: Optional[str] = None,
    y_columns: Optional[List[str]] = None,
) -> BytesIO:
    """Generate a bar chart.

    Args:
        df: Input DataFrame
        title: Chart title
        x_column: Column to use for x-axis (categories)
        y_columns: Columns to use for y-axis (values)

    Returns:
        BytesIO object with PNG image
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    if x_column and x_column in df.columns:
        x_data = df[x_column]
        x_label = x_column
    else:
        # Use first column as categories
        x_data = df.iloc[:, 0] if len(df.columns) > 0 else range(len(df))
        x_label = df.columns[0] if len(df.columns) > 0 else "Category"

    if y_columns:
        for col in y_columns:
            if col in df.columns:
                ax.bar(x_data, df[col], label=col, alpha=0.8)
    else:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            ax.bar(x_data, df[col], label=col, alpha=0.8)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(x_label or "Category", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf


def _generate_pie_chart(
    df: pd.DataFrame,
    title: str,
    labels_column: Optional[str] = None,
    values_column: Optional[str] = None,
) -> BytesIO:
    """Generate a pie chart.

    Args:
        df: Input DataFrame
        title: Chart title
        labels_column: Column to use for labels
        values_column: Column to use for values

    Returns:
        BytesIO object with PNG image
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    if labels_column and labels_column in df.columns:
        labels = df[labels_column]
    else:
        # Use first column as labels
        labels = df.iloc[:, 0] if len(df.columns) > 0 else ["A", "B", "C", "D", "E"]

    if values_column and values_column in df.columns:
        values = df[values_column]
    else:
        # Use second column as values or auto-generate
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            values = df[numeric_cols[0]]
        else:
            values = [1] * len(labels)

    # Limit to top 10 for readability
    if len(labels) > 10:
        labels = labels[:10].tolist() + ["Others"]
        values = values[:10].tolist()
        if len(values) > 10:
            values = values[:10] + [sum(values[10:])]

    colors = plt.cm.Set3(range(len(labels)))

    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
    )
    ax.set_title(title, fontsize=14, fontweight="bold")

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf


def _generate_scatter_chart(
    df: pd.DataFrame,
    title: str,
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
) -> BytesIO:
    """Generate a scatter chart.

    Args:
        df: Input DataFrame
        title: Chart title
        x_column: Column to use for x-axis
        y_column: Column to use for y-axis

    Returns:
        BytesIO object with PNG image
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    x_col = x_column if x_column in numeric_cols else (numeric_cols[0] if len(numeric_cols) > 0 else None)
    y_col = y_column if y_column in numeric_cols else (numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0] if len(numeric_cols) > 0 else None)

    if x_col and y_col and x_col in df.columns and y_col in df.columns:
        ax.scatter(df[x_col], df[y_col], alpha=0.6, s=50)
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
    else:
        # Plot index vs first numeric
        if len(numeric_cols) > 0:
            ax.scatter(range(len(df)), df[numeric_cols[0]], alpha=0.6, s=50)
            ax.set_xlabel("Index", fontsize=12)
            ax.set_ylabel(numeric_cols[0], fontsize=12)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf


def generate_chart(
    data: str,
    chart_type: Literal["line", "bar", "pie", "scatter"] = "bar",
    title: str = "数据分析图表",
    output_path: Optional[str] = None,
    x_column: Optional[str] = None,
    y_columns: Optional[List[str]] = None,
    labels_column: Optional[str] = None,
    values_column: Optional[str] = None,
) -> ToolResponse:
    """Generate a chart from data.

    This tool takes data (JSON format) and generates a chart image.
    Supported chart types: line, bar, pie, scatter.

    Args:
        data: Data to visualize, can be:
            - JSON string (array of objects or object with arrays)
            - CSV content
            - File path to JSON/CSV file
        chart_type: Type of chart - "line", "bar", "pie", or "scatter".
            Defaults to "bar". Auto-detection can suggest better type.
        title: Chart title. Defaults to "数据分析图表".
        output_path: Optional path to save the chart image.
            If not provided, a temp file will be created.
        x_column: Column name to use for x-axis (line, bar, scatter).
        y_columns: List of column names to use for y-axis (line, bar).
        labels_column: Column name to use for pie chart labels.
        values_column: Column name to use for pie chart values.

    Returns:
        ToolResponse containing the chart image path or base64 encoded image
    """
    if not MATPLOTLIB_AVAILABLE:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: matplotlib is not available. "
                    "Please install matplotlib and pandas to use chart generation.",
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
        # Check if data is a file path
        data_path = Path(data)
        if data_path.exists() and data_path.suffix in (".json", ".csv"):
            if data_path.suffix == ".json":
                with open(data_path, "r", encoding="utf-8") as f:
                    data = f.read()
            else:
                # CSV file - read and convert to JSON
                df = pd.read_csv(data_path)
                data = df.to_json(orient="records", force_ascii=False)

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

        # Auto-detect chart type if needed
        chart_type = _auto_detect_chart_type(df, chart_type)

        # Generate chart based on type
        if chart_type == "line":
            buf = _generate_line_chart(df, title, x_column, y_columns)
        elif chart_type == "bar":
            buf = _generate_bar_chart(df, title, x_column, y_columns)
        elif chart_type == "pie":
            buf = _generate_pie_chart(df, title, labels_column, values_column)
        elif chart_type == "scatter":
            buf = _generate_scatter_chart(df, title, x_column, y_column)
        else:
            buf = _generate_bar_chart(df, title, x_column, y_columns)

        # Determine output path
        if output_path:
            output_file = Path(output_path)
        else:
            # Create temp file
            from .file_io import _get_temp_dir
            temp_dir = Path(WORKING_DIR) / ".qwenpaw" / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_file = temp_dir / f"chart_{id(buf)}.png"

        # Save to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "wb") as f:
            f.write(buf.getvalue())

        # Return result with file path
        result_text = f"Chart generated successfully:\n\nFile: {output_file}\nType: {chart_type}\nTitle: {title}\nData points: {len(df)}"

        return ToolResponse(
            content=[
                TextBlock(type="text", text=result_text),
            ],
        )

    except Exception as e:
        logger.error("Error generating chart: %s", e)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Error generating chart: {e}")],
        )
