"""
Modelos Pydantic de argumentos das tools MCP.

As restrições de domínio (faixas numéricas, valores permitidos, campos
obrigatórios) ficam declaradas aqui, num só lugar, em vez de espalhadas como
`raise ValueError` no corpo de cada tool. A validação roda dentro da tool,
depois da coerção numérica (`coage_numericos`), via o decorator
`server.tools._validacao.valida_entrada`.

Importante: a *assinatura* das tools continua aceitando `int | str` / `float |
str` (ver `server.tools._coercao`) para tolerar números serializados como
string por LLMs cliente. A coerção normaliza o valor antes destes modelos
validarem a faixa; por isso os campos abaixo são tipados como `int`/`float`.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class _BuscaBase(BaseModel):
    """Base das tools que buscam por `bo_id` OU `texto_livre`."""

    bo_id: str = ""
    texto_livre: str = ""

    @model_validator(mode="after")
    def _exige_referencia(self):
        if not self.bo_id and not self.texto_livre:
            raise ValueError("Informe bo_id ou texto_livre.")
        return self


class BuscarOcorrenciasSimilaresArgs(_BuscaBase):
    top_k: int = Field(default=10, ge=1, le=100)


class ObterRazoesSimilaridadeArgs(BaseModel):
    bo_id_a: str = Field(min_length=1)
    bo_id_b: str = Field(min_length=1)


class AgruparSerieCriminalArgs(_BuscaBase):
    top_k: int = Field(default=30, ge=1, le=100)
    eps: float = Field(default=0.35, gt=0)
    min_samples: int = Field(default=2, ge=1)


class DetectarAnomaliasArgs(BaseModel):
    estado: str = ""
    dominio: str = ""
    natureza: str = ""
    limiar_z: float = Field(default=2.0, ge=0)


class CalcularTaxaElucidacaoArgs(BaseModel):
    estado: str = ""
    delegacia: str = ""
    natureza: str = ""


class ListarDelegaciasAlertaArgs(BaseModel):
    estado: str = ""
    limiar_z: float = Field(default=2.0, ge=0)
    taxa_elucidacao_max: float = Field(default=0.3, ge=0, le=1)


class SubscreverAlertasArgs(BaseModel):
    estado: str = ""
    desde_horas: int = Field(default=24, ge=1)


class CalcularIndiceVulnerabilidadeArgs(BaseModel):
    estado: str = ""
    meses: int = Field(default=0, ge=0)


class GerarAtlasVulnerabilidadeArgs(BaseModel):
    estado: str = ""
    meses: int = Field(default=0, ge=0)
    n_classes: int = Field(default=5, ge=2)


class ReindexarEmbeddingsArgs(BaseModel):
    batch_size: int = Field(default=100, ge=1)


class ConsultarJobStatusArgs(BaseModel):
    job_id: str = Field(min_length=1)


class ExportarResultadoArgs(BaseModel):
    dados_json: str = Field(min_length=1)
    formato: Literal["csv", "json", "geojson"] = "json"
