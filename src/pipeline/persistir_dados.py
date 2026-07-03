import pandas as pd
import logging
import time
from pathlib import Path


def salvar_em_parquet(df: pd.DataFrame, caminho_arquivo: str | Path) -> None:
    """Salva o DataFrame consolidado no formato colunar Parquet."""
    inicio = time.time()

    Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(caminho_arquivo, engine="pyarrow", index=False)

    fim = time.time()
    logging.info(f"Base de dados salva em Parquet: '{caminho_arquivo}'")
    logging.info(f"Tempo de execução (Parquet): {fim - inicio:.4f} segundos")
