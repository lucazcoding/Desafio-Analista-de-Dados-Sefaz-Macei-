import re
from pathlib import Path

def descobrir_ano_pelo_caminho(caminho_arquivo: str | Path) -> int | None:
    """
    Descobre o ano a partir do caminho do arquivo.
    Procura nas partes do caminho alguma pasta que represente um ano (4 dígitos numéricos).
    Exemplo: 'dados_extraidos/2021/finbra.csv' -> retorna 2021
    
    Args:
        caminho_arquivo: Caminho do arquivo a ser analisado.
        
    Returns:
        O ano como inteiro, ou None se não for encontrado um ano válido na estrutura de pastas.
    """
    caminho = Path(caminho_arquivo)
    
    # Percorre todas as partes do caminho para buscar uma string de exatos 4 dígitos
    for parte in caminho.parts:
        if re.fullmatch(r"\d{4}", parte):
            return int(parte)
            
    return None

if __name__ == "__main__":
    # Teste simples executado localmente
    caminho_teste = Path("dados_extraidos/2022/finbra.csv")
    ano_encontrado = descobrir_ano_pelo_caminho(caminho_teste)
    print(f"Caminho analisado: {caminho_teste}")
    print(f"Ano descoberto: {ano_encontrado}")
