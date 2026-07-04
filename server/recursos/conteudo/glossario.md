# Glossário do domínio — Segurança Pública (BNBO)

Termos usados pelas tools e resources deste servidor MCP.

- **BO (Boletim de Ocorrência):** registro de uma ocorrência policial, com
  relato em texto livre, data/hora, localização (lat/lng), natureza e perfis de
  vítima/autor. É a unidade básica de análise.
- **Inquérito:** investigação criminal vinculada a um BO. Tem delegacia
  responsável, status e datas de abertura/conclusão. Base do cálculo de
  **taxa de elucidação**.
- **TCO (Termo Circunstanciado de Ocorrência):** registro de infração de menor
  potencial ofensivo, também vinculado a um BO.
- **Natureza:** tipificação da ocorrência (ex.: roubo, furto, lesão corporal).
- **Domínio:** agrupamento da natureza em `pessoa` (crimes contra a pessoa) ou
  `patrimonio` (crimes patrimoniais). Pondera o **IVC**.
- **Série criminal:** conjunto de BOs atribuíveis a um mesmo autor/modus
  operandi, identificado por agrupamento (DBSCAN) de ocorrências similares.
- **Similaridade:** combinação de score semântico (embeddings do relato) com
  razões estruturais (instrumento, modus, geografia, temporalidade).
- **H3 (resolução 8):** grade hexagonal global usada para discretizar o
  território; cada hexágono agrega ocorrências para o Atlas.
- **IVC (Índice de Vulnerabilidade Criminal):** índice 0–1 por hexágono H3,
  soma ponderada de ocorrências por domínio, normalizada pelo hexágono de maior
  incidência. Ver `bnbo://dominio/metodologia-ivc`.
- **Jenks (natural breaks):** método de classificação dos valores de IVC em
  faixas de vulnerabilidade para legenda de mapa.
- **Anomalia estatística:** mês cujo volume de BOs desvia do padrão histórico,
  medido por **z-score** (limiar configurável).
- **Taxa de elucidação:** inquéritos concluídos / total de inquéritos, por
  delegacia, estado ou natureza.
- **Perfis de acesso:** `publico` < `analista` < `investigador`, em ordem
  crescente de privilégio. Controlam a redação de PII. Ver `bnbo://dominio/perfis`.
