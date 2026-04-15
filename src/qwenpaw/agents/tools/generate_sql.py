# -*- coding: utf-8 -*-
"""SQL generation tool using natural language to SQL conversion.

This tool uses LLM to generate SQL queries based on database metadata
and user questions.
"""

import logging
import re
from pathlib import Path
from typing import Literal, Optional

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...constant import WORKING_DIR
from .database_metadata import load_metadata, to_prompt_context

logger = logging.getLogger(__name__)

# Get the prompt template directory
_PROMPT_DIR = Path(__file__).parent.parent 


def _get_workspace_md_dir() -> Path:
    """Get the workspace md files directory.

    Priority:
    1. WORKING_DIR ./md_files/zh
    2. Default package md_files/zh

    Returns:
        Path to the md files directory
    """
    # Check workspace directory first
    workspace_md_dir = WORKING_DIR 
    if workspace_md_dir.exists() and workspace_md_dir.is_dir():
        return workspace_md_dir

    # Fallback to package default directory
    return _PROMPT_DIR


def _load_prompt_template(template_name: str) -> str:
    """Load prompt template from markdown file.

    Args:
        template_name: Name of the template file (without .md extension)

    Returns:
        Template content as string
    """
    md_dir = _get_workspace_md_dir()
    template_path = md_dir / f"{template_name}.md"

    if template_path.exists():
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(
                "Failed to load prompt template %s: %s, using fallback",
                template_name,
                e,
            )

    # Return inline fallback template
    return _get_fallback_template()


def _load_schema_context_template() -> str:
    """Load schema context template from markdown file.

    Returns:
        Schema context template content
    """
    md_dir = _get_workspace_md_dir()
    template_path = md_dir / "sql_schema_context.md"

    if template_path.exists():
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(
                "Failed to load schema context template: %s, using fallback",
                e,
            )

    # Return inline fallback
    return _get_fallback_schema_context()


def _get_fallback_template() -> str:
    """Get inline fallback template."""
    return """你是一个SQL专家。根据以下数据库表结构，将用户问题转换为SQL查询。

{schema_context}

## 用户问题
{question}

## 要求
1. 只生成 SELECT 查询语句，不要生成 INSERT/UPDATE/DELETE
2. 使用标准SQL语法
3. 如果涉及日期筛选，使用适当的日期函数
4. 如果需要排序，使用 ORDER BY
5. 如果需要限制结果数，使用 LIMIT
6. 只返回SQL语句，不要包含任何解释或说明

## SQL查询
"""


def _get_fallback_schema_context() -> str:
    """Get inline fallback schema context."""
    return """## 数据库表结构

{schema_context}"""

# Fallback mock data for when database is not configured
FALLBACK_MOCK_METADATA = """Database: sales_db

### Table: orders
Comment: 订单主表
Columns:
  - id: bigint NOT NULL AUTO_INCREMENT [PRI] -- 订单ID
  - order_no: varchar(64) -- 订单编号
  - customer_id: bigint -- 客户ID
  - customer_name: varchar(128) -- 客户名称
  - total_amount: decimal(12,2) -- 订单总金额
  - status: varchar(32) -- 订单状态
  - created_at: datetime -- 创建时间
  - updated_at: datetime -- 更新时间

### Table: order_items
Comment: 订单明细表
Columns:
  - id: bigint NOT NULL AUTO_INCREMENT [PRI] -- 明细ID
  - order_id: bigint -- 订单ID
  - product_id: bigint -- 商品ID
  - product_name: varchar(256) -- 商品名称
  - quantity: int -- 数量
  - unit_price: decimal(10,2) -- 单价
  - subtotal: decimal(12,2) -- 小计金额

### Table: products
Comment: 商品表
Columns:
  - id: bigint NOT NULL AUTO_INCREMENT [PRI] -- 商品ID
  - name: varchar(256) -- 商品名称
  - category: varchar(64) -- 商品分类
  - price: decimal(10,2) -- 价格
  - stock: int -- 库存数量

### Table: customers
Comment: 客户表
Columns:
  - id: bigint NOT NULL AUTO_INCREMENT [PRI] -- 客户ID
  - name: varchar(128) -- 客户名称
  - phone: varchar(32) -- 联系电话
  - address: varchar(512) -- 地址
  - registered_at: datetime -- 注册时间
"""


def _call_llm_for_sql(prompt: str) -> Optional[str]:
    """Call LLM to generate SQL from prompt.

    This is a placeholder that attempts to use the model's chat capability.
    In a full implementation, this would integrate with the model's API.

    Args:
        prompt: Formatted prompt with schema and question

    Returns:
        Generated SQL string or None
    """
    try:
        # Try to import and use the model's chat functionality
        # This is implementation-dependent based on how the project
        # accesses the LLM
        from ..model_factory import get_model_client

        model_client = get_model_client()
        if model_client is None:
            return None

        response = model_client.chat(
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=30,
        )

        if response and hasattr(response, "text"):
            return response.text
        elif isinstance(response, dict):
            return response.get("text") or response.get("content")
        return None

    except Exception as e:
        logger.warning("Failed to call LLM for SQL generation: %s", e)
        return None


