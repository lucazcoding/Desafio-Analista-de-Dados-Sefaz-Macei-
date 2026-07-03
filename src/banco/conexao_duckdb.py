import duckdb
import logging
from pathlib import Path


def conectar(caminho_db: str | Path) -> duckdb.DuckDBPyConnection:
    """Conecta ao banco DuckDB existente ou cria um novo."""
    return duckdb.connect(str(caminho_db))
