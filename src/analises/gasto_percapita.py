import duckdb
import pandas as pd


def gasto_percapita(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Gasto Per Capita em Educação (2024).

    Compara o gasto público por habitante entre as capitais.
    Retorna DataFrame ordenado por Per_Capita decrescente.
    """
    query = """
    WITH base AS (
        SELECT
            Instituição,
            UF,
            MAX(População) as Populacao,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) as Pago
        FROM despesas_finbra
        WHERE ContaTipo = 'Função'
          AND Conta LIKE '12 %'
          AND Ano = 2024
        GROUP BY Instituição, UF
    )
    SELECT
        Instituição,
        UF,
        Populacao,
        Pago,
        Pago / Populacao as Per_Capita
    FROM base
    ORDER BY Per_Capita DESC
    """
    return con.execute(query).df()
