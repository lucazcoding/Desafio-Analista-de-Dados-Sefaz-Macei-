import pandas as pd
import duckdb
import logging
import time
from pathlib import Path

def salvar_em_parquet(df: pd.DataFrame, caminho_arquivo: str | Path) -> None:
    """
    Salva o DataFrame consolidado no formato colunar Parquet, 
    que é extremamente otimizado para leitura.
    """
    inicio = time.time()
    
    Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
    
    # Salva o arquivo usando a engine do pyarrow
    df.to_parquet(caminho_arquivo, engine='pyarrow', index=False)
    
    fim = time.time()
    logging.info(f"Base de dados salva em Parquet com sucesso: '{caminho_arquivo}'")
    logging.info(f"Tempo de execução (Salvar Parquet): {fim - inicio:.4f} segundos")

def criar_banco_duckdb(caminho_parquet: str | Path, caminho_db: str | Path = "finbra.duckdb") -> duckdb.DuckDBPyConnection:
    """
    Cria ou conecta a um banco DuckDB e cria uma View 
    que consome os dados direto do arquivo Parquet de forma veloz.
    """
    inicio = time.time()
    
    # Conecta no arquivo duckdb local (isso permite persistência das views)
    con = duckdb.connect(str(caminho_db))
    
    # Cria uma View em SQL lendo diretamente o parquet. 
    # Com isso o DuckDB nem carrega tudo na RAM, ele lê sob demanda.
    con.execute(f"CREATE OR REPLACE VIEW despesas_finbra AS SELECT * FROM read_parquet('{caminho_parquet}')")
    
    fim = time.time()
    logging.info(f"Banco DuckDB atualizado com a tabela 'despesas_finbra' apontando para o Parquet.")
    logging.info(f"Tempo de conexão/criação view (DuckDB): {fim - inicio:.4f} segundos")
    
    return con

if __name__ == "__main__":
    # Teste de execução local do helper
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    import sys
    # Garante importação do modulo local
    diretorio_atual = Path(__file__).parent.parent
    sys.path.append(str(diretorio_atual))
    
    from helpers.consolidar_dataframe import consolidar_todos_os_csvs
    
    pasta_extraidos = diretorio_atual / "dados_extraidos"
    caminho_parquet = pasta_extraidos / "finbra_consolidado.parquet"
    caminho_db = diretorio_atual / "finbra.duckdb" # banco ficará na raiz
    
    logging.info("Carregando base consolidada em memória para iniciar persistência...")
    df_consolidado = consolidar_todos_os_csvs(pasta_extraidos)
    
    if not df_consolidado.empty:
        logging.info("\n--- ETAPA 1: SALVAR PARQUET ---")
        salvar_em_parquet(df_consolidado, caminho_parquet)
        
        logging.info("\n--- ETAPA 2: CONFIGURAR DUCKDB ---")
        con = criar_banco_duckdb(caminho_parquet, caminho_db)
        
        logging.info("\n--- TESTE DE CONSULTA SQL ---")
        inicio_sql = time.time()
        
        # Testamos um SELECT básico que agrupa e conta linhas por ano
        df_resultado_sql = con.execute("SELECT Ano, COUNT(*) as qtd_linhas FROM despesas_finbra GROUP BY Ano ORDER BY Ano").df()
        
        fim_sql = time.time()
        
        print("\nResultado da Query:")
        print(df_resultado_sql.to_string(index=False))
        logging.info(f"Tempo de execução da Query SQL (DuckDB): {fim_sql - inicio_sql:.4f} segundos")
        
        con.close()
