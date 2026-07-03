import duckdb
import pandas as pd


def evolucao_temporal(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Evolução Temporal — Maceió vs Média das Capitais (2020-2024).

    Analisa se Maceió está melhorando a taxa de execução ao longo do tempo.
    Retorna DataFrame com Taxa_Maceio e Taxa_Media_Outras por ano.
    """
    query = """
    WITH base_ano AS (
        SELECT
            Ano,
            Instituição,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) as Empenhado,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) as Pago
        FROM despesas_finbra
        WHERE ContaTipo = 'Função'
          AND Conta LIKE '12 %'
          AND Ano <= 2024
        GROUP BY Ano, Instituição
    )
    SELECT
        Ano,
        SUM(CASE WHEN Instituição LIKE '%Maceió%' THEN Pago ELSE 0 END) /
        NULLIF(SUM(CASE WHEN Instituição LIKE '%Maceió%' THEN Empenhado ELSE 0 END), 0) * 100 as Taxa_Maceio,
        SUM(CASE WHEN Instituição NOT LIKE '%Maceió%' THEN Pago ELSE 0 END) /
        NULLIF(SUM(CASE WHEN Instituição NOT LIKE '%Maceió%' THEN Empenhado ELSE 0 END), 0) * 100 as Taxa_Media_Outras
    FROM base_ano
    GROUP BY Ano
    ORDER BY Ano
    """
    return con.execute(query).df()
