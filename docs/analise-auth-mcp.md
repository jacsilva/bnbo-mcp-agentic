# Autenticação real do cliente ao servidor MCP (JWT por claims + TLS)

## Context

Hoje **não há autenticação do cliente ao servidor MCP** — é um placeholder assumido no código.
`server/security/contexto.py` resolve `get_perfil_atual()`/`get_cliente_atual()` a partir das
variáveis de ambiente `MCP_PERFIL_ATUAL`/`MCP_CLIENTE_ATUAL` do **processo servidor**, o que significa:

- No transporte `streamable-http` (`http://127.0.0.1:8080/mcp`), qualquer processo que alcance a
  porta invoca todas as tools **sem credencial**.
- O perfil é **global por processo**, não por requisição — clientes concorrentes são indistinguíveis.
- Sem TLS: token/PII trafegariam em claro.

A camada de **autorização** (perfis `publico<analista<investigador`, gate em `util_jobs.py:40`,
redação de PII em `p2_linkage.py:52,111`) e **auditoria** (`audit_log`) já existem e funcionam, mas
todas se apoiam nessa identidade falsa. O próprio `contexto.py:6-13` declara que o perfil "deve vir
de um token validado (JWT/OAuth) anexado à conexão MCP" e marca isso como pendência da Fatia 2.

**Objetivo:** implementar autenticação real por **JWT validado por claims** (assinatura + expiração),
derivando cliente/perfil das claims do token e tornando o contexto **por-requisição**; adicionar **TLS**.

O SDK em uso (`mcp` 1.28.1, `FastMCP`) já suporta tudo isso nativamente — basta configurá-lo.
`PyJWT 2.13.0` já está instalado no venv.

## Abordagem (apenas a recomendada)

Servidor MCP atua como **Resource Server**: recebe `Authorization: Bearer <jwt>`, valida o JWT e
expõe o perfil via contexto de auth do SDK. Reaproveita os pontos de extensão nativos:

- `mcp.server.auth.provider.TokenVerifier` (protocol: `async def verify_token(token) -> AccessToken | None`)
- `mcp.server.auth.provider.AccessToken` (campos `client_id`, `scopes`, `subject`, `claims`)
- `mcp.server.auth.settings.AuthSettings` (`issuer_url`, `resource_server_url`, `required_scopes`)
- `mcp.server.auth.middleware.auth_context.get_access_token()` — devolve o `AccessToken` da
  requisição atual (via contextvar) de dentro de qualquer tool. **É isto que torna o contexto request-scoped.**

Wiring: `FastMCP(..., auth=AuthSettings(...), token_verifier=JwtTokenVerifier())`. Quando `auth`
está setado, o SDK injeta automaticamente `BearerAuthBackend` + `RequireAuthMiddleware` +
`AuthContextMiddleware` na app Starlette (ver `fastmcp/server.py:857-874`) — sem rota/middleware manual.

## Arquivos a criar / modificar

### 1. `server/security/jwt_verifier.py` (novo)
- Classe `JwtTokenVerifier` implementando `verify_token(token)`:
  - decodifica com `jwt.decode(token, key, algorithms=[ALG], audience=..., issuer=...)`;
  - HS256 com segredo compartilhado (`MCP_JWT_SECRET`) **ou** RS256/JWKS via `PyJWKClient`
    (`MCP_JWT_JWKS_URL`) — selecionado por `MCP_JWT_ALG`;
  - em sucesso retorna `AccessToken(token=..., client_id=claims["sub"], subject=claims["sub"],
    scopes=[claim de perfil], claims=payload)`; em falha (assinatura/exp/claims) retorna `None`
    (o SDK responde 401 automaticamente).
  - O **perfil** vem de uma claim dedicada (ex. `perfil` ou `scope`), mapeada para
    `{publico,analista,investigador}` de `server/security/perfis.py` (reusar `PERFIS_VALIDOS`).

### 2. `server/security/contexto.py` (modificar — peça central)
Tornar request-scoped **sem alterar a assinatura** (tools continuam chamando sem argumentos):
```python
from mcp.server.auth.middleware.auth_context import get_access_token

def get_perfil_atual() -> str:
    tok = get_access_token()
    if tok is not None:
        perfil = (tok.claims or {}).get("perfil")  # ou mapear de tok.scopes
        return perfil if perfil in PERFIS_VALIDOS else PUBLICO
    # fallback DEV/stdio apenas, gated por MCP_ALLOW_ENV_AUTH=1
    ...

def get_cliente_atual() -> str:
    tok = get_access_token()
    return tok.subject or tok.client_id if tok else os.getenv("MCP_CLIENTE_ATUAL", "desconhecido")
```
O fallback por env var fica **explicitamente atrás de flag** (`MCP_ALLOW_ENV_AUTH`) e só faz sentido
em `stdio`/dev — em produção HTTP, ausência de token ⇒ 401 antes de chegar na tool.
**Nenhuma tool precisa mudar** — `util_jobs.py:40`, `p2_linkage.py:52,111` continuam iguais.

