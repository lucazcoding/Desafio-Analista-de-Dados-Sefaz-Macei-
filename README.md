# Desafio Analista de Dados — SEFAZ Maceió

## 📋 Visão Geral

Análise de eficiência da execução orçamentária de **26 capitais brasileiras** (2020-2024), comparando quanto do orçamento empenhado foi efetivamente pago em cada função de governo.

**Objetivo:** Identificar padrões de gasto público, posicionar Maceió em relação às demais capitais e analisar a pressão fiscal acumulada via Restos a Pagar.

---

## 🚀 Como Reproduzir a Análise

### Opção 1 — Via Jupyter Notebooks (Recomendado)

Execute os notebooks **em ordem**. Cada um depende do anterior.

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar o Jupyter
jupyter notebook
```

| Notebook | O que faz |
|----------|-----------|
| `00_preparacao_dados.ipynb` | ETL completo: descompacta ZIPs, lê CSVs, enriquece, valida e carrega o DuckDB |
| `01_calculo_indicadores.ipynb` | Calcula as 702 taxas de execução (26 capitais × 27 funções) |
| `02_comparacao_capitais.ipynb` | Estatística descritiva por função: média, mediana, DP, CV |
| `03_padroes_nacionais.ipynb` | Identifica capitais consistentes e funções problemáticas |
| `04_casos.ipynb` | Seleciona os 3 estudos de caso: Goiânia, Maceió e Natal |
| `05_aprofundamento.ipynb` | Aprofunda os 3 casos: evolução temporal e composição de subfunções |
| `06_restos_a_pagar.ipynb` | Análise de Restos a Pagar: quem mais adia pagamentos? |

### Opção 2 — Via CLI (Terminal)

```bash
# Executar pipeline ETL (equivalente ao Notebook 00)
python main.py build

# Executar análises individuais
python main.py analyze taxa
python main.py analyze percapita
python main.py analyze evolucao
python main.py analyze subfuncoes
```

---

## 🎯 Perguntas Respondidas

| # | Pergunta | Resposta Principal | Notebook |
|---|----------|--------------------|---------|
| 1 | Taxa de execução por capital por função | 702 registros (26 × 27) | 01 |
| 2 | Taxa geral por capital | Goiânia #1 (98.06%), Natal último (83.60%) | 01 |
| 3 | Quem executa melhor em Saúde/Educação | Saúde: Recife #1. Educação: Fortaleza #1 | 02 |
| 4 | Mediana vs média (outliers) | 3 funções com outliers (CV alto) | 02 |
| 5 | Função com mais desigualdade | Ciência e Tecnologia (CV=29.72%) | 02 |
| 6 | Capitais consistentemente acima da média | Fortaleza, Belém, Aracaju | 03 |
| 7 | Função mais problemática | Defesa Nacional (66.67% das capitais abaixo da média) | 03 |
| 8 | Posição de Maceió no ranking geral | 8º lugar (94.28%), acima da média (92.41%) | 04 |
| 9 | Maceió melhorou ao longo dos anos? | Leve melhora (~93% → ~94%) | 05 |
| 10 | Composição por subfunção | Maceió concentra 58% em Assistência Hospitalar (Saúde) | 05 |
| 11 | O que Goiânia faz diferente? | 60% do gasto de Educação vai para Ensino Fundamental | 05 |
| 12 | Quem mais acumula Restos a Pagar? | Análise completa por capital e por função | 06 |

---

## 🏗️ Estrutura do Projeto

```
├── main.py                    # Entry point CLI (Typer)
├── requirements.txt           # Dependências
├── notebooks/                 # Análises interativas (narrativa principal)
│   ├── 00_preparacao_dados.ipynb    # ETL completo
│   ├── 01_calculo_indicadores.ipynb
│   ├── 02_comparacao_capitais.ipynb
│   ├── 03_padroes_nacionais.ipynb
│   ├── 04_casos.ipynb
│   ├── 05_aprofundamento.ipynb
│   └── 06_restos_a_pagar.ipynb
├── src/
│   ├── cli/                   # Interface de linha de comando (Typer)
│   ├── pipeline/              # ETL (extração, consolidação, validação)
│   ├── banco/                 # Conexão DuckDB
│   ├── analises/              # Módulos de análise SQL
│   ├── visualizacao/          # Gráficos matplotlib
│   └── utils/                 # Constantes e utilitários
└── data/
    └── processed/             # Parquets intermediários
```

---

## 📊 Métricas Utilizadas

**Taxa de Execução:**
$$Taxa = \frac{Despesas\ Pagas}{Despesas\ Empenhadas} \times 100$$

**Taxa Geral Ponderada:**
$$Taxa_{Geral}(C) = \frac{\sum Pago(C,\text{todas funções})}{\sum Empenhado(C,\text{todas funções})} \times 100$$

> Por que soma total e não média simples? Porque a média simples daria peso igual a todas as funções, fazendo com que uma área com R$ 5 milhões pesasse tanto quanto Saúde com R$ 1 bilhão. A soma ponderada é matematicamente correta.

**Coeficiente de Variação (CV):**
$$CV = \frac{Desvio\ Padrão}{Média} \times 100$$

- CV < 15%: Homogênea (capitais se comportam parecido)
- 15% ≤ CV < 30%: Moderada
- CV ≥ 30%: Heterogênea (grandes diferenças entre capitais)

---

## 📈 Principais Resultados

### Ranking Geral (Top 5)
1. Goiânia — 98.06%
2. Belém — 96.98%
3. Recife — 96.93%
4. Aracaju — 96.73%
5. Manaus — 96.26%

### Posição de Maceió
- **8º lugar** de 26 capitais
- **94.28%** de taxa geral
- **1.87 pp acima** da média nacional (92.41%)
- **Ponto forte**: Saúde (4º lugar nacional, 97.91%)
- **Ponto a melhorar**: Educação (fora do Top 10)

---

## 🛠️ Tecnologias

- **Python 3** + **venv** (ambiente isolado)
- **DuckDB** — Consultas SQL analíticas diretamente no Parquet
- **Pandas** — Manipulação de dados
- **Matplotlib** — Visualizações
- **Typer** — CLI profissional
- **PyArrow/Parquet** — Formato otimizado de armazenamento

---

## 📁 Dados

- **Fonte:** FINBRA/Siconfi — Despesas das prefeituras municipais (Anexo I-E)
- **Período:** 2020-2024 (2025 excluído — dados incompletos: apenas 11 de 26 capitais)
- **Escopo:** 26 capitais brasileiras
- **Funções:** 27 funções de governo

---

## 📝 Decisões Metodológicas

- **2025 excluído**: Apenas 11 de 26 capitais declararam dados. Incluir causaria comparações injustas.
- **Desvio padrão amostral** (n-1): Usado porque trabalhamos com uma amostra (26 capitais), não a população total.
- **Mediana como referência** em funções com outliers: Quando a diferença entre média e mediana supera 5 pp, a mediana é mais representativa.
- **Funções com N < 5 capitais**: Estatísticas calculadas mas não usadas para benchmarking nacional (base amostral insuficiente).
