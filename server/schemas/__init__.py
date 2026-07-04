"""
Contratos de validação Pydantic das tools MCP.

`entrada` reúne os modelos de argumentos (restrições de domínio declarativas,
validadas no corpo da tool via `server.tools._validacao.valida_entrada`).
`saida` reúne os modelos de resposta, usados para validar e serializar o
retorno de cada tool em vez de `json.dumps` cru — garantindo que o formato
devolvido ao cliente bate com o contrato documentado.
"""
