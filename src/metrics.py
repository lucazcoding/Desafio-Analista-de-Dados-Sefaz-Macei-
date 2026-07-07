import pandas as pd


def calcular_ranking_saude(con, nome_tabela: str = "despesas_finbra") -> pd.DataFrame:
    """Calcula o ranking de execução orçamentária para a função Saúde (2020-2024).

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame ordenado contendo as colunas: Capital, Empenhado, Pago,
        Taxa_Execucao (formatado em %).
    """
    query = f"""
    SELECT
        TRIM(
        regexp_extract(
            Instituição,
            'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]',
            1
        )
    ) AS Capital,

        SUM(CASE
            WHEN Coluna = 'Despesas Empenhadas'
            THEN Valor ELSE 0
        END) AS Empenhado,

        SUM(CASE
            WHEN Coluna = 'Despesas Pagas'
            THEN Valor ELSE 0
        END) AS Pago,

        ROUND(
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END)
            /
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END)
            * 100,
            2
        ) AS Taxa_Execucao

    FROM {nome_tabela}

    WHERE ContaTipo = 'Função'
      AND Conta = '10 - Saúde'
      AND Ano BETWEEN 2020 AND 2024

    GROUP BY Capital

    ORDER BY Taxa_Execucao DESC

    LIMIT 27
    """
    df = con.execute(query).df()
    df["Taxa_Execucao"] = df["Taxa_Execucao"].map(lambda x: f"{x:.2f}%")
    return df


def calcular_ranking_educacao(
    con, nome_tabela: str = "despesas_finbra"
) -> pd.DataFrame:
    """Calcula o ranking de execução orçamentária para a função Educação (2020-2024).

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame ordenado contendo as colunas: Capital, Empenhado, Pago,
        Taxa_Execucao (formatado em %).
    """
    query = f"""
    SELECT
        TRIM(
        regexp_extract(
            Instituição,
            'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]',
            1
        )
    ) AS Capital,

        SUM(CASE
            WHEN Coluna = 'Despesas Empenhadas'
            THEN Valor ELSE 0
        END) AS Empenhado,

        SUM(CASE
            WHEN Coluna = 'Despesas Pagas'
            THEN Valor ELSE 0
        END) AS Pago,

        ROUND(
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END)
            /
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END)
            * 100,
            2
        ) AS Taxa_Execucao

    FROM {nome_tabela}

    WHERE ContaTipo = 'Função'
      AND Conta = '12 - Educação'
      AND Ano BETWEEN 2020 AND 2024

    GROUP BY Capital

    ORDER BY Taxa_Execucao DESC

    LIMIT 27
    """
    df = con.execute(query).df()
    df["Taxa_Execucao"] = df["Taxa_Execucao"].map(lambda x: f"{x:.2f}%")
    return df


def calcular_execucao_natal_por_funcao(
    con, nome_tabela: str = "despesas_finbra"
) -> pd.DataFrame:
    """Calcula as taxas de execução orçamentária de Natal por função (2020-2024).

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame ordenado decrescentemente por taxa de execução.
    """
    query = f"""
    SELECT
        Conta AS Funcao,
        SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) AS Pago,
        SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) AS Empenhado,
        CASE 
            WHEN SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) > 0
            THEN 
                (SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END)
                /
                SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END)) * 100
            ELSE NULL
        END AS Taxa_Execucao
    FROM {nome_tabela}
    WHERE ContaTipo = 'Função'
      AND Ano BETWEEN 2020 AND 2024
      AND TRIM(
            regexp_extract(
                Instituição,
                'Prefeitura Municipal d[aeo]\\s*(.*?)\\s*[-–]',
                1
            )
          ) = 'Natal'
    GROUP BY Conta
    ORDER BY Taxa_Execucao DESC;
    """
    df = con.execute(query).df()
    df["Taxa_Execucao"] = df["Taxa_Execucao"].map(lambda x: f"{x:.2f}%")
    return df


