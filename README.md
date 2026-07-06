 # Analise da Execucao Orcamentaria das Capitais Brasileiras

## Objetivo

Analise de eficiencia da execucao orcamentaria de **26 capitais brasileiras** (2020-2024), comparando quanto do orcamento empenhado foi efetivamente pago em cada funcao de governo. Identificar padroes de gasto publico, posicionar Maceio em relacao as demais capitais e analisar a pressao fiscal acumulada via Restos a Pagar.

## Base de dados

- **Fonte:** FINBRA/Siconfi — Despesas das prefeituras municipais (Anexo I-E)
- **Periodo:** 2020-2024 (2025 excluido — dados incompletos: apenas 11 de 26 capitais)
- **Escopo:** 26 capitais brasileiras, 27 funcoes de governo
- **Campos principais:** Instituicao, Coluna (Empenhadas/Pagas/etc), Conta (Funcao/Subfuncao), Valor

## Tecnologias utilizadas

- **Python 3** + **venv** (ambiente isolado)
- **DuckDB** — Consultas SQL analiticas
- **Pandas** — Manipulacao de dados
- **Matplotlib** — Visualizacoes
- **PyArrow/Parquet** — Armazenamento colunar comprimido

## Estrutura do projeto

```
Desafio-Analista-de-Dados-Sefaz-Macei-
├── requirements.txt
├── notebooks/
│   ├── 1-Preparar_Dataset.ipynb   # ETL (rodar primeiro)
│   └── 2-Analise.ipynb            # Analise completa
├── src/
│   ├── banco/
│   │   ├── conexao_duckdb.py
│   │   └── criar_tabela.py
│   └── utils/
│       └── constantes.py
├── dados_compactos/               # ZIPs originais
├── dados_extraidos/               # CSVs descompactados
├── data/processed/                # Parquets
└── finbra.duckdb                  # Banco gerado
```

## Etapas da analise

1. **Consolidacao dos arquivos** — Descompactar ZIPs por ano, ler CSVs (latin-1, `;`, decimal `,`), adicionar coluna `Ano` e classificar `ContaTipo` (Funcao, Subfuncao, Subfuncao_agregada, Total_Geral)
2. **Armazenamento no DuckDB** — Salvar consolidado em Parquet e carregar tabela `despesas_finbra` no DuckDB
3. **Calculo da taxa de execucao** — `Taxa = (Pago / Empenhado) * 100` por capital e por funcao (702 registros: 26 capitais x 27 funcoes)
4. **Comparacao entre capitais** — Estatistica descritiva (media, mediana, desvio padrao, CV) e ranking geral
5. **Investigacao do caso de Natal** — Identificar por que Natal tem a menor taxa de execucao (83.64%)
6. **Comparacao com a media nacional** — Posicionar Maceio (8o lugar, 94.28%) e identificar capitais consistentemente acima/abaixo da media
7. **Investigacao por subfuncoes** — Analisar onde o dinheiro vai dentro de Saude e Educacao (composicao do gasto)
8. **Validacao se o problema era local ou estrutural** — Verificar se baixa execucao e specifica de uma funcao ou generalizada

## Principais descobertas

| Descoberta | Resultado |
|------------|-----------|
| Melhor execucao geral | Goiania (98.06%) |
| Pior execucao geral | Natal (83.64%) |
| Posicao de Maceio | 8o lugar (94.28%), 1.87 pp acima da media |
| Ponto forte de Maceio | Saude (4o lugar nacional, 97.91%) |
| Funcao com mais desigualdade | Ciencia e Tecnologia (CV=29.72%) |
| Capitais consistentes | Goiania, Belem, Aracaju (CV < 2%) |

## Como executar

```bash
# 1. Criar ambiente virtual
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Rodar preparacao do dataset (primeira vez)
jupyter notebook notebooks/1-Preparar_Dataset.ipynb

# 4. Rodar analise
jupyter notebook notebooks/2-Analise.ipynb
```

## Consideracoes finais

- **2025 excluido**: Apenas 11 de 26 capitais declararam dados, causaria comparacoes injustas
- **Desvio padrao amostral** (n-1): Trabalhamos com amostra de 26 capitais, nao a populacao total
- **Mediana como referencia**: Em funcoes com outliers, a mediana e mais representativa que a media
- **Funcoes com N < 5 capitais**: Estatisticas calculadas mas nao usadas para benchmarking nacional
