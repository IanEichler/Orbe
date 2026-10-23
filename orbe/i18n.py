"""Brazilian Portuguese presentation text; internal command keys stay stable."""
from pathlib import Path
import re
import sys

WORDS = {
    "Save": "Salvar", "Save copy": "Salvar cópia", "Apply": "Aplicar",
    "Compress": "Comprimir", "Resize": "Redimensionar", "Protect": "Proteger",
    "Brightness": "Brilho", "Contrast": "Contraste", "Saturation": "Saturação",
    "Warmth": "Temperatura", "Sharpness": "Nitidez", "Size": "Tamanho",
    "Quality": "Qualidade", "Width": "Largura", "Height": "Altura",
    "W": "L", "H": "A", "Padding": "Margem", "Corners": "Cantos",
    "Shadow": "Sombra", "Angle": "Ângulo", "Background": "Fundo",
    "Free": "Livre", "Auto": "Automático", "Aspect ratio": "Proporção",
    "Rotate 90°": "Girar 90°", "Double-click the image to reset": "Duplo clique para restaurar",
    "Custom colour": "Cor personalizada", "Background colour": "Cor do fundo",
    "Copy the result to the clipboard": "Copiar o resultado para a área de transferência",
    "Save with Background": "Salvar com fundo", "Copied ✓": "Copiado ✓", "Copy": "Copiar",
    "Sunset": "Pôr do sol", "Prism": "Prisma", "Peach": "Pêssego",
    "Mint": "Menta", "Ocean": "Oceano", "Dusk": "Crepúsculo",
    "Lemon": "Limão", "Night": "Noite", "Rose": "Rosa",
    "Undo": "Desfazer", "Redo": "Refazer", "➜ Arrow": "➜ Seta", "▢ Box": "▢ Caixa",
    "◯ Circle": "◯ Círculo", "✎ Pen": "✎ Caneta", "▬ Marker": "▬ Marca",
    "T Text": "T Texto", "① Step": "① Passo", "Type, then Enter": "Digite e pressione Enter",
    "Black box": "Tarja preta", "Pixelate": "Pixelizar", "Blur": "Desfocar",
    "Drag over anything you want hidden. It's burned into the pixels — it can't be undone in the copy.":
        "Arraste sobre o que deseja ocultar. A alteração é gravada nos pixels e fica permanente na cópia.",
    "✦ Auto": "✦ Automático", "Automatic light and colour": "Ajustar luz e cores automaticamente",
    "⇋ Flip": "⇋ Espelhar H", "⇵ Flip": "⇵ Espelhar V", "B&&W": "P&&B",
    "Hold to compare": "Segure para comparar", "Target size": "Tamanho desejado",
    "Original size": "Tamanho original", "Compressed": "Comprimido",
    "Make each file under": "Cada arquivo abaixo de",
    "Convert to WebP (usually the smallest)": "Converter para WebP (geralmente menor)",
    "Already well compressed — try a smaller size or WebP": "Já está bem comprimido. Tente reduzir as dimensões ou usar WebP.",
    "Presets — percent or longest side in px": "Predefinições — porcentagem ou lado maior em pixels",
    "Exact size": "Dimensões exatas", "Keep proportions": "Manter proporção",
    "No personal metadata found.": "Nenhum metadado pessoal encontrado.",
    "Open map": "Abrir mapa", "⚠  This photo reveals where it was taken.": "⚠  Esta foto revela onde foi tirada.",
    "Field": "Campo", "Value": "Valor", "Remove location only": "Remover só a localização",
    "Remove all metadata": "Remover todos os metadados", "Password": "Senha",
    "Confirm": "Confirmar", "Show": "Mostrar",
    "AES-256 encryption. Anyone opening the PDF will need this password.":
        "Criptografia AES-256. A senha será necessária para abrir o PDF.",
    "Use at least 4 characters.": "Use pelo menos 4 caracteres.",
    "Passwords don't match yet.": "As senhas ainda não coincidem.",
    "Camera": "Câmera", "Taken": "Data da foto", "Software": "Programa",
    "Exposure": "Exposição", "Aperture": "Abertura", "Location": "Localização",
    "Dimensions": "Dimensões", "Format": "Formato", "Mode": "Modo de cor",
    "Make": "Fabricante", "Model": "Modelo", "Orientation": "Orientação",
    "DateTime": "Data e hora", "DateTimeOriginal": "Data e hora originais",
    "DateTimeDigitized": "Data e hora da digitalização", "Artist": "Autor",
    "Copyright": "Direitos autorais", "ImageDescription": "Descrição da imagem",
    "ImageWidth": "Largura da imagem", "ImageLength": "Altura da imagem",
    "ExifImageWidth": "Largura EXIF", "ExifImageHeight": "Altura EXIF",
    "XResolution": "Resolução horizontal", "YResolution": "Resolução vertical",
    "ResolutionUnit": "Unidade de resolução", "ExposureTime": "Tempo de exposição",
    "FNumber": "Abertura da lente", "ExposureProgram": "Programa de exposição",
    "ISOSpeedRatings": "Sensibilidade ISO", "FocalLength": "Distância focal",
    "LensModel": "Modelo da lente", "LensMake": "Fabricante da lente",
    "WhiteBalance": "Balanço de branco", "ColorSpace": "Espaço de cor",
    "BrightnessValue": "Luminosidade", "ShutterSpeedValue": "Velocidade do obturador",
    "ApertureValue": "Valor de abertura", "MeteringMode": "Modo de medição",
    "ExposureBiasValue": "Compensação de exposição", "UserComment": "Comentário do usuário",
    "comment": "Comentário", "duration": "Duração", "loop": "Repetições",
    "transparency": "Transparência", "progressive": "Progressivo", "progression": "Progressão",
    "jfif": "Identificador JFIF", "jfif_version": "Versão JFIF", "jfif_unit": "Unidade JFIF",
    "jfif_density": "Densidade JFIF", "dpi": "Resolução (dpi)",
    "Pages": "Páginas", "title": "Título", "author": "Autor", "subject": "Assunto",
    "keywords": "Palavras-chave", "creator": "Programa de criação", "producer": "Gerador do PDF",
    "creationDate": "Data de criação", "modDate": "Data de modificação", "trapped": "Sobreposição de impressão",
    "format": "Formato", "encryption": "Criptografia",
}

