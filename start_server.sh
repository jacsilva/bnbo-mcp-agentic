#!/bin/bash

# Script de inicialização do MCP Agentic RAG Server
# Uso: ./start_server.sh

echo "============================================================"
echo "MCP AGENTIC RAG - INICIALIZANDO SERVIDOR"
echo "============================================================"
echo ""

# Ativar ambiente virtual
if [ -d "venv" ]; then
    echo "✓ Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "✗ Ambiente virtual não encontrado!"
    echo "  Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    echo "  Instalando dependências..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Verificar se Qdrant está rodando
echo ""
echo "Verificando Qdrant..."
if curl -s http://localhost:6333/ > /dev/null 2>&1; then
    echo "✓ Qdrant está rodando"
else
    echo "✗ Qdrant não está rodando!"
    echo "  Iniciando Qdrant com Docker..."
    docker compose up -d
    echo "  Aguardando Qdrant iniciar..."
    sleep 5
fi

# Verificar API key
echo ""
if grep -q "your_firecrawl_api_key_here" .env 2>/dev/null; then
    echo "⚠ AVISO: API key do Firecrawl não configurada!"
    echo "  Edite o arquivo .env e adicione sua chave"
    echo "  A busca web não funcionará sem a chave"
fi

# Iniciar servidor
echo ""
echo "============================================================"
echo "INICIANDO SERVIDOR MCP..."
echo "============================================================"
echo ""

python3 mcp_server.py