def _extract_sql(response_text: str) -> Optional[str]:
    """Extract SQL from LLM response text.

    Handles cases where the LLM wraps SQL in code blocks or adds explanations.

    Args:
        response_text: Raw response from LLM

    Returns:
        Extracted SQL or None
    """
    if not response_text:
        return None

    # Remove markdown code blocks
    sql = response_text.strip()

    # Check if it's in a code block
    code_block_match = re.search(
        r"```(?:sql)?\s*\n?(.*?)\n?```",
        sql,
        re.DOTALL | re.IGNORECASE,
    )
    if code_block_match:
        sql = code_block_match.group(1).strip()

    # Remove any leading explanations (lines before the actual SQL)
    # Look for the first line that looks like a SQL statement
    lines = sql.split("\n")
    sql_lines = []
    in_sql = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with SQL keywords
        if re.match(
            r"^\s*(SELECT|WITH|EXPLAIN| SHOW)",
            line,
            re.IGNORECASE,
        ):
            in_sql = True

        if in_sql:
            sql_lines.append(line)

    if sql_lines:
        return "\n".join(sql_lines).strip()

    # If no SQL pattern found, just return the whole thing if it's short
    if len(lines) <= 3 and len(sql) < 500:
        return sql

    return None


def generate_sql(
    question: str,
    database: Literal["mysql", "doris"] = "mysql",
    require_approval: bool = True,
) -> ToolResponse:
    """Generate SQL query from natural language question.

    This tool takes a user's natural language question and generates
    a SQL query based on the database schema.

    Args:
        question: User's natural language question about the data
        database: Database type - "mysql" or "doris". Defaults to "mysql"
        require_approval: Whether the generated SQL requires user approval
            before execution. Defaults to True.

    Returns:
        ToolResponse containing the generated SQL or error message
    """
    if not question or not question.strip():
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: Question cannot be empty. "
                    "Please provide a natural language question about your data.",
                )
            ],
        )

    try:
        # Load database metadata
        try:
            metadata = load_metadata(database=database, use_cache=True)
            schema_context = to_prompt_context(metadata, include_columns=True)
        except Exception as e:
            logger.warning("Failed to load real metadata: %s, using fallback", e)
            # Use fallback mock metadata for demo/testing
            schema_context = FALLBACK_MOCK_METADATA

        # Build prompt - load template from md file
        # Step 1: Load schema context template and fill in actual metadata
        schema_template = _load_schema_context_template()
        schema_filled = schema_template.format(schema_context=schema_context)

        # Step 2: Load main prompt template and combine with schema context
        prompt_template = _load_prompt_template("sql_generation")
        prompt = prompt_template.format(
            schema_context=schema_filled,
            question=question.strip(),
        )

        # Call LLM to generate SQL
        llm_response = _call_llm_for_sql(prompt)

        if llm_response:
            sql = _extract_sql(llm_response)
            if sql:
                approval_note = (
                    "\n\n[Note: This SQL requires approval before execution due to "
                    "require_approval=True. Use execute_sql tool to run it after approval.]"
                    if require_approval
                    else ""
                )
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Generated SQL:\n\n{sql}{approval_note}",
                        )
                    ],
                )

        # Fallback: try to generate a simple SQL based on keywords
        sql = _generate_simple_sql(question)
        if sql:
            approval_note = (
                "\n\n[Note: This SQL requires approval before execution.]"
                if require_approval
                else ""
            )
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Generated SQL (based on keyword analysis):\n\n{sql}{approval_note}",
                    )
                ],
            )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: Failed to generate SQL from the given question. "
                    "Please try rephrasing your question or ensure the database "
                    "metadata is properly configured.",
                )
            ],
        )

    except Exception as e:
        logger.error("Error generating SQL: %s", e)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Error generating SQL: {e}")],
        )


def _generate_simple_sql(question: str) -> Optional[str]:
    """Generate simple SQL based on keyword matching.

    This is a fallback for when LLM is not available. It performs
    simple keyword-based SQL generation.

    Args:
        question: User question

    Returns:
        Generated SQL or None
    """
    q = question.lower()

    # Simple keyword patterns
    if "销售" in q or "订单" in q or "订单" in q:
        if "每天" in q or "日" in q or "day" in q:
            return (
                "SELECT DATE(created_at) as date, COUNT(*) as order_count, "
                "SUM(total_amount) as total_amount "
                "FROM orders "
                "GROUP BY DATE(created_at) "
                "ORDER BY date DESC "
                "LIMIT 30"
            )
        elif "每月" in q or "月" in q or "month" in q:
            return (
                "SELECT DATE_FORMAT(created_at, '%Y-%m') as month, "
                "COUNT(*) as order_count, SUM(total_amount) as total_amount "
                "FROM orders "
                "GROUP BY DATE_FORMAT(created_at, '%Y-%m') "
                "ORDER BY month DESC "
                "LIMIT 12"
            )
        elif "客户" in q:
            return (
                "SELECT customer_id, customer_name, COUNT(*) as order_count, "
                "SUM(total_amount) as total_amount "
                "FROM orders "
                "GROUP BY customer_id, customer_name "
                "ORDER BY total_amount DESC "
                "LIMIT 20"
            )
        elif "产品" in q or "商品" in q:
            return (
                "SELECT p.id, p.name, p.category, p.price, "
                "COUNT(oi.id) as sales_count, SUM(oi.subtotal) as total_sales "
                "FROM products p "
                "LEFT JOIN order_items oi ON p.id = oi.product_id "
                "GROUP BY p.id, p.name, p.category, p.price "
                "ORDER BY total_sales DESC "
                "LIMIT 20"
            )
        else:
            return (
                "SELECT * FROM orders ORDER BY created_at DESC LIMIT 100"
            )

    if "用户" in q or "会员" in q:
        return (
            "SELECT * FROM customers ORDER BY registered_at DESC LIMIT 100"
        )

    if "产品" in q or "商品" in q:
        return (
            "SELECT * FROM products ORDER BY id LIMIT 100"
        )

    # Default: return a simple select from orders
    if any(keyword in q for keyword in ["查询", "查看", "获取", "select", "get", "list"]):
        return "SELECT * FROM orders ORDER BY created_at DESC LIMIT 100"

    return None
