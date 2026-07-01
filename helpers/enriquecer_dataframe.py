import pandas as pd
import re
import logging

def classificar_conta(conta: str) -> str:
    """
    Classifica a string da Conta no seu respectivo tipo, conforme as regras da Sefaz:
    - Função (ex: '10 - Saúde')
    - Subfunção (ex: '10.301 - Atenção Básica')
    - Subfuncao_agregada (ex: 'FU10 - Demais Subfunções')
    - Total_Geral (ex: 'Despesas Exceto Intraorçamentárias')
    """
    if not isinstance(conta, str):
        return 'Desconhecido'
        
    conta = conta.strip()
    
    # Verifica se é um Total Geral
    if conta in ['Despesas Exceto Intraorçamentárias', 'Despesas Intraorçamentárias']:
        return 'Total_Geral'
        
    # Verifica Subfunção: formato DD.DDD - Texto (ex: 10.301 - Atenção Básica)
    if re.match(r"^\d{2}\.\d{3}\s*-", conta):
        return 'Subfunção'
        
    # Verifica Função: formato DD - Texto (ex: 10 - Saúde)
    if re.match(r"^\d{2}\s*-", conta):
        return 'Função'
        
    # Verifica Subfuncao_agregada: formato FUDD - Texto (ex: FU10 - Demais Subfunções)
    if re.match(r"^FU\d{2}\s*-", conta):
        return 'Subfuncao_agregada'
        
    return 'Outros'

def enriquecer_dados_finbra(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    """
    Enriquece o DataFrame bruto do Finbra:
    1. Adiciona a coluna 'Ano'.
    2. Adiciona a coluna 'ContaTipo' baseada na classificação da coluna 'Conta'.
    3. Garante que a coluna 'Valor' seja numérica.
    """
    # Opera em uma cópia para não alterar o DataFrame original acidentalmente
    df_enriquecido = df.copy()
    
    # 1. Adicionar o Ano
    df_enriquecido['Ano'] = ano
    
    # 2. Garantir que 'Valor' é estritamente numérico (força conversão e lida com problemas)
    if 'Valor' in df_enriquecido.columns:
        # errors='coerce' converte dados inválidos em NaN
        df_enriquecido['Valor'] = pd.to_numeric(df_enriquecido['Valor'], errors='coerce')
        
    # 3. Classificar a Conta criando a coluna 'ContaTipo'
    if 'Conta' in df_enriquecido.columns:
        df_enriquecido['ContaTipo'] = df_enriquecido['Conta'].apply(classificar_conta)
        
    return df_enriquecido

if __name__ == "__main__":
    # Configuração de log para o teste
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Teste rápido simulando o DataFrame para validar a classificação Regex
    df_teste = pd.DataFrame({
        'Conta': [
            '10 - Saúde', 
            '10.301 - Atenção Básica', 
            'FU10 - Demais Subfunções', 
            'Despesas Exceto Intraorçamentárias',
            'Despesas Intraorçamentárias',
            '12 - Educação',
            '12.361 - Ensino Fundamental',
            'Conta Desconhecida Teste'
        ],
        'Valor': ['1000', '200', '50.5', '10000', '0', '3000', '1500', 'abc'] # abc deve virar NaN
    })
    
    logging.info("Testando enriquecimento de dados...")
    df_resultado = enriquecer_dados_finbra(df_teste, 2022)
    
    logging.info("\nDataFrame Enriquecido Final:\n")
    # Imprime com as colunas relevantes para o teste
    print(df_resultado[['Ano', 'Conta', 'ContaTipo', 'Valor']].to_string(index=False))
