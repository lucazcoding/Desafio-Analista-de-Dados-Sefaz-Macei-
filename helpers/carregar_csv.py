import pandas as pd
from pathlib import Path
import logging

def carregar_csv_finbra(caminho_csv: str | Path) -> pd.DataFrame:
    """
    Lê o arquivo CSV do FINBRA com as particularidades de formatação:
    - Encoding: latin-1 (ISO-8859-1)
    - Separador: ';'
    - Pula as 3 primeiras linhas (metadados)
    - Decimais separados por vírgula ','
    
    Args:
        caminho_csv: Caminho para o arquivo CSV.
        
    Returns:
        DataFrame contendo os dados brutos lidos do CSV.
    """
    caminho = Path(caminho_csv)
    
    try:
        # A leitura do CSV com o pandas tratando as particularidades
        df = pd.read_csv(
            caminho,
            sep=";",
            skiprows=3,
            encoding="latin-1",
            decimal=",",
            # thousand="." pode ser útil se o valor usar ponto para milhares,
            # mas no Siconfi geralmente os números vem diretos sem milhar (ex: 874885274,98).
            # Mas não custa precaver (embora as vezes no pandas cause bugs se houver mistura).
        )
        
        # Limpar espaços em branco que possam vir nos nomes das colunas
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo CSV '{caminho}': {e}")
        raise

if __name__ == "__main__":
    # Teste simples
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Pegar o primeiro csv extraído para teste
    caminhos_csv = list(Path("dados_extraidos").rglob("*.csv"))
    
    if caminhos_csv:
        caminho_teste = caminhos_csv[0]
        logging.info(f"Testando a leitura do arquivo: {caminho_teste}")
        
        df_teste = carregar_csv_finbra(caminho_teste)
        logging.info(f"Formato do DataFrame (linhas, colunas): {df_teste.shape}")
        logging.info(f"Colunas: {list(df_teste.columns)}")
        logging.info(f"Primeiras 3 linhas da coluna Valor:\n{df_teste['Valor'].head(3)}")
        logging.info(f"Tipo da coluna Valor: {df_teste['Valor'].dtype}")
    else:
        logging.warning("Nenhum CSV encontrado em 'dados_extraidos' para testar.")
