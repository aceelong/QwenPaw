# -*- coding: utf-8 -*-
"""SQL execution tool supporting MySQL and Doris databases."""

import os
from pathlib import Path
from typing import Literal, Optional

import pymysql
from dotenv import load_dotenv
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...constant import WORKING_DIR


def _load_db_config(database: Literal["mysql", "doris"]) -> dict:
    """Load database configuration from .env file.

    Args:
        database: Database type - "mysql" or "doris"

    Returns:
        dict: Database connection configuration
    """
    prefix = database.upper()
    env_path = Path(WORKING_DIR) / ".env"

    if env_path.exists():
        load_dotenv(env_path)

    config = {
        "host": os.getenv(f"{prefix}_HOST", "localhost"),
        "port": int(os.getenv(f"{prefix}_PORT", "3306" if database == "mysql" else "9030")),
        "user": os.getenv(f"{prefix}_USER", "root"),
        "password": os.getenv(f"{prefix}_PASSWORD", ""),
        "database": os.getenv(f"{prefix}_DATABASE", ""),
    }

    return config


def _format_results(columns: tuple, rows: list) -> str:
    """Format query results as a readable table.

    Args:
        columns: Column names from cursor.description
        rows: Query result rows

    Returns:
        str: Formatted table string
    """
    if not rows:
        return "Query executed successfully. No results returned."

    col_names = [desc[0] for desc in columns]
    col_widths = [len(str(name)) for name in col_names]

    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    header = " | ".join(
        str(name).ljust(width) for name, width in zip(col_names, col_widths)
    )
    separator = "-+-".join("-" * width for width in col_widths)

    lines = [header, separator]
    for row in rows:
        line = " | ".join(
            str(val).ljust(width) for val, width in zip(row, col_widths)
        )
        lines.append(line)

    return "\n".join(lines)


def execute_sql(
    sql: str,
    database: Literal["mysql", "doris"] = "mysql",
    timeout: float = 30.0,
) -> ToolResponse:
    """Execute SQL query on MySQL or Doris database.

    Configuration is read from .env file in the working directory:
    - MySQL: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
    - Doris: DORIS_HOST, DORIS_PORT, DORIS_USER, DORIS_PASSWORD, DORIS_DATABASE

    Args:
        sql: SQL query to execute. Supports SELECT, INSERT, UPDATE, DELETE, etc.
        database: Database type - "mysql" or "doris". Defaults to "mysql".
        timeout: Query timeout in seconds. Defaults to 30.0.

    Returns:
        ToolResponse: Query results or error message in text format.
    """
    if not sql or not sql.strip():
        return ToolResponse(
            content=[TextBlock(type="text", text="Error: SQL query cannot be empty.")],
        )

    if database not in ("mysql", "doris"):
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Error: Unsupported database type '{database}'. Use 'mysql' or 'doris'.")],
        )

    try:
        config = _load_db_config(database)

        if not config["host"]:
            return ToolResponse(
                content=[TextBlock(type="text", text=f"Error: {database.upper()}_HOST is not configured in .env file.")],
            )

        connection = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"] or None,
            connect_timeout=timeout,
            read_timeout=timeout,
            write_timeout=timeout,
            charset="utf8mb4",
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)

                sql_upper = sql.strip().upper()
                is_select = sql_upper.startswith("SELECT") or sql_upper.startswith("SHOW")

                if is_select:
                    columns = cursor.description
                    rows = cursor.fetchall()
                    result_text = _format_results(columns, rows)
                    row_count = len(rows)
                    result_text += f"\n\n({row_count} row{'s' if row_count != 1 else ''} affected)"
                else:
                    connection.commit()
                    row_count = cursor.rowcount
                    result_text = f"Query executed successfully. ({row_count} row{'s' if row_count != 1 else ''} affected)"

                return ToolResponse(
                    content=[TextBlock(type="text", text=result_text)],
                )
        finally:
            connection.close()

    except pymysql.Error as e:
        error_msg = f"Database error: {e}"
        return ToolResponse(
            content=[TextBlock(type="text", text=error_msg)],
        )
    except Exception as e:
        error_msg = f"Error: {e}"
        return ToolResponse(
            content=[TextBlock(type="text", text=error_msg)],
        )