SUFFIXES = {
    "Compressed": "Comprimido", "Cropped": "Recortado", "Edited": "Editado",
    "Annotated": "Anotado", "Redacted": "Ocultado", "With Background": "Com fundo",
    "Clean": "Sem metadados", "No Location": "Sem localização", "Combined": "Combinado",
    "Merged": "Unido", "Protected": "Protegido", "Rotated": "Girado",
}

GPS_FIELDS = {
    "GPSVersionID": "Versão", "GPSLatitudeRef": "Referência da latitude", "GPSLatitude": "Latitude",
    "GPSLongitudeRef": "Referência da longitude", "GPSLongitude": "Longitude",
    "GPSAltitudeRef": "Referência da altitude", "GPSAltitude": "Altitude", "GPSTimeStamp": "Horário",
    "GPSSatellites": "Satélites", "GPSStatus": "Estado", "GPSMeasureMode": "Modo de medição",
    "GPSDOP": "Diluição da precisão", "GPSSpeedRef": "Unidade de velocidade", "GPSSpeed": "Velocidade",
    "GPSTrackRef": "Referência do trajeto", "GPSTrack": "Direção do trajeto",
    "GPSImgDirectionRef": "Referência da direção da imagem", "GPSImgDirection": "Direção da imagem",
    "GPSMapDatum": "Referencial geodésico", "GPSDestLatitudeRef": "Referência da latitude de destino",
    "GPSDestLatitude": "Latitude de destino", "GPSDestLongitudeRef": "Referência da longitude de destino",
    "GPSDestLongitude": "Longitude de destino", "GPSDestBearingRef": "Referência do rumo de destino",
    "GPSDestBearing": "Rumo de destino", "GPSDestDistanceRef": "Unidade da distância de destino",
    "GPSDestDistance": "Distância de destino", "GPSProcessingMethod": "Método de processamento",
    "GPSAreaInformation": "Informações da área", "GPSDateStamp": "Data", "GPSDifferential": "Correção diferencial",
    "GPSHPositioningError": "Erro de posicionamento horizontal",
}


def translate(text):
    if text.startswith("GPS ") and text[4:] in GPS_FIELDS:
        return "GPS · " + GPS_FIELDS[text[4:]]
    if text.startswith("Max "):
        return "Máximo " + text[4:]
    return WORDS.get(text, text)


def output_suffix(text):
    if re.fullmatch(r"page \d+", text):
        return "página " + text[5:]
    return SUFFIXES.get(text, text)


def quantity(count, singular, plural=None):
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def install_portuguese(app):
    """Load Qt's bundled pt-BR strings, including file and colour dialogs."""
    from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
    QLocale.setDefault(QLocale("pt_BR"))
    if getattr(app, "_orbe_translator", None) is not None:
        return True
    translator = QTranslator(app)
    locations = [Path(QLibraryInfo.path(QLibraryInfo.TranslationsPath))]
    if getattr(sys, "frozen", False):
        locations.insert(0, Path(sys._MEIPASS) / "translations")
    for location in locations:
        if translator.load(str(location / "qtbase_pt_BR.qm")):
            app.installTranslator(translator)
            app._orbe_translator = translator
            return True
    return False
