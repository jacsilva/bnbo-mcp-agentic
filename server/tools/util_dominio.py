"""
Tools utilitárias transversais — export de resultados e metadados de domínio.
"""

import csv
import io
import json

from server.recursos.dominio import consultar_regioes
from server.schemas.entrada import ExportarResultadoArgs
from server.schemas.saida import RegioesDisponiveis
from server.security.auditoria import com_auditoria
from server.tools._erros import tratar_erros
from server.tools._validacao import valida_entrada


@com_auditoria("exportar_resultado")
@tratar_erros
@valida_entrada(ExportarResultadoArgs)
def exportar_resultado_tool(dados_json: str, formato: str = "json") -> str:
    """
    Converte o resultado JSON de outra tool (ex.: buscar_ocorrencias_similares)
    para o formato solicitado: csv, json ou geojson.

    Use esta tool quando o usuário quiser baixar/exportar um resultado já
    obtido em outro formato, em vez de receber o JSON bruto.

    Args:
        dados_json (str): JSON (lista de objetos ou dict com "clusters"/"membros")
                           retornado por outra tool do domínio.
        formato (str): Um de "csv", "json" ou "geojson" (default "json").

    Returns:
        str: Conteúdo já formatado no formato solicitado.
    """
    dados = json.loads(dados_json)
    registros = dados if isinstance(dados, list) else dados.get("clusters") or dados.get("membros") or [dados]

    if formato == "json":
        return json.dumps(registros, ensure_ascii=False, default=str)

    if formato == "csv":
        if not registros:
            return ""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(registros[0].keys()))
        writer.writeheader()
        for registro in registros:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                              for k, v in registro.items()})
        return buffer.getvalue()

    if formato == "geojson":
        features = []
        for registro in registros:
            lat, lng = registro.get("lat"), registro.get("lng")
            if lat is None or lng is None:
                continue
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lng, lat]},
                "properties": {k: v for k, v in registro.items() if k not in ("lat", "lng")},
            })
        return json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, default=str)

    # `formato` é validado como Literal["csv", "json", "geojson"] em
    # ExportarResultadoArgs, então os três ramos acima cobrem todos os casos.


@com_auditoria("listar_regioes_disponiveis")
@tratar_erros
def listar_regioes_disponiveis_tool() -> str:
    """
    Lista os estados e municípios com Boletins de Ocorrência cadastrados na base.

    Use esta tool quando o usuário quiser saber quais regiões podem ser
    consultadas antes de fazer uma busca geográfica ou estatística.

    Returns:
        str: JSON com a lista de estados e, para cada um, os municípios
             disponíveis.
    """
    return RegioesDisponiveis.dump_json(RegioesDisponiveis.validate_python(consultar_regioes())).decode()
