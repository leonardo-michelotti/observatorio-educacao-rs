# Deploy — dashboard no Railway

O que vai pro ar são **duas páginas estáticas** (`public/index.html` e
`public/arquitetura.html`), servidas por um
**Caddy** mínimo e endurecido. Sem backend, sem BigQuery, **sem segredos na imagem** — o
pipeline de dados continua rodando localmente e só o HTML gerado é publicado.

**No ar:** <https://observatorio-educacao-rs-production.up.railway.app>

> Nota do primeiro deploy: o `railway up` (CLI) usa o Railpack, que detecta o site estático e
> copia o contexto para `/app`. Por isso o `Caddyfile`/`Dockerfile` servem `/app/public`. Se
> você conectar via GitHub, o `railway.toml` faz usar o `Dockerfile` (que também serve
> `/app/public`) — os dois caminhos são equivalentes.

## Arquivos que compõem o deploy

| Arquivo | Papel |
|---|---|
| `public/index.html` | narrativa e explorador (gerados e versionados) |
| `public/arquitetura.html` | arquitetura, metodologia e decisões de curadoria |
| `Dockerfile` | imagem `caddy:2-alpine` que copia `public/` e o `Caddyfile` |
| `Caddyfile` | servidor estático + cabeçalhos de segurança + `$PORT` do Railway |
| `.dockerignore` | bloqueia tudo menos `Caddyfile` e `public/` (nada de `.env`/dados/venv) |
| `railway.toml` | build via Dockerfile + healthcheck na raiz |

## Subir (opção recomendada: GitHub → Railway)

1. Garanta que `public/index.html` está atualizado e commitado:
   ```bash
   python viz/build_dashboard.py   # ou python run_pipeline.py (regenera tudo)
   git add public/index.html && git commit -m "chore: atualiza dashboard publicado"
   git push
   ```
2. No [Railway](https://railway.app/): **New Project → Deploy from GitHub repo** →
   selecione `observatorio-educacao-rs`.
3. O Railway detecta o `Dockerfile`/`railway.toml`, builda e sobe sozinho.
4. **Settings → Networking → Generate Domain** (ou adicione um domínio próprio). HTTPS é
   automático.

Toda vez que você der `git push` com um `public/index.html` novo, o Railway **re-deploya sozinho**.

## Subir pela CLI (alternativa)

```bash
npm i -g @railway/cli      # ou: brew install railway
railway login
railway init               # cria/associa o projeto
railway up                 # builda e sobe a partir do Dockerfile
railway domain             # gera a URL pública
```

## Segurança (o que já está coberto)

- **Nenhum segredo na imagem.** O `.dockerignore` só deixa entrar `Caddyfile` e `public/`;
  `.env`, credenciais GCP, `data/` e o código do pipeline ficam de fora. (O `.env` também é
  git-ignored — nunca vai pro GitHub.)
- **Superfície mínima.** Página 100% estática e autocontida; não há backend nem chamada externa
  em runtime.
- **Cabeçalhos de segurança** no `Caddyfile`: CSP travada (`default-src 'none'`, libera só
  inline de CSS/JS e `data:` para o favicon), `X-Content-Type-Options`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, `Permissions-Policy` e `HSTS`.
- **HTTPS** automático pelo Railway (TLS terminado na borda; o container escuta HTTP em `$PORT`).
- **Header `Server` removido** (não expõe versão).

> Nota sobre a CSP: como o CSS e o JS são inline (peça autocontida), a política usa
> `'unsafe-inline'` para `style-src`/`script-src`. É o padrão aceitável para páginas estáticas
> self-contained; todo o resto fica bloqueado. Se um dia quiser CSP sem `unsafe-inline`, dá pra
> migrar para hashes/nonce.

## Atualizar o conteúdo

O dado muda quando você roda o pipeline. Para publicar a versão nova:
```bash
python run_pipeline.py     # regenera public/index.html (entre outros)
git commit -am "chore: atualiza dados publicados" && git push
```
