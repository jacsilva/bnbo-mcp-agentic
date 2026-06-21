"""
Gerador de Boletins de Ocorrência sintéticos.

Permite desenvolver e testar o slice do P2 (Linkage Criminal) sem depender
de convênios com dados reais. Gera relatos plausíveis por natureza, com
coordenadas aproximadas, e popula a tabela `bo` com embeddings já calculados.
"""

import argparse
import random
import uuid
from datetime import datetime, timedelta

from data.db import get_connection
from ml.embeddings import EmbeddingEngine

ESTADOS = ["SP", "RJ", "MG", "BA", "RS"]

NATUREZAS = {
    "furto": [
        "Vítima relatou que teve {item} furtado enquanto estava em {local}.",
        "Subtração de {item} ocorrida em {local}, sem uso de violência.",
    ],
    "roubo": [
        "Autor abordou a vítima em {local} e, mediante grave ameaça, subtraiu {item}.",
        "Roubo de {item} próximo a {local}, autor portava {instrumento}.",
    ],
    "lesao_corporal": [
        "Discussão entre vítima e autor em {local} resultou em agressão física.",
        "Vítima foi agredida com {instrumento} durante desentendimento em {local}.",
    ],
    "ameaca": [
        "Autor ameaçou a vítima verbalmente em {local} após discussão.",
        "Vítima relatou receber ameaças repetidas do autor, conhecido, em {local}.",
    ],
}

ITENS = ["celular", "bicicleta", "carteira", "notebook", "veículo", "bolsa"]
LOCAIS = ["via pública", "residência da vítima", "estabelecimento comercial", "transporte público"]
INSTRUMENTOS = ["faca", "arma de fogo", "objeto contundente", None]

DOMINIO_POR_NATUREZA = {
    "furto": "patrimonio",
    "roubo": "patrimonio",
    "lesao_corporal": "pessoa",
    "ameaca": "pessoa",
}

# Bounding boxes aproximados (lat_min, lat_max, lng_min, lng_max) por estado.
BBOX_ESTADO = {
    "SP": (-24.5, -20.0, -50.0, -44.0),
    "RJ": (-23.5, -20.5, -44.5, -40.5),
    "MG": (-22.5, -14.0, -51.0, -39.5),
    "BA": (-18.5, -8.5, -46.5, -37.0),
    "RS": (-33.5, -27.0, -57.5, -49.5),
}


def _gerar_relato(natureza: str) -> tuple[str, str | None]:
    template = random.choice(NATUREZAS[natureza])
    item = random.choice(ITENS)
    local = random.choice(LOCAIS)
    instrumento = random.choice(INSTRUMENTOS)
    relato = template.format(item=item, local=local, instrumento=instrumento or "objeto não identificado")
    return relato, instrumento


def gerar_bo() -> dict:
    estado = random.choice(ESTADOS)
    lat_min, lat_max, lng_min, lng_max = BBOX_ESTADO[estado]
    natureza = random.choice(list(NATUREZAS.keys()))
    relato, instrumento = _gerar_relato(natureza)
    data_hora = datetime.now() - timedelta(days=random.randint(0, 730), hours=random.randint(0, 23))

    return {
        "bo_numero": str(uuid.uuid4())[:8].upper(),
        "estado": estado,
        "municipio": f"Municipio-{random.randint(1, 50)}",
        "data_hora": data_hora,
        "lat": round(random.uniform(lat_min, lat_max), 6),
        "lng": round(random.uniform(lng_min, lng_max), 6),
        "dominio": DOMINIO_POR_NATUREZA[natureza],
        "natureza": natureza,
        "relato": relato,
        "vitima_perfil": {"genero": random.choice(["F", "M"]), "faixa_etaria": random.choice(["18-25", "26-40", "41-60", "60+"])},
        "autor_perfil": {"vinculo": random.choice(["desconhecido", "conhecido", "familiar"])},
        "instrumento": instrumento,
        "status": random.choice(["registrado", "investigacao", "elucidado"]),
    }


DELEGACIAS_POR_ESTADO = {
    estado: [f"{estado}ª Delegacia {n}" for n in range(1, 6)] for estado in ESTADOS
}


def _gerar_inquerito(bo_id: str, estado: str, data_hora, status_bo: str) -> dict | None:
    """Gera um inquérito para BOs com status 'investigacao'/'elucidado' (ETL real
    de matching bo_id↔inquerito ainda não implementada — ver nota no README)."""
    if status_bo not in ("investigacao", "elucidado"):
        return None
    aberto_em = data_hora + timedelta(days=random.randint(1, 5))
    status_inquerito = "concluido" if status_bo == "elucidado" else random.choice(["em_andamento", "concluido"])
    concluido_em = aberto_em + timedelta(days=random.randint(10, 180)) if status_inquerito == "concluido" else None
    return {
        "bo_id": bo_id,
        "numero": str(uuid.uuid4())[:8].upper(),
        "delegacia": random.choice(DELEGACIAS_POR_ESTADO[estado]),
        "estado": estado,
        "status": status_inquerito,
        "aberto_em": aberto_em,
        "concluido_em": concluido_em,
    }


def popular_base(n: int, batch_size: int = 50) -> None:
    engine = EmbeddingEngine()
    registros = [gerar_bo() for _ in range(n)]

    with get_connection() as conn:
        for i in range(0, len(registros), batch_size):
            batch = registros[i : i + batch_size]
            embeddings = engine.embed_passages([r["relato"] for r in batch])
            with conn.cursor() as cur:
                for registro, vetor in zip(batch, embeddings):
                    cur.execute(
                        """
                        INSERT INTO bo (
                            bo_numero, estado, municipio, data_hora, lat, lng,
                            dominio, natureza, relato, vitima_perfil, autor_perfil,
                            instrumento, status, embedding
                        ) VALUES (%(bo_numero)s, %(estado)s, %(municipio)s, %(data_hora)s,
                                  %(lat)s, %(lng)s, %(dominio)s, %(natureza)s, %(relato)s,
                                  %(vitima_perfil)s, %(autor_perfil)s, %(instrumento)s,
                                  %(status)s, %(embedding)s)
                        RETURNING id
                        """,
                        {**registro, "vitima_perfil": __import__("json").dumps(registro["vitima_perfil"]),
                         "autor_perfil": __import__("json").dumps(registro["autor_perfil"]),
                         "embedding": vetor},
                    )
                    bo_id = cur.fetchone()[0]
                    inquerito = _gerar_inquerito(bo_id, registro["estado"], registro["data_hora"], registro["status"])
                    if inquerito:
                        cur.execute(
                            """
                            INSERT INTO inquerito (bo_id, numero, delegacia, estado, status, aberto_em, concluido_em)
                            VALUES (%(bo_id)s, %(numero)s, %(delegacia)s, %(estado)s, %(status)s, %(aberto_em)s, %(concluido_em)s)
                            """,
                            inquerito,
                        )
            conn.commit()
            print(f"Inseridos {min(i + batch_size, n)}/{n} BOs sintéticos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de BOs sintéticos.")
    parser.add_argument("--n", type=int, default=500, help="Número de BOs a gerar.")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()
    popular_base(args.n, args.batch_size)