def calcular_comparacao_natal_media(
    con, nome_tabela: str = "despesas_finbra"
) -> pd.DataFrame:
    """Calcula a diferença da taxa de execução de Natal vs. média das capitais (2020-2024).

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame com as colunas: Funcao, Capital, Taxa_Execucao_Natal,
        Media_Capitais, Diferenca.
    """
    query = f"""
    WITH base AS (
        SELECT
            TRIM(
                regexp_extract(Instituição, 'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]', 1)
            ) AS Capital,
            Conta AS Funcao,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) AS Empenhado,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) AS Pago
        FROM {nome_tabela}
        WHERE ContaTipo = 'Função'
          AND Ano BETWEEN 2020 AND 2024
        GROUP BY Capital, Funcao
    ),
    taxas AS (
        SELECT
            Capital,
            Funcao,
            Empenhado,
            Pago,
            CASE 
                WHEN Empenhado > 0 THEN (Pago / Empenhado) * 100
                ELSE NULL
            END AS Taxa_Execucao
        FROM base
    ),
    media_capitais AS (
        SELECT
            Funcao,
            AVG(Taxa_Execucao) AS Media_Funcao
        FROM taxas
        GROUP BY Funcao
    )
    SELECT
        t.Funcao,
        t.Capital,
        ROUND(t.Taxa_Execucao, 2) AS Taxa_Execucao_Natal,
        ROUND(m.Media_Funcao, 2) AS Media_Capitais,
        ROUND(t.Taxa_Execucao - m.Media_Funcao, 2) AS Diferenca
    FROM taxas t
    JOIN media_capitais m
        ON t.Funcao = m.Funcao
    WHERE t.Capital = 'Natal'
    ORDER BY Diferenca ASC;
    """
    return con.execute(query).df()


def calcular_subfuncoes_natal(
    con, nome_tabela: str = "despesas_finbra"
) -> pd.DataFrame:
    """Calcula a taxa de execução das subfunções de Natal (2020-2024).

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame ordenado de forma ascendente pela taxa de execução.
    """
    query = f"""
    WITH base AS (
        SELECT
            TRIM(regexp_extract(Instituição, 'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]', 1)) AS Capital,
            Conta AS Subfuncao,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) AS Empenhado,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) AS Pago
        FROM {nome_tabela}
        WHERE ContaTipo = 'Subfunção'
          AND Ano BETWEEN 2020 AND 2024
          AND TRIM(regexp_extract(Instituição, 'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]', 1)) = 'Natal'
        GROUP BY Capital, Subfuncao
    ),
    taxas AS (
        SELECT
            Capital,
            Subfuncao,
            Empenhado,
            Pago,
            CASE 
                WHEN Empenhado > 0 THEN (Pago / Empenhado) * 100
                ELSE NULL
            END AS Taxa_Execucao
        FROM base
    )
    SELECT
        Capital,
        Subfuncao,
        Empenhado,
        Pago,
        ROUND(Taxa_Execucao, 2) AS Taxa_Execucao
    FROM taxas
    ORDER BY Taxa_Execucao ASC;
    """
    return con.execute(query).df()


def calcular_taxa_funcoes_criticas(
    con, nome_tabela: str = "despesas_finbra"
) -> pd.DataFrame:
    """Calcula a taxa de execução orçamentária de Habitação e Urbanismo de todas as capitais.

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame ordenado por Função e Taxa_Execucao.
    """
    query = f"""
    WITH base AS (
        SELECT
            TRIM(
                regexp_extract(Instituição, 'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]', 1)
            ) AS Capital,
            Conta AS Funcao,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) AS Empenhado,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) AS Pago
        FROM {nome_tabela}
        WHERE ContaTipo = 'Função'
          AND Ano BETWEEN 2020 AND 2024
          AND Conta IN (
              '16 - Habitação',
              '15 - Urbanismo'
          )
        GROUP BY Capital, Funcao
    ),
    taxas AS (
        SELECT
            Capital,
            Funcao,
            Empenhado,
            Pago,
            CASE 
                WHEN Empenhado > 0 THEN (Pago / Empenhado) * 100
                ELSE NULL
            END AS Taxa_Execucao
        FROM base
    )
    SELECT
        Capital,
        Funcao,
        ROUND(Empenhado, 2) AS Empenhado,
        ROUND(Pago, 2) AS Pago,
        ROUND(Taxa_Execucao, 2) AS Taxa_Execucao
    FROM taxas
    ORDER BY Funcao, Taxa_Execucao ASC;
    """
    return con.execute(query).df()


