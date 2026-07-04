"""
Funções dos Prompt Templates. Registradas em `server/mcp_server.py` via
`mcp_server.prompt(name=...)`. Cada função retorna a mensagem (string) que
prepara o modelo para executar a tarefa com a tool adequada.

Os argumentos com default "" são opcionais; quando vazios, o template instrui o
modelo a consultar a base sem filtro.
"""


def analisar_ocorrencias_similares(bo_id: str = "", texto_livre: str = "", top_k: int = 10) -> str:
    """Busca ocorrências similares a um BO ou a um texto e explica as razões."""
    alvo = f"o BO `{bo_id}`" if bo_id else f"o relato livre: «{texto_livre}»"
    return (
        f"Quero analisar ocorrências similares a {alvo}.\n\n"
        f"1. Chame `buscar_ocorrencias_similares` com top_k={top_k} "
        "(top_k deve estar entre 1 e 100). Use `bo_id` se eu informei um BO, "
        "senão `texto_livre`.\n"
        "2. Para os pares mais relevantes, chame `obter_razoes_similaridade` "
        "para explicar as dimensões (semântica + razões estruturais) que ligam "
        "os BOs.\n"
        "3. Resuma os achados. Respeite a redação de PII conforme o perfil de "
        "acesso (consulte o resource `bnbo://dominio/perfis` em caso de dúvida)."
    )


def mapear_serie_criminal(bo_id: str = "", texto_livre: str = "") -> str:
    """Agrupa ocorrências similares em séries criminais."""
    alvo = f"o BO `{bo_id}`" if bo_id else f"o relato livre: «{texto_livre}»"
    return (
        f"Quero identificar séries criminais a partir de {alvo}.\n\n"
        "Chame `agrupar_serie_criminal` (DBSCAN sobre ocorrências similares) e "
        "apresente cada cluster com seu tamanho e coesão média, destacando o "
        "possível modus operandi comum. Veja `bnbo://dominio/glossario` para os "
        "conceitos de série criminal e similaridade."
    )


def detectar_anomalias(estado: str = "", dominio: str = "", natureza: str = "") -> str:
    """Detecta meses com volume anômalo de BOs (z-score)."""
    filtros = ", ".join(f"{k}={v}" for k, v in
                        (("estado", estado), ("dominio", dominio), ("natureza", natureza)) if v) or "sem filtro"
    return (
        f"Quero detectar anomalias estatísticas de volume de ocorrências "
        f"({filtros}).\n\n"
        "Chame `detectar_anomalias_estatisticas` com os filtros aplicáveis e "
        "explique os meses com z-score acima do limiar. Domínio válido: "
        "`pessoa` ou `patrimonio`."
    )


def avaliar_taxa_elucidacao(estado: str = "", delegacia: str = "") -> str:
    """Calcula a taxa de elucidação (inquéritos concluídos / total)."""
    filtros = ", ".join(f"{k}={v}" for k, v in
                        (("estado", estado), ("delegacia", delegacia)) if v) or "geral"
    return (
        f"Quero avaliar a taxa de elucidação ({filtros}).\n\n"
        "Chame `calcular_taxa_elucidacao` e interprete o resultado (inquéritos "
        "concluídos sobre o total). Aponte onde a taxa está baixa."
    )


def priorizar_delegacias(estado: str = "") -> str:
    """Combina anomalias de volume e baixa elucidação para priorizar delegacias."""
    filtro = f"no estado {estado}" if estado else "em todos os estados"
    return (
        f"Quero priorizar delegacias para atenção {filtro}.\n\n"
        "Chame `listar_delegacias_com_alerta`, que combina anomalias de volume "
        "com baixa taxa de elucidação, e ordene as delegacias por prioridade, "
        "justificando cada uma."
    )


def gerar_atlas_vulnerabilidade(estado: str = "", meses: int = 0) -> str:
    """Gera o ranking e o atlas (GeoJSON) de vulnerabilidade por hexágono H3."""
    periodo = f"dos últimos {meses} meses" if meses else "de todo o período"
    local = f"no estado {estado}" if estado else "em todo o território"
    return (
        f"Quero o Atlas de Vulnerabilidade Criminal {local}, {periodo}.\n\n"
        "1. Chame `calcular_indice_vulnerabilidade` para o ranking textual de "
        "hexágonos por IVC.\n"
        "2. Chame `gerar_atlas_vulnerabilidade` para o GeoJSON pronto para mapa "
        "(classes Jenks).\n"
        "Veja a metodologia e os pesos em `bnbo://dominio/metodologia-ivc`."
    )
