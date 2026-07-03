import duckdb
import pandas as pd


def taxa_execucao(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Ranking de Execução em Educação (2020-2024).

    Compara as capitais pela capacidade de transformar empenhos em pagamentos.
    Retorna DataFrame ordenado por Taxa_Execucao decrescente.
    """
    query = """
    WITH base AS (
        SELECT
            Instituição,
            UF,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) as Empenhado,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) as Pago
        FROM despesas_finbra
        WHERE ContaTipo = 'Função'
          AND Conta LIKE '12 %'
          AND Ano <= 2024
        GROUP BY Instituição, UF
    )
    SELECT
        Instituição,
        UF,
        Empenhado,
        Pago,
        CASE WHEN Empenhado > 0 THEN (Pago / Empenhado) * 100 ELSE 0 END as Taxa_Execucao
    FROM base
    ORDER BY Taxa_Execucao DESC
    """
    return con.execute(query).df()
