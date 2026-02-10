from PIL import Image
import base64
from io import BytesIO

def codificar_imagem(imagem: Image.Image) -> str:
    """Converte imagem PIL para string base64."""
    buffer = BytesIO()
    imagem.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")