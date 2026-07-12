# Deploy do dashboard estático — imagem mínima (Caddy Alpine), sem Python, sem segredos.
# O container serve apenas os arquivos de public/; o pipeline de dados roda localmente.
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY public /srv

# Documentação de porta (Railway injeta $PORT em runtime; o Caddyfile já a usa).
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- "http://127.0.0.1:${PORT:-8080}/" >/dev/null 2>&1 || exit 1
