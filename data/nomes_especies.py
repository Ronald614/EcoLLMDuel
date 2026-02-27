# Dicionário de mapeamento: Nome da Pasta (Científico) -> Nome Comum
NOMES_COMUNS_ESPECIES = {
    "Crax globulosa": "Mutum-fava",
    "Didelphis albiventris": "Gambá-de-orelha-branca",
    "Leopardus wiedii": "Gato-maracajá",
    "Panthera onca": "Onça-pintada",
    "Pauxi tuberosa": "Mutum-cavalo",
    "Pauxituberosa": "Mutum-cavalo",
    "Sapajus macrocephalus": "Macaco-prego-de-cabeça-grande",
    "Sciurus spadiceus": "Esquilo-vermelho-da-Amazônia",
    "Tupinambis teguixin": "Teiú-branco",
    "background": "Esta foto não contém nenhum animal !"
}

def obter_nome_exibicao(especie_raw: str, incluir_cientifico: bool = False) -> str:
    # Casos especiais de erro
    if especie_raw == "erro_ou_desconhecido":
        return "Erro (Inventou Especie)"
    if especie_raw == "erro_formatacao":
        return "Erro (Formato Invalido)"

    nome_comum = especie_raw
    cientifico_formatado = especie_raw

    for chave, valor in NOMES_COMUNS_ESPECIES.items():
        if chave.replace(" ", "").lower() == especie_raw.replace(" ", "").lower():
            nome_comum = valor
            cientifico_formatado = chave
            break

    if incluir_cientifico and nome_comum != cientifico_formatado:
        return f"{nome_comum} ({cientifico_formatado})"
    
    return nome_comum
