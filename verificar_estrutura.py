from pathlib import Path
import duckdb

CAMINHO_DUCKDB = Path(__file__).parent / 'finbra.duckdb'
con = duckdb.connect(str(CAMINHO_DUCKDB))

# Verificar funções
print("=== FUNÇÕES DISPONÍVEIS ===")
funcoes = con.execute("SELECT DISTINCT Conta FROM despesas_finbra WHERE ContaTipo = 'Função' ORDER BY Conta").df()
print(funcoes)
print(f"\nTotal de funções: {len(funcoes)}")

# Verificar colunas
print("\n=== ESTRUTURA DA TABELA ===")
print(con.execute("DESCRIBE despesas_finbra").df())

# Verificar tipos de despesa
print("\n=== TIPOS DE DESPESA ===")
print(con.execute("SELECT DISTINCT Coluna FROM despesas_finbra ORDER BY Coluna").df())

# Verificar anos
print("\n=== ANOS DISPONÍVEIS ===")
print(con.execute("SELECT DISTINCT Ano FROM despesas_finbra ORDER BY Ano").df())

# Verificar capitais
print("\n=== NÚMERO DE CAPITAIS ===")
print(con.execute("SELECT COUNT(DISTINCT Instituição) as Num_Capitais FROM despesas_finbra").df())