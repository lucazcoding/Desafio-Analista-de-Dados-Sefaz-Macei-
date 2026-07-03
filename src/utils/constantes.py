from pathlib import Path

DIRETORIO_RAIZ = Path(__file__).parent.parent.parent

PASTA_COMPACTOS = DIRETORIO_RAIZ / "dados_compactos"
PASTA_EXTRAIDOS = DIRETORIO_RAIZ / "dados_extraidos"
CAMINHO_PARQUET = PASTA_EXTRAIDOS / "finbra_consolidado.parquet"
CAMINHO_DUCKDB = DIRETORIO_RAIZ / "finbra.duckdb"
