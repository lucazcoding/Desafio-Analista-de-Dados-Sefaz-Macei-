import logging
import time
from pathlib import Path

import duckdb


def criar_view_finbra(
    con: duckdb.DuckDBPyConnection,
    caminho_parquet: str | Path,
    nome_tabela: str = "despesas_finbra",
) -> None:
    """Cria ou substitui uma View no DuckDB apontando para o Parquet."""
    inicio = time.time()

    con.execute(
        f"CREATE OR REPLACE VIEW {nome_tabela} "
        f"AS SELECT * FROM read_parquet('{caminho_parquet}')"
    )

    fim = time.time()
    logging.info(f"View '{nome_tabela}' criada/atualizada no DuckDB.")
    logging.info(f"Tempo de criação da view: {fim - inicio:.4f} segundos")
