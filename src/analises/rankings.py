import duckdb
import pandas as pd


def ranking_geral(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Ranking Geral de Eficiência de Execução Orçamentária (2020-2024).

    Calcula a taxa de execução ponderada de cada capital considerando
    todas as funções juntas (Σ Pago / Σ Empenhado × 100).

    Retorna DataFrame com 26 capitais ordenado por Taxa_Geral decrescente.
    """
    query = """
    WITH base AS (
        SELECT
            Instituição,
            UF,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) as Pago_Total,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) as Empenhado_Total
        FROM despesas_finbra
        WHERE ContaTipo = 'Função'
          AND Ano <= 2024
        GROUP BY Instituição, UF
    )
    SELECT
        Instituição,
        UF,
        Pago_Total,
        Empenhado_Total,
        CASE WHEN Empenhado_Total > 0
             THEN ROUND((Pago_Total / Empenhado_Total) * 100, 2)
             ELSE 0
        END as Taxa_Geral
    FROM base
    ORDER BY Taxa_Geral DESC
    """
    return con.execute(query).df()
