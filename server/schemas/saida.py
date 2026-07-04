"""
Modelos Pydantic de resposta das tools MCP.

Cada tool valida o que devolve contra um destes modelos e serializa via
`Modelo.model_dump_json()` / `TypeAdapter(...).dump_json()`, em vez de
`json.dumps(..., default=str)` cru. Isso garante que o formato entregue ao
cliente bate com o contrato documentado e detecta divergências entre a camada
`ml`/SQL e o contrato.

As tools continuam retornando `str` (invariante de transporte do
`_erros.py`); estes modelos só padronizam o *conteúdo* dessa string.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, TypeAdapter


# --- P2 Linkage Criminal ---

class OcorrenciaSimilar(BaseModel):
    bo_id: str
    bo_numero: str
    natureza: str | None = None
    estado: str | None = None
    municipio: str | None = None
    relato: str | None = None
    data_hora: str
    score_semantico: float
    score_final: float
    razoes_estruturais: dict[str, float] = {}


class RazaoSimilaridade(BaseModel):
    bo_id_a: str
    bo_id_b: str
    score_semantico: float
    razoes_estruturais: dict[str, float] = {}
    contribuicoes_pesadas: dict[str, float] = {}
    score_final: float


class ClusterSerie(BaseModel):
    cluster_id: int
    tamanho: int
    coesao_media: float
    membros: list[OcorrenciaSimilar]


class SerieCriminal(BaseModel):
    clusters: list[ClusterSerie]
    ruido: list[OcorrenciaSimilar]


# --- P1 Observatório ---

class AnomaliaEstatistica(BaseModel):
    estado: str | None = None
    municipio: str | None = None
    dominio: str | None = None
    natureza: str | None = None
    mes: str
    total_ocorrencias: int
    z_score: float


class TaxaElucidacao(BaseModel):
    delegacia: str | None = None
    estado: str | None = None
    natureza: str | None = None
    total_inqueritos: int
    concluidos: int
    taxa_elucidacao: float


class DelegaciasComAlerta(BaseModel):
    anomalias_volume: list[AnomaliaEstatistica]
    delegacias_baixa_elucidacao: list[TaxaElucidacao]


class AlertaObservatorio(BaseModel):
    estado: str | None = None
    municipio: str | None = None
    dominio: str | None = None
    natureza: str | None = None
    mes: date
    z_score: float
    criado_em: datetime


# --- P4 Atlas de Vulnerabilidade ---

class HexagonoVulnerabilidade(BaseModel):
    hex_id: str
    estado: str | None = None
    municipio: str | None = None
    total_ocorrencias: int
    ivc: float


class _PropriedadesAtlas(BaseModel):
    hex_id: str
    estado: str | None = None
    municipio: str | None = None
    total_ocorrencias: int
    ivc: float
    classe_vulnerabilidade: int


class _GeometriaGeoJSON(BaseModel):
    type: str
    coordinates: Any


class FeatureAtlas(BaseModel):
    type: str = "Feature"
    geometry: _GeometriaGeoJSON
    properties: _PropriedadesAtlas


class AtlasGeoJSON(BaseModel):
    type: str = "FeatureCollection"
    features: list[FeatureAtlas]


# --- Jobs assíncronos ---

class JobDisparo(BaseModel):
    job_id: str
    status: str


class JobStatus(BaseModel):
    job_id: str
    estado: str
    progresso: Any | None = None
    resultado: Any | None = None
    erro: str | None = None


# --- Adapters para retornos que são listas / dicts simples ---

ListaOcorrenciasSimilares = TypeAdapter(list[OcorrenciaSimilar])
ListaAnomalias = TypeAdapter(list[AnomaliaEstatistica])
ListaTaxasElucidacao = TypeAdapter(list[TaxaElucidacao])
ListaAlertas = TypeAdapter(list[AlertaObservatorio])
ListaHexagonos = TypeAdapter(list[HexagonoVulnerabilidade])
RegioesDisponiveis = TypeAdapter(dict[str, list[str]])
