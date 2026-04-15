# -*- coding: utf-8 -*-
"""Database metadata management for SQL generation.

This module provides functionality to load, cache, and manage database
table schemas (metadata) for use in SQL generation from natural language.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import pymysql
from dotenv import load_dotenv

from ...constant import WORKING_DIR

logger = logging.getLogger(__name__)

METADATA_CACHE_DIR = Path(WORKING_DIR) / ".qwenpaw" / "db_metadata"


@dataclass
class ColumnMeta:
    """Metadata for a database column."""

    name: str
    type: str
    comment: str = ""
    is_nullable: bool = True
    key: str = ""  # PRI, UNI, MUL, etc.
    default: Optional[str] = None


@dataclass
class TableMeta:
    """Metadata for a database table."""

    name: str
    comment: str = ""
    columns: List[ColumnMeta] = field(default_factory=list)


@dataclass
class DatabaseMetadata:
    """Metadata for an entire database."""

    database: str
    tables: List[TableMeta] = field(default_factory=list)
    loaded_at: Optional[str] = None


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


def _get_cache_file(database: str) -> Path:
    """Get the cache file path for a database.

    Args:
        database: Database name

    Returns:
        Path to cache file
    """
    METADATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Sanitize database name for filesystem
    safe_name = database.replace("/", "_").replace("\\", "_")
    return METADATA_CACHE_DIR / f"{safe_name}.json"


def _parse_column(row: tuple) -> ColumnMeta:
    """Parse a DESCRIBE query row into ColumnMeta.

    Args:
        row: Row from DESCRIBE table query

    Returns:
        ColumnMeta object
    """
    return ColumnMeta(
        name=row[0],
        type=str(row[1]),
        is_nullable=row[2] == "YES",
        key=row[3] or "",
        default=str(row[4]) if row[4] is not None else None,
        comment=str(row[8]) if len(row) > 8 and row[8] else "",
    )


def _load_metadata_from_db(database: Literal["mysql", "doris"]) -> DatabaseMetadata:
    """Load metadata directly from database.

    Args:
        database: Database type - "mysql" or "doris"

    Returns:
        DatabaseMetadata object with all table schemas
    """
    config = _load_db_config(database)

    if not config["host"]:
        raise ValueError(f"{database.upper()}_HOST is not configured in .env file")

    connection = pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"] or None,
        connect_timeout=30,
        read_timeout=30,
        charset="utf8mb4",
    )

    try:
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("SHOW TABLES")
            table_rows = cursor.fetchall()

            db_name = config["database"] or "unknown"
            metadata = DatabaseMetadata(database=db_name)

            for row in table_rows:
                table_name = row[0]

                # Get table comment
                cursor.execute(f"SHOW TABLE STATUS WHERE Name = '{table_name}'")
                status_rows = cursor.fetchall()
                table_comment = ""
                if status_rows:
                    table_comment = str(status_rows[0][-1]) if status_rows[0][-1] else ""

                # Get column info using DESCRIBE
                cursor.execute(f"DESCRIBE `{table_name}`")
                column_rows = cursor.fetchall()

                columns = [_parse_column(row) for row in column_rows]

                table_meta = TableMeta(
                    name=table_name,
                    comment=table_comment,
                    columns=columns,
                )
                metadata.tables.append(table_meta)

            return metadata

    finally:
        connection.close()


def load_metadata(
    database: Literal["mysql", "doris"] = "mysql",
    use_cache: bool = True,
    force_refresh: bool = False,
) -> DatabaseMetadata:
    """Load database metadata, using cache if available.

    Args:
        database: Database type - "mysql" or "doris"
        use_cache: Whether to use cached metadata if available
        force_refresh: Force refresh from database even if cache exists

    Returns:
        DatabaseMetadata object
    """
    config = _load_db_config(database)
    db_name = config["database"] or "unknown"
    cache_file = _get_cache_file(db_name)

    # Try to load from cache first
    if use_cache and not force_refresh and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            metadata = DatabaseMetadata(
                database=data["database"],
                tables=[
                    TableMeta(
                        name=t["name"],
                        comment=t.get("comment", ""),
                        columns=[ColumnMeta(**c) for c in t.get("columns", [])],
                    )
                    for t in data.get("tables", [])
                ],
                loaded_at=data.get("loaded_at"),
            )
            logger.info("Loaded metadata from cache: %s", cache_file)
            return metadata
        except Exception as e:
            logger.warning("Failed to load metadata cache: %s, refreshing...", e)

    # Load from database
    metadata = _load_metadata_from_db(database)

    # Save to cache
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "database": metadata.database,
                    "tables": [
                        {
                            "name": t.name,
                            "comment": t.comment,
                            "columns": [asdict(c) for c in t.columns],
                        }
                        for t in metadata.tables
                    ],
                    "loaded_at": metadata.loaded_at,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info("Saved metadata to cache: %s", cache_file)
    except Exception as e:
        logger.warning("Failed to save metadata cache: %s", e)

    return metadata


def get_tables(metadata: DatabaseMetadata) -> List[TableMeta]:
    """Get all tables from metadata.

    Args:
        metadata: DatabaseMetadata object

    Returns:
        List of TableMeta objects
    """
    return metadata.tables


def get_table_schema(
    metadata: DatabaseMetadata,
    table_name: str,
) -> Optional[TableMeta]:
    """Get schema for a specific table.

    Args:
        metadata: DatabaseMetadata object
        table_name: Name of the table

    Returns:
        TableMeta object or None if not found
    """
    for table in metadata.tables:
        if table.name == table_name:
            return table
    return None


def search_tables(
    metadata: DatabaseMetadata,
    keyword: str,
) -> List[TableMeta]:
    """Search tables by name or comment keyword.

    Args:
        metadata: DatabaseMetadata object
        keyword: Search keyword

    Returns:
        List of matching TableMeta objects
    """
    keyword_lower = keyword.lower()
    results = []
    for table in metadata.tables:
        if (
            keyword_lower in table.name.lower()
            or keyword_lower in table.comment.lower()
        ):
            results.append(table)
    return results


def to_prompt_context(
    metadata: DatabaseMetadata,
    include_columns: bool = True,
    max_tables: Optional[int] = None,
) -> str:
    """Convert metadata to a prompt context string for LLM.

    Args:
        metadata: DatabaseMetadata object
        include_columns: Whether to include column details
        max_tables: Maximum number of tables to include (None for all)

    Returns:
        Formatted string suitable for use in prompt
    """
    tables = metadata.tables[:max_tables] if max_tables else metadata.tables

    lines = [f"Database: {metadata.database}"]
    lines.append("")

    for table in tables:
        lines.append(f"### Table: {table.name}")
        if table.comment:
            lines.append(f"Comment: {table.comment}")

        if include_columns and table.columns:
            lines.append("Columns:")
            for col in table.columns:
                nullable = "NULL" if col.is_nullable else "NOT NULL"
                default = f" DEFAULT {col.default}" if col.default else ""
                key = f" [{col.key}]" if col.key else ""
                comment = f" -- {col.comment}" if col.comment else ""
                lines.append(
                    f"  - {col.name}: {col.type} {nullable}{default}{key}{comment}",
                )
        lines.append("")

    return "\n".join(lines)
