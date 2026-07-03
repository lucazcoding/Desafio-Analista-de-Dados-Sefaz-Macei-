import duckdb
import pandas as pd


def composicao_subfuncoes(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Composição de Subfunções da Educação (2024).

    Detalha onde o dinheiro da educação foi aplicado (Ensino Fundamental,
    Infantil, etc). Retorna DataFrame com percentual de participação.
    """
    query = """
    WITH totais AS (
        SELECT
            Conta,
            SUM(Valor) as Pago_Total
        FROM despesas_finbra
        WHERE ContaTipo IN ('Subfunção', 'Subfuncao_agregada')
          AND (Conta LIKE '12.%' OR Conta LIKE 'FU12 %')
          AND Coluna = 'Despesas Pagas'
          AND Ano = 2024
        GROUP BY Conta
    )
    SELECT
        Conta,
        Pago_Total,
        Pago_Total / (SELECT SUM(Pago_Total) FROM totais) * 100 as Percentual_do_Total
    FROM totais
    ORDER BY Pago_Total DESC
    """
    return con.execute(query).df()
