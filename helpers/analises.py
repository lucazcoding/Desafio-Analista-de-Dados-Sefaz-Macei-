import duckdb
import pandas as pd
from pathlib import Path
import logging

def conectar_duckdb(caminho_db: str | Path) -> duckdb.DuckDBPyConnection:
    """Conecta ao banco DuckDB existente."""
    return duckdb.connect(str(caminho_db))

def analise_ranking_execucao(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    1 - Ranking de Execução em Educação
    Objetivo: Quem paga proporcionalmente mais do que empenha?
    Regras: Agrupa anos de 2020 a 2024 (ignora 2025 incompleto)
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
          AND Conta LIKE '12 %' -- Filtra apenas Educação
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

def analise_per_capita(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    2 - Gasto Per Capita em Educação
    Objetivo: Quem investe mais por habitante?
    Regras: Filtramos o ano de 2024, pois a população muda a cada ano e queremos
            uma foto do ano completo mais recente.
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

def analise_evolucao_maceio(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    3 - Evolução Temporal (Maceió vs Média das Capitais) em Educação
    Objetivo: Maceió está melhorando a sua taxa de execução ao longo do tempo?
    Regras: Linha do tempo de 2020 a 2024.
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
        -- Maceió
        SUM(CASE WHEN Instituição LIKE '%Maceió%' THEN Pago ELSE 0 END) / 
        NULLIF(SUM(CASE WHEN Instituição LIKE '%Maceió%' THEN Empenhado ELSE 0 END), 0) * 100 as Taxa_Maceio,
        
        -- Média das Outras Capitais
        SUM(CASE WHEN Instituição NOT LIKE '%Maceió%' THEN Pago ELSE 0 END) / 
        NULLIF(SUM(CASE WHEN Instituição NOT LIKE '%Maceió%' THEN Empenhado ELSE 0 END), 0) * 100 as Taxa_Media_Outras
    FROM base_ano
    GROUP BY Ano
    ORDER BY Ano
    """
    return con.execute(query).df()

def analise_composicao_subfuncoes(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    4 - Composição de Subfunções da Educação
    Objetivo: Onde o dinheiro está concentrado (Ensino Fundamental, Infantil, etc)?
    Regras: Filtra ano de 2024, ContaTipo in (Subfunção, Subfuncao_agregada)
    """
    query = """
    WITH totais AS (
        SELECT 
            Conta,
            SUM(Valor) as Pago_Total
        FROM despesas_finbra
        WHERE ContaTipo IN ('Subfunção', 'Subfuncao_agregada')
          -- Busca subfunções da Educação (ex: 12.361) e a Agregada (FU12)
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

if __name__ == "__main__":
    # Teste local das análises
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    pd.options.display.float_format = '{:,.2f}'.format
    
    diretorio_atual = Path(__file__).parent.parent
    caminho_db = diretorio_atual / "finbra.duckdb"
    
    try:
        con = conectar_duckdb(caminho_db)
        
        logging.info("\n" + "="*70)
        logging.info("1. RANKING DE EXECUÇÃO EM EDUCAÇÃO (2020-2024) - TOP 5")
        logging.info("="*70)
        df1 = analise_ranking_execucao(con)
        print(df1.head(5).to_string(index=False))
        
        logging.info("\n" + "="*70)
        logging.info("2. GASTO PER CAPITA EM EDUCAÇÃO (2024) - TOP 5")
        logging.info("="*70)
        df2 = analise_per_capita(con)
        print(df2.head(5).to_string(index=False))
        
        logging.info("\n" + "="*70)
        logging.info("3. EVOLUÇÃO TAXA DE EXECUÇÃO (MACEIÓ vs MÉDIA OUTRAS CAPITAIS)")
        logging.info("="*70)
        df3 = analise_evolucao_maceio(con)
        print(df3.to_string(index=False))
        
        logging.info("\n" + "="*70)
        logging.info("4. ONDE VAI O DINHEIRO DA EDUCAÇÃO? (SUBFUNÇÕES - 2024)")
        logging.info("="*70)
        df4 = analise_composicao_subfuncoes(con)
        print(df4.to_string(index=False))
        
        con.close()
    except Exception as e:
        logging.error(f"Erro ao executar análises: {e}")
