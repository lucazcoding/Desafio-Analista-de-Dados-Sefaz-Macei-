import re
from pathlib import Path
import pandas as pd


def classificar_conta(conta: str) -> str:
    """Classifica o nível de agregação da conta a partir do texto.

    Total_Geral:             'Despesas Exceto Intraorçamentárias'
    Função:                  '10 - Saúde'
    Subfunção:               '10.301 - Atenção Básica'
    Subfuncao_agregada:      'FU10 - Demais Subfunções'
    """
    if not isinstance(conta, str):
        return "Outros"

    conta = conta.strip()

    if conta in [
        "Despesas Exceto Intraorçamentárias",
        "Despesas Intraorçamentárias",
    ]:
        return "Total_Geral"

    if re.match(r"^\d{2}\.\d{3}\s*-", conta):
        return "Subfunção"

    if re.match(r"^\d{2}\s*-", conta):
        return "Função"

    if re.match(r"^FU\d{2}\s*-", conta):
        return "Subfuncao_agregada"

    return "Outros"


def descobrir_ano(caminho: Path) -> int:
    """Extrai o ano (4 dígitos) de qualquer parte do caminho.

    Args:
        caminho: Path correspondente ao arquivo de dados.

    Returns:
        Ano como inteiro.

    Raises:
        ValueError: Se o ano não for encontrado no caminho.
    """
    for parte in caminho.parts:
        if re.fullmatch(r"\d{4}", parte):
            return int(parte)
    raise ValueError(f"Ano não encontrado no caminho: {caminho}")


def limpar_e_transformar_df(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Limpa e transforma o DataFrame bruto do FINBRA de um ano específico.

    Remove espaços nos nomes das colunas, define o ano, classifica as contas
    e converte a coluna 'Valor' para tipo numérico.

    Args:
        df: DataFrame original carregado do CSV.
        ano: Inteiro indicando o ano dos dados.

    Returns:
        DataFrame limpo e transformado.
    """
    df = df.copy()
    df.columns = df.columns.str.strip()
    df["Ano"] = ano
    df["ContaTipo"] = df["Conta"].apply(classificar_conta)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    return df
