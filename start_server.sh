#!/bin/bash

# Script de inicialização do MCP BNBO Server (P2 Linkage Criminal)
# Uso: ./start_server.sh

echo "============================================================"
echo "MCP BNBO - INICIALIZANDO SERVIDOR"
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

# Verificar se PostgreSQL/Redis estão rodando
echo ""
echo "Verificando PostgreSQL/Redis..."
if curl -s http://localhost:5432/ > /dev/null 2>&1 || nc -z localhost 5432 2>/dev/null; then
    echo "✓ PostgreSQL está acessível"
else
    echo "✗ PostgreSQL não está rodando!"
    echo "  Iniciando PostgreSQL + Redis com Docker..."
    docker compose up -d
    echo "  Aguardando serviços iniciarem..."
    sleep 5
fi

# Iniciar servidor
echo ""
echo "============================================================"
echo "INICIANDO SERVIDOR MCP..."
echo "============================================================"
echo ""

python3 mcp_server.py
