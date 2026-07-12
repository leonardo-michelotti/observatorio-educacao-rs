# Retomar - estado da execucao

Atualizado: 12/07/2026. O projeto foi muito alem do "pipeline v1": tem vitrine no README,
painel editorial interativo e deploy ao vivo. Este arquivo e o ponto de retomada.

## No ar / links
- Painel ao vivo (Railway): https://observatorio-educacao-rs-production.up.railway.app
- Artifact (claude.ai): https://claude.ai/code/artifact/f070f10e-27e8-4222-b338-43a698e15e2e
- GitHub: https://github.com/leonardo-michelotti/observatorio-educacao-rs (branch main, tudo pushado)
- Pasta local: /mnt/c/Projetos/observatorio-educacao-rs

## O que esta pronto
- Pipeline (run_pipeline.py, 4 etapas idempotentes): ingestao BigQuery/Base dos Dados para
  data/bronze/*.parquet, depois dbt-duckdb (stg_*, fct_indicadores, 11 testes verdes), depois
  viz/make_charts.py (5 PNGs em assets/), depois viz/build_dashboard.py (viz/dashboard.html para
  o Artifact e public/index.html para a web).
- Indicadores no fct_indicadores (tidy: nivel, ano, indicador, etapa, valor): ideb,
  saeb_matematica, saeb_lingua_portuguesa, taxa_aprovacao, distorcao_idade_serie (so EF anos
  finais, curado).
- Niveis: Santa Maria (4316907), RS, Brasil. Fonte: INEP via Base dos Dados.
- README: vitrine editorial com os 3 achados e notas de qualidade.
- Painel: peca editorial de dados (data-journalism). Narrativa "comeca forte e perde o passo",
  cor como atencao seletiva (Santa Maria em destaque, RS/Brasil em cinza), graficos anotados,
  hero da queda 5,8 para 4,6 para 2,4, explorador interativo no fim. Gerado por build_dashboard.py.
- Deploy: Caddy estatico endurecido. Dockerfile, Caddyfile, railway.toml, .dockerignore,
  .railwayignore. Headers de seguranca (CSP, HSTS, X-Frame-Options, etc.). Sem segredos na
  imagem. Passo a passo em docs/DEPLOY.md. Serve de /app/public.
- Investigacao viva: docs/MELHORIAS.md (achados AF-1 a AF-6; frentes A a E).

## Logicas de calculo / curadoria (insumo para a aba de arquitetura)
- IDEB = proficiencia (SAEB) vezes rendimento (aprovacao). Por isso carregamos as notas SAEB:
  para decompor e mostrar a perda de aprendizagem da pandemia que a aprovacao mascara.
- Filtro de validade da aprovacao: valor entre 40 e 100 (remove pontos corrompidos).
- Distorcao idade-serie: so ef_anos_finais sobrevive a auditoria celula a celula (RS quebrado
  ate 2022; Santa Maria quebrada nos anos iniciais pos-2020; EM corrompido para todos).
  Curadoria documentada em dbt/models/staging/stg_indicadores.sql.
- Regra de render dos graficos: a etapa aparece se pelo menos 2 niveis tem serie solida (5+
  anos), plotando so os que passam. Por isso EM de aprovacao entra como SM vs Brasil e IDEB de
  EM nao.
- Origem da corrupcao: e da harmonizacao da Base dos Dados, nao do INEP (AF-6). O dado do INEP
  e publico e limpo; integra-lo direto (microdado/indicadores oficiais) e um proximo passo.

## Deploy / redeploy
- python run_pipeline.py regenera public/index.html.
- Publicar: git add -A && git commit && git push, depois
  railway up -y --ci --service observatorio-educacao-rs (CLI ja logada como Leonardo).
- Auth git: usar gh como credential helper:
  git -c credential.helper='!gh auth git-credential' push origin main
- Screenshots para conferir a viz: Chrome do Windows headless:
  "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --screenshot=... file:///C:/...

## PROXIMAS TAREFAS (retomar aqui)

1. Nova aba/secao "Arquitetura e Metodologia" no painel (viz/build_dashboard.py), focada so em
   explicar o projeto: como conseguimos os dados (Base dos Dados / BigQuery / INEP), como
   construimos (arquitetura medalhao bronze para silver/gold com dbt, depois viz), como funciona
   o pipeline, como versionamos (git e dbt) e as logicas de calculo/curadoria (a secao acima).
   Pode ser uma aba ou seccao ancorada dentro da pagina; reaproveitar a identidade editorial.

2. Revisar o texto das paginas ja publicadas (painel e README) para tirar a cara de IA da
   escrita. Tres pontos concretos:
   a) Travessoes: cortar o excesso de "—". Usar pontuacao natural (virgula, parenteses, ponto,
      dois-pontos) e evitar construcoes simetricas artificiais ("nao X, mas Y").
   b) Gafe do rodape: a nota "Como estes numeros foram tratados" diz que "a fonte oficial do
      INEP e limpa, mas seu servidor e inacessivel deste ambiente". Isso vaza contexto do agente
      e da a entender que o dado do INEP nao esta disponivel, quando ele e PUBLICO. Reescrever
      sem citar "este ambiente": enquadrar como escolha informada. Ex.: a corrupcao esta na
      camada harmonizada da Base dos Dados; a fonte oficial do INEP (publica) e limpa e a
      integracao direta fica como proximo passo; por ora, curadoria transparente sobre a Base
      dos Dados. O texto deve mostrar dominio do assunto, nao uma limitacao tecnica.
   c) Emojis: remover todos os emojis das paginas (o README tem emojis nos "3 achados" e no
      link "Painel ao vivo"; conferir o restante). Manter apenas o favicon se fizer sentido.
   Depois de revisar: rebuild (python viz/build_dashboard.py ou run_pipeline.py) e redeploy.

## Cuidados
- Nunca versionar nem subir o .env ou a credencial GCP (protegidos por .gitignore,
  .dockerignore e .railwayignore).
- Sempre testar de verdade (curl no site, screenshot da viz) antes de dar por pronto. O primeiro
  deploy deu 404 e so pegamos porque testamos.
- Preferencias de estilo do Leonardo: sem emojis, sem excesso de travessoes, nada com "cara de
  IA". Ver a memoria design-nao-cara-de-ia.
