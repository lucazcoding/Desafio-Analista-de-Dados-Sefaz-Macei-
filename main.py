"""
main.py — Entry point do CLI Desafio Sefaz Maceio.

Uso:
    python main.py build          # executa pipeline ETL
    python main.py analyze taxa   # roda analise especifica
    python main.py analyses       # lista analises disponiveis
    python main.py run            # executa todas as analises
"""

from src.cli.app import app

if __name__ == "__main__":
    app()
