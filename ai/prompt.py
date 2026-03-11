# --- PROMPT ---
PROMPT_TEMPLATE = """
Você é um biólogo especialista em vida selvagem e reconhecimento de imagem.

Tarefa:
Analise esta imagem de armadilha fotográfica e descreva detalhadamente o que é visível. Caso haja animais na imagem, identifique a espécie presente, informando o nome científico, o nome comum e o número de indivíduos detectados, considere imagens no contexto da selva amazônica brasileira.

Formato de saída:
Retorne a análise estritamente em formato JSON, sem qualquer texto adicional, contendo obrigatoriamente os seguintes campos:

- "deteccao": "Sim" se algum animal for detectado, caso contrário "Nenhuma".
- "nome_cientifico": Nome científico da espécie detectada sem abreviações ou "Nenhum".
- "nome_comum": Nome comum da espécie detectada ou "Nenhum".
- "numero_individuos": Quantidade numérica de indivíduos detectados ou "Nenhum".
- "descricao_imagem": Descrição detalhada dos elementos visíveis na imagem.
- "razao": Justificativa baseada nas características visuais observadas que levaram à conclusão.

Condição de exceção:
Se nenhum animal for detectado, retorne 'Nenhum' em todos os campos exceto em "descricao_imagem" e "razao", que devem conter apenas a descrição visual da cena e a justificativa para essa classificação.
"""