import os
import zipfile
import logging
from pathlib import Path

# Configurando um logger básico para exibir mensagens no terminal
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extrair_zips(pasta_origem: str | Path, pasta_destino: str | Path) -> None:
    """
    Percorre a pasta de origem, encontra arquivos .zip e os extrai para a pasta de destino.
    Mantém a estrutura de subpastas da origem (ex: ano).
    """
    origem = Path(pasta_origem)
    destino = Path(pasta_destino)

    if not origem.exists():
        logging.warning(f"A pasta de origem '{origem}' não foi encontrada.")
        return

    # rglob vai buscar arquivos .zip em todos os subdiretórios (ex: 2020, 2021, ...)
    zips_encontrados = list(origem.rglob("*.zip"))
    
    if not zips_encontrados:
        logging.info("Nenhum arquivo .zip encontrado para extração.")
        return
        
    logging.info(f"Encontrados {len(zips_encontrados)} arquivo(s) .zip. Iniciando extração...")

    for caminho_zip in zips_encontrados:
        # Descobre qual é a subpasta (o ano, ex: '2020') para espelhar no destino
        caminho_relativo = caminho_zip.relative_to(origem).parent
        pasta_destino_arquivo = destino / caminho_relativo
        
        # Cria a pasta do ano dentro de dados_extraidos se ela não existir
        pasta_destino_arquivo.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Extraindo: '{caminho_zip.name}' -> '{pasta_destino_arquivo}'")
        
        try:
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(pasta_destino_arquivo)
        except zipfile.BadZipFile:
            logging.error(f"Erro ao extrair '{caminho_zip.name}': arquivo corrompido ou inválido.")
        except Exception as e:
            logging.error(f"Erro inesperado ao extrair '{caminho_zip.name}': {e}")

if __name__ == "__main__":
    # Teste de execução local caso rode o script diretamente
    diretorio_atual = Path(__file__).parent.parent
    pasta_origem_dados = diretorio_atual / "dados_compactos"
    pasta_destino_dados = diretorio_atual / "dados_extraidos"
    
    extrair_zips(pasta_origem_dados, pasta_destino_dados)
