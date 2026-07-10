# Retomar — estado da execução (auto mode v1)

Última sessão parou aqui (10/07/2026). Reinício de PC pendente.

## Onde estamos
- **M0 (auth GCP):** ❌ credencial do Google **não** criada (o `gcloud auth application-default login`
  não completou — WSL sem navegador; precisa abrir a URL no navegador do Windows).
- **M1 (scaffold):** ✅ commitado e pushado (`bf5189c`). Mas o `pip install` **não terminou**
  (só `duckdb` instalou) e falta rodar `dbt debug`.
- **M2–M6:** não iniciados.

## Para retomar (2 passos humanos, depois o loop segue sozinho)

### 1. Terminar o setup do Python
```bash
cd /mnt/c/Projetos/observatorio-educacao-rs
source .venv/bin/activate
pip install -r requirements.txt          # completar o que faltou
```

### 2. Autenticar no Google (1x) — o gargalo do M0
O WSL não tem navegador, então:
```bash
gcloud auth application-default login --no-launch-browser
```
Isso mostra uma **URL** e pede um **código**. Abra a URL no navegador do **Windows**, faça login,
copie o código de volta pro terminal. (O modo `--no-launch-browser` é mais garantido no WSL do que
o padrão, que trava esperando `localhost`.)

Depois, descubra/anote seu **Project ID** do Google Cloud:
```bash
gcloud config get-value project
```

## Decisões travadas (não reabrir)
- Fonte: **Base dos Dados** no BigQuery (via cliente `google-cloud-bigquery`, não o pacote basedosdados).
- Recorte: **Santa Maria `4316907`** vs **RS** vs **Brasil**. Indicadores v1: **IDEB · taxas de
  rendimento · distorção idade-série**.
- Stack: BQ → Parquet bronze → dbt-duckdb (silver/gold) → matplotlib PNG → README (a vitrine).
- Escopo do loop: **até a vitrine no README**; commit+push a cada etapa; **sem** deploy/tornar público.
- Plano completo: `~/.claude/plans/snug-marinating-dolphin.md`.

## Próximo passo do Claude ao retomar
1. Confirmar install completo + `dbt debug` verde (fecha M1).
2. Localizar o arquivo de ADC gerado, apontar `GOOGLE_APPLICATION_CREDENTIALS`/`.env`
   (`BILLING_PROJECT_ID`) e testar `SELECT 1` no BigQuery (M0).
3. **M2:** descobrir schema real das tabelas no BD (`br_inep_ideb`, `br_inep_indicadores_educacionais`),
   extrair os 3 indicadores nos 3 níveis → `data/bronze/*.parquet`.
4. Seguir M3→M6 (dbt silver/gold → gráficos → README), commitando a cada milestone.
