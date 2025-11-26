import logging
from typing import Any, Dict, Generator, Tuple, Optional

import clickhouse_connect
import pymysql
from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from jinja2 import Template
from sqlglot import parse_one

from provider import dbquery
from tools.api import SQLType, typeOf

from pymysql.cursors import DictCursor

logger = logging.getLogger(__name__)
logger.addHandler(plugin_logger_handler)


class SqlQueryToolNode(Tool):
    def __init__(self, runtime, session):
        super().__init__(runtime, session)
        try:
            credentials = self.runtime.credentials or runtime.credentials
            self.db_config, config = dbquery.get_config(credentials)
            self.db_type = self.db_config.get("dbtype", "").lower()
            self.max_fetched_rows = config.get("max_fetched_rows", 100)
        except Exception as e:
            logger.error(f"Failed to initialize DB config: {e}")
            raise

    def _get_client(self):
        """根据 db_type 返回对应客户端"""
        if self.db_type == "clickhouse":
            return clickhouse_connect.get_client(
                host=self.db_config["host"],
                port=int(self.db_config["port"]),
                username=self.db_config["username"],
                password=self.db_config["password"],
                database=self.db_config["database"],
            )
        elif self.db_type == "mysql":
            return pymysql.connect(
                host=self.db_config["host"],
                port=int(self.db_config["port"]),
                user=self.db_config["username"],
                password=self.db_config["password"],
                database=self.db_config["database"],
                charset="utf8mb4",
                autocommit=True,
            )
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def _check_query(self, query: str, parameters: Dict) -> Tuple[SQLType, str]:
        if not query:
            raise ValueError("SQL query is required")

        # Step 1: Render Jinja2 template (e.g., {% if %} logic)
        if "{" in query:
            tpl = Template(query)
            query = tpl.render(parameters)

        # Step 2: Parse with sqlglot using correct dialect
        dialect = "clickhouse" if self.db_type == "clickhouse" else "mysql"
        try:
            ast = parse_one(query, dialect=dialect)
        except Exception as ex:
            raise ValueError(f"SQL syntax error in {dialect}: {ex}") from ex

        # Step 3: Re-generate normalized SQL
        normalized_sql = ast.sql(dialect=dialect)
        return typeOf(ast), normalized_sql

    def _invoke(
        self, parameters: Dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        raw_query: str = parameters.get("query")
        sql_type, final_sql = self._check_query(raw_query, parameters)

        if sql_type != SQLType.SELECT:
            raise ValueError(f"Only SELECT statements are supported. Got: {sql_type}")

        client = self._get_client()
        cursor = None

        try:
            if self.db_type == "clickhouse":
                # ClickHouse: use .query() with optional parameters (for {arg} style)
                # But since we already rendered Jinja, pass empty dict or original params
                result = client.query(final_sql, parameters)
                columns = result.column_names
                rows = result.result_rows[: self.max_fetched_rows]

            elif self.db_type == "mysql":
                cursor = client.cursor(pymysql.cursors.DictCursor)
                # For MySQL, we cannot safely parameterize full dynamic SQL after Jinja
                # So we execute the final SQL string directly (ensure Jinja inputs are safe!)
                cursor.execute(final_sql)
                raw_rows = cursor.fetchall()
                rows = [list(row.values()) for row in raw_rows]  # List of lists
                columns = list(raw_rows[0].keys()) if raw_rows else []

                # Trim to max rows
                rows = rows[: self.max_fetched_rows]

            else:
                raise RuntimeError("Unexpected DB type")

            logger.info(f"Executed {self.db_type.upper()} query: {final_sql}, rows={len(rows)}")

            # Yield structured output
            yield self.create_variable_message("data", rows)
            yield self.create_variable_message("columns", columns)
            data_dict = [dict(zip(columns, row)) for row in rows]
            yield self.create_json_message({"data": data_dict})

        except Exception as ex:
            logger.exception(f"Database query failed: {final_sql}, error={ex}")
            raise RuntimeError(f"{self.db_type.upper()} query error: {ex}") from ex

        finally:
            if cursor:
                cursor.close()
            if client:
                client.close()