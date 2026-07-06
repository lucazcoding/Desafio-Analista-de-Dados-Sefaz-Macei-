import duckdb
import pandas as pd


def restos_a_pagar(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Análise de Restos a Pagar por Capital (2020-2024).

    Calcula a proporção de despesas empenhadas que foram inscritas
    como Restos a Pagar (Não Processados e Processados) em vez de
    quitadas dentro do mesmo exercício.

    Retorna DataFrame ordenado por Pct_Total_RP decrescente.
    """
    query = """
    WITH base AS (
        SELECT
            Instituição,
            UF,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) as Empenhado,
            SUM(CASE WHEN Coluna = 'Inscrição de Restos a Pagar Não Processados' THEN Valor ELSE 0 END) as RPNP,
            SUM(CASE WHEN Coluna = 'Inscrição de Restos a Pagar Processados' THEN Valor ELSE 0 END) as RPP
        FROM despesas_finbra
        WHERE ContaTipo = 'Função'
          AND Ano BETWEEN 2020 AND 2024
        GROUP BY Instituição, UF
    )
    SELECT
        Instituição,
        UF,
        Empenhado,
        RPNP,
        RPP,
        RPNP + RPP as Total_RP,
        CASE WHEN Empenhado > 0 THEN ROUND(RPNP / Empenhado * 100, 2) ELSE 0 END as Pct_RPNP,
        CASE WHEN Empenhado > 0 THEN ROUND(RPP / Empenhado * 100, 2) ELSE 0 END as Pct_RPP,
        CASE WHEN Empenhado > 0 THEN ROUND((RPNP + RPP) / Empenhado * 100, 2) ELSE 0 END as Pct_Total_RP
    FROM base
    WHERE Empenhado > 0
    ORDER BY Pct_Total_RP DESC
    """
    return con.execute(query).df()
