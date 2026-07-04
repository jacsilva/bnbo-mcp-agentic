# Metodologia do IVC — Índice de Vulnerabilidade Criminal

O IVC quantifica a vulnerabilidade criminal de uma área geográfica, agregando
Boletins de Ocorrência por hexágono e ponderando o tipo de crime.

## Passos

1. **Discretização espacial:** cada BO é atribuído a um hexágono **H3 de
   resolução 8** a partir de sua latitude/longitude.
2. **Ponderação por domínio:** as ocorrências do hexágono são somadas com peso
   por domínio — crimes contra a pessoa pesam mais que crimes patrimoniais na
   percepção de vulnerabilidade:

   | Domínio      | Peso |
   |--------------|------|
   | `pessoa`     | 2.0  |
   | `patrimonio` | 1.0  |
   | (outros)     | 1.0  |

   `score_bruto(hex) = Σ (total_ocorrencias_dominio × peso_dominio)`
3. **Normalização:** o IVC é o `score_bruto` dividido pelo maior `score_bruto`
   entre todos os hexágonos, resultando em um valor **entre 0 e 1**
   (arredondado a 4 casas).
4. **Classificação (Atlas):** para visualização em mapa, os valores de IVC são
   divididos em `n_classes` faixas via **Jenks natural breaks**
   (`1` = menor vulnerabilidade, `n_classes` = maior). O algoritmo minimiza a
   variância intra-classe (Fisher-Jenks).

## Tools relacionadas

- `calcular_indice_vulnerabilidade` — ranking textual de hexágonos por IVC.
- `gerar_atlas_vulnerabilidade` — GeoJSON com polígono por hexágono e a classe
  Jenks, pronto para plotagem.

Fonte de verdade da ponderação: `services/atlas.py` (`PESO_DOMINIO`).
