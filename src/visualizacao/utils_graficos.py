import pandas as pd


def extrair_nome_capital(texto: str) -> str:
    """Extrai o nome limpo da capital a partir do texto da Instituição.

    Ex: 'Prefeitura Municipal de Maceió - AL' → 'Maceió'
    """
    nome = texto.replace("Prefeitura Municipal de ", "").replace("Prefeitura Municipal do ", "")
    nome = nome.split(" - ")[0].strip()
    return nome
