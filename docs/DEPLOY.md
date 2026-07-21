# Deploy — dashboard no Railway

O ambiente de produção serve `public/` com uma imagem mínima do Caddy. Não há Python, banco,
credenciais do INEP ou dados brutos no container.

**Produção:** <https://observatorio-educacao-rs-production.up.railway.app>

## Fluxo automático

```text
PR → merge na main → CI verde → Deploy Railway → verificação HTTP
```

O workflow [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) é acionado somente
depois que a CI da `main` termina com sucesso. Ele publica exatamente o commit validado e testa
o endereço público. O job fica intencionalmente desabilitado até que a credencial seja criada.

### Ativar uma única vez

1. No projeto do Railway, abra **Settings → Tokens** e crie um **Project Token** do ambiente
   `production`. Project Tokens são limitados ao projeto e são a credencial recomendada pelo
   Railway para CI/CD.
2. Salve o valor sem colocá-lo em arquivo:
   ```bash
   gh secret set RAILWAY_TOKEN --repo leonardo-michelotti/observatorio-educacao-rs
   ```
   O comando solicita o token de forma interativa e o envia criptografado ao GitHub.
3. Habilite o workflow:
   ```bash
   gh variable set RAILWAY_DEPLOY_ENABLED --body true \
     --repo leonardo-michelotti/observatorio-educacao-rs
   ```
4. Execute **Deploy Railway → Run workflow** uma vez. Depois disso, todo merge aprovado pela
   CI será publicado automaticamente.

O token não deve ser um token pessoal ou de workspace. A documentação oficial está em
<https://docs.railway.com/cli/deploying#using-project-tokens>.

## Arquivos publicados

| Arquivo | Papel |
|---|---|
| `public/index.html` | narrativa e explorador |
| `public/arquitetura.html` | arquitetura e metodologia |
| `public/data-status.json` | anos disponíveis e fontes por indicador |
| `Dockerfile` | imagem `caddy:2-alpine` |
| `Caddyfile` | servidor, compressão, cache e cabeçalhos de segurança |
| `railway.toml` | Dockerfile, healthcheck e política de reinício |

## Deploy manual de contingência

Se o GitHub Actions ou o token estiver indisponível, um operador autenticado pode publicar a
mesma árvore local:

```bash
npx --yes @railway/cli@5.27.2 up --ci \
  --environment production \
  --service observatorio-educacao-rs
```

O deploy manual é contingência, não o fluxo normal.

## Segurança

- `.dockerignore` restringe o contexto da imagem a `Caddyfile` e `public/`.
- O token existe somente como secret do GitHub e é injetado durante o job.
- A `main` exige a CI antes do deploy.
- O Caddy aplica CSP, HSTS, proteção contra framing, `nosniff` e política restritiva de
  permissões.
- O site é estático e não faz chamadas externas em runtime.
