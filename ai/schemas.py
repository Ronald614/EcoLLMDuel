from pydantic import BaseModel, Field
from typing import Literal

class AnaliseBiologica(BaseModel):
    deteccao: Literal["Sim", "Nenhuma"] = Field(..., description="Indica se algum animal foi detectado na imagem.")
    nome_cientifico: str = Field(..., description="Nome científico da espécie detectada ou 'Nenhum'.")
    nome_comum: str = Field(..., description="Nome comum da espécie detectada ou 'Nenhum'.")
    numero_individuos: str = Field(..., description="Quantidade numérica de indivíduos ou 'Nenhum'.")
    descricao_imagem: str = Field(..., description="Descrição detalhada dos elementos visíveis na imagem.")
    razao: str = Field(..., description="Justificativa baseada nas características visuais.")