### 3. `server/mcp_server.py` (modificar — linha ~59)
Quando `MCP_TRANSPORT` for `streamable-http`/`http`, instanciar com auth:
```python
from mcp.server.auth.settings import AuthSettings
from server.security.jwt_verifier import JwtTokenVerifier

auth = AuthSettings(
    issuer_url=os.getenv("MCP_JWT_ISSUER"),
    resource_server_url=f"http://{HOST}:{PORT}/mcp",  # https em prod
    required_scopes=None,
)
mcp_server = FastMCP(..., host=HOST, port=PORT,
                     auth=auth, token_verifier=JwtTokenVerifier())
```
Em `stdio` (default), manter sem auth (não há canal HTTP/headers). Selecionar via o mesmo
ramo `if transport in ("streamable-http","http")` que já existe (`server/mcp_server.py:142`).

### 4. TLS/HTTPS
Recomendado: **reverse proxy** (nginx/Caddy) terminando TLS na frente do `:8080`, mantendo o
uvicorn do SDK em loopback. Documentar no README + exemplo de config. (Alternativa: uvicorn com
`ssl_keyfile/ssl_certfile`, porém o `FastMCP.run()` não expõe esses kwargs diretamente — o proxy é
o caminho limpo.) Atualizar `resource_server_url`/`MCP_SERVER_URL` para `https://`.

### 5. `.env.example` (modificar — corrigir drift + novas vars)
- Trocar `MCP_TRANSPORT=stdio | sse` → `stdio | streamable-http` e `MCP_SERVER_URL .../sse` → `.../mcp`.
- Documentar: `MCP_JWT_ALG`, `MCP_JWT_SECRET` ou `MCP_JWT_JWKS_URL`, `MCP_JWT_ISSUER`,
  `MCP_JWT_AUDIENCE`, `MCP_PERFIL_CLAIM`, `MCP_ALLOW_ENV_AUTH`.
- Documentar (antes não existiam) `MCP_PERFIL_ATUAL`/`MCP_CLIENTE_ATUAL` como **dev-only**.

### 6. Testes (`tests/`)
- `tests/test_jwt_verifier.py` (novo): token válido → `AccessToken` com perfil correto; assinatura
  inválida / expirado / claim de perfil ausente → `None`.
- `tests/test_contexto.py` (novo): monkeypatch de `get_access_token` para simular requisição
  autenticada e verificar `get_perfil_atual()`/`get_cliente_atual()` request-scoped + fallback dev.
- Ajustar quaisquer testes existentes que setem `MCP_PERFIL_ATUAL` para usar o fallback gated.

### 7. Higiene de segredos (paralelo, baixo esforço)
`.env` **não** é rastreado pelo git (já está no `.gitignore:30`), mas contém `GROQ_API_KEY` real.
Recomendar **rotação** dessa chave por precaução e confirmar que nunca foi commitada (`git log -p`).

## Verificação (end-to-end)

1. **Unit:** `./venv/bin/pytest tests/test_jwt_verifier.py tests/test_contexto.py -v`.
2. **401 sem token:** subir `MCP_TRANSPORT=streamable-http ./venv/bin/python -m server.mcp_server` e
   `curl -i http://127.0.0.1:8080/mcp` → deve retornar **401 Unauthorized** (não 200/tool).
3. **Token válido por perfil:** gerar JWT de teste (HS256 com `MCP_JWT_SECRET`, claim `perfil=analista`),
   chamar via cliente MCP (`server/.../client` ou script com header `Authorization: Bearer`) a tool
   `reindexar_embeddings` → **permitido**; com `perfil=publico` → **negado** pelo gate de `util_jobs.py:40`.
4. **Redação de PII por perfil:** `buscar_ocorrencias_similares` com `perfil=investigador` retorna PII
   íntegra; com `publico/analista` retorna mascarada (`p2_linkage.py` + `redacao.py`).
5. **Auditoria:** confirmar em `audit_log` que `cliente`/`perfil` agora refletem o `sub`/claim do JWT,
   não a env var.
6. **stdio inalterado:** rodar em `stdio` sem token e confirmar que segue funcionando (fallback dev).
7. **TLS:** com o proxy, `curl -i https://<host>/mcp` (cert válido) e `http://` recusado/redirecionado.
