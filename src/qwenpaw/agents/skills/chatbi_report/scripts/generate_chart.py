# -*- coding: utf-8 -*-
"""Chart generation for ChatBI reports."""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import json


def generate_chart(
    data: List[Dict[str, Any]],
    chart_type: str = "bar",
    title: str = "Chart",
    x_field: str = "x",
    y_field: str = "y",
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """Generate a chart from data.

    Args:
        data: List of data records
        chart_type: Type of chart (bar, line, pie, scatter)
        title: Chart title
        x_field: Field name for x-axis
        y_field: Field name for y-axis
        output_dir: Directory to save chart

    Returns:
        Path to generated chart image or None
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        # Use non-interactive backend
        matplotlib.use('Agg')
    except ImportError:
        print("Warning: matplotlib not available, chart generation disabled")
        return None

    if not output_dir:
        output_dir = Path(__file__).parent.parent / "charts"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract x and y values
    x_values = [str(row.get(x_field, "")) for row in data]
    y_values = [float(row.get(y_field, 0)) for row in data]

    plt.figure(figsize=(10, 6))

    if chart_type == "bar":
        plt.bar(x_values, y_values)
        plt.xlabel(x_field)
    elif chart_type == "line":
        plt.plot(x_values, y_values, marker='o')
        plt.xlabel(x_field)
    elif chart_type == "pie":
        plt.pie(y_values, labels=x_values, autopct='%1.1f%%')
    elif chart_type == "scatter":
        plt.scatter(x_values, y_values)
        plt.xlabel(x_field)

    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Generate filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{safe_title}_{chart_type}.png"
    output_path = output_dir / filename

    plt.savefig(output_path, dpi=100)
    plt.close()

    return str(output_path)


def generate_revenue_chart(
    data: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """Generate revenue comparison chart.

    Args:
        data: List of city revenue data
        output_dir: Output directory

    Returns:
        Path to generated chart
    """
    return generate_chart(
        data=data,
        chart_type="bar",
        title="各分公司营收排名",
        x_field="地市名称",
        y_field="营业收入(万)",
        output_dir=output_dir,
    )


def generate_trend_chart(
    data: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """Generate trend line chart.

    Args:
        data: List of time series data
        output_dir: Output directory

    Returns:
        Path to generated chart
    """
    return generate_chart(
        data=data,
        chart_type="line",
        title="营收趋势",
        x_field="年月",
        y_field="指标值(万)",
        output_dir=output_dir,
    )


if __name__ == "__main__":
    # Test chart generation
    sample_data = [
        {"地市名称": "广州市", "营业收入(万)": 10000},
        {"地市名称": "深圳市", "营业收入(万)": 9000},
        {"地市名称": "佛山市", "营业收入(万)": 8000},
    ]

    chart_path = generate_revenue_chart(sample_data)
    print(f"Chart generated: {chart_path}")