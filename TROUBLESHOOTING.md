# Guia de Troubleshooting - MCP Agentic RAG

## Problema: Timeout ao baixar modelo do HuggingFace

### Sintomas
```
ReadTimeoutError("HTTPSConnectionPool(host='huggingface.co', port=443): Read timed out. (read timeout=10)")
Retrying in 1s [Retry 1/5]...
```

### Soluções

#### Solução 1: Usar modelo menor (RECOMENDADO)
O código já foi atualizado para usar `sentence-transformers/all-MiniLM-L6-v2` por padrão, que é:
- **Menor**: ~80MB vs ~500MB
- **Mais rápido**: Download e carregamento
- **Confiável**: Modelo amplamente usado

Basta reiniciar o servidor:
```bash
# Pare o servidor atual (Ctrl+C)
python3 mcp_server.py
```

#### Solução 2: Aumentar timeout manualmente
Se quiser usar o modelo Nomic (melhor qualidade), edite `rag_app.py`:

```python
# Já configurado no código:
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'  # 5 minutos
```

#### Solução 3: Download manual do modelo
```bash
# Instale huggingface-cli
pip install huggingface-hub

# Baixe o modelo manualmente
huggingface-cli download sentence-transformers/all-MiniLM-L6-v2

# Ou para o modelo Nomic:
huggingface-cli download nomic-ai/nomic-embed-text-v1.5
```

#### Solução 4: Usar cache local
Se você já baixou o modelo antes:
```bash
# Verifique o cache
ls -la ~/.cache/huggingface/hub/

# O modelo será reutilizado automaticamente
```

#### Solução 5: Configurar proxy (se necessário)
```bash
export HTTP_PROXY=http://seu-proxy:porta
export HTTPS_PROXY=http://seu-proxy:porta
python3 mcp_server.py
```

---

## Problema: Servidor não inicia (porta 8080 em uso)

### Solução
```bash
# Encontre o processo usando a porta
lsof -i :8080

# Mate o processo
kill -9 <PID>

# Ou use outra porta editando mcp_server.py:
PORT = 8081  # Mude para porta diferente
```

---

## Problema: Qdrant não conecta

### Verificações
```bash
# Verifique se o container está rodando
docker ps | grep qdrant

# Se não estiver, inicie:
docker compose up -d

# Verifique os logs
docker compose logs qdrant

# Teste a conexão
curl http://localhost:6333/collections
```

---

## Problema: Import Error - subprocess

### Solução
O código já foi corrigido. Se ainda tiver erro:
```python
# Adicione no topo de mcp_server.py:
import subprocess
```

---

## Problema: Dependências faltando

### Solução completa
```bash
# Reinstale todas as dependências
pip install --upgrade pip
pip install -r requirements.txt

# Se torch estiver causando problemas:
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

---

## Verificação de Saúde do Sistema

Execute este script para verificar tudo:

```bash
#!/bin/bash
echo "=== Verificação do Sistema ==="

echo -n "Docker: "
docker --version && echo "✓" || echo "✗"

echo -n "Qdrant: "
curl -s http://localhost:6333/ > /dev/null && echo "✓" || echo "✗"

echo -n "Python: "
python3 --version

echo -n "Dependências: "
pip list | grep -E "mcp|qdrant|llama-index" && echo "✓" || echo "✗"

echo "=== Fim da Verificação ==="
```

---

## Logs Úteis

### Ver logs do servidor MCP
```bash
python3 mcp_server.py 2>&1 | tee mcp_server.log
```

### Ver logs do Qdrant
```bash
docker compose logs -f qdrant
```

### Verificar uso de memória
```bash
# Durante o download do modelo
watch -n 1 'free -h'
```

---

## Contato e Suporte

- **HuggingFace Status**: https://status.huggingface.co/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **MCP Docs**: https://modelcontextprotocol.io/

---

## Modelos Alternativos

Se continuar com problemas, tente estes modelos (do menor para o maior):

| Modelo | Tamanho | Dimensões | Velocidade | Qualidade |
|--------|---------|-----------|------------|-----------|
| `sentence-transformers/all-MiniLM-L6-v2` | 80MB | 384 | ⚡⚡⚡ | ⭐⭐⭐ |
| `sentence-transformers/all-mpnet-base-v2` | 420MB | 768 | ⚡⚡ | ⭐⭐⭐⭐ |
| `nomic-ai/nomic-embed-text-v1.5` | 500MB | 768 | ⚡ | ⭐⭐⭐⭐⭐ |

Para mudar o modelo, edite em `mcp_server.py`:
```python
faq_engine = FAQEngine(
    qdrant_url=QDRANT_URL, 
    collection_name=COLLECTION_NAME,
    embed_model_name="sentence-transformers/all-MiniLM-L6-v2"  # Escolha aqui
)
```