def calcular_resumo_estatistico_critico(
    con, nome_tabela: str = "despesas_finbra"
) -> pd.DataFrame:
    """Calcula resumo estatístico (média, mínimo e máximo) para Habitação e Urbanismo.

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame contendo: Funcao, Media_Nacional, Min_Taxa, Max_Taxa.
    """
    query = f"""
    WITH base AS (
        SELECT
            TRIM(
                regexp_extract(Instituição, 'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]', 1)
            ) AS Capital,
            Conta AS Funcao,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) AS Empenhado,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) AS Pago
        FROM {nome_tabela}
        WHERE ContaTipo = 'Função'
          AND Ano BETWEEN 2020 AND 2024
          AND Conta IN ('16 - Habitação', '15 - Urbanismo')
        GROUP BY Capital, Funcao
    ),
    taxas AS (
        SELECT
            Capital,
            Funcao,
            (Pago / NULLIF(Empenhado, 0)) * 100 AS Taxa_Execucao
        FROM base
    )
    SELECT
        Funcao,
        ROUND(AVG(Taxa_Execucao), 2) AS Media_Nacional,
        ROUND(MIN(Taxa_Execucao), 2) AS Min_Taxa,
        ROUND(MAX(Taxa_Execucao), 2) AS Max_Taxa
    FROM taxas
    GROUP BY Funcao
    ORDER BY Media_Nacional ASC;
    """
    return con.execute(query).df()


def calcular_ranking_funcoes_criticas(
    con, nome_tabela: str = "despesas_finbra"
) -> pd.DataFrame:
    """Calcula o ranking de Urbanismo e Habitação, destacando as top 5 e Natal.

    Args:
        con: Conexão ativa com o DuckDB.
        nome_tabela: Nome da tabela no DuckDB. Padrão: 'despesas_finbra'.

    Returns:
        DataFrame filtrado contendo as top 5 capitais em execução orçamentária
        e a capital Natal, ordenado por Função e Rank_Funcao.
    """
    query = f"""
    WITH base AS (
        SELECT
            TRIM(
                regexp_extract(Instituição, 'Prefeitura Municipal d[eo]\\s*(.*?)\\s*[-–]', 1)
            ) AS Capital,
            Conta AS Funcao,
            SUM(CASE WHEN Coluna = 'Despesas Empenhadas' THEN Valor ELSE 0 END) AS Empenhado,
            SUM(CASE WHEN Coluna = 'Despesas Pagas' THEN Valor ELSE 0 END) AS Pago
        FROM {nome_tabela}
        WHERE ContaTipo = 'Função'
          AND Ano BETWEEN 2020 AND 2024
          AND Conta IN ('15 - Urbanismo', '16 - Habitação')
        GROUP BY Capital, Funcao
    ),
    taxas AS (
        SELECT
            Capital,
            Funcao,
            (Pago / NULLIF(Empenhado,0)) * 100 AS Taxa_Execucao
        FROM base
    ),
    ranking AS (
        SELECT
            Capital,
            Funcao,
            Taxa_Execucao,
            AVG(Taxa_Execucao) OVER (PARTITION BY Funcao) AS Media_Nacional,
            RANK() OVER (PARTITION BY Funcao ORDER BY Taxa_Execucao DESC) AS Rank_Funcao
        FROM taxas
    )
    SELECT *
    FROM ranking
    WHERE Capital IN ('Natal')
       OR Rank_Funcao <= 5
    ORDER BY Funcao, Rank_Funcao;
    """
    return con.execute(query).df()
