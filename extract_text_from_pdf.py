import os
from pdf2image import convert_from_path
import pytesseract
import re

# Ruta del PDF a procesar
pdf_path = "documento.pdf"  # Asegúrate de que el PDF existe
output_text_file = "output.txt"


# Expresión regular para limpiar ruido OCR sin eliminar texto real
def clean_text(text):
    """Limpia el texto extraído eliminando caracteres extraños sin borrar contenido útil."""
    text = re.sub(
        r"[<>|=]+", "", text
    )  # Elimina caracteres raros sin eliminar palabras
    text = re.sub(
        r"[^A-Za-zÁÉÍÓÚáéíóúñÑ0-9,.¡!¿?()\s]", "", text
    )  # Mantiene letras, números y puntuación básica
    text = re.sub(
        r"\b[a-zA-Z]\b", "", text
    )  # Elimina letras sueltas (pero no palabras reales)
    text = re.sub(
        r"\s+", " ", text
    ).strip()  # Reduce espacios repetidos y limpia bordes
    return text


# Verificar que el PDF existe
if not os.path.exists(pdf_path):
    print(f"Error: No se encontró el archivo {pdf_path}. Verifica la ruta.")
    exit(1)

# Convertir todas las páginas del PDF a imágenes
print(" Convirtiendo PDF a imágenes...")
pages = convert_from_path(pdf_path, dpi=300)

if not pages:
    print(" Error: No se pudo convertir el PDF a imágenes.")
    exit(1)

extracted_text = []

# Procesar cada página
for i, page in enumerate(pages):
    image_path = f"page_{i+1}.png"
    page.save(image_path, "PNG")
    print(f" Página {i+1} convertida a imagen: {image_path}")

    # Verificar si la imagen se creó correctamente
    if not os.path.exists(image_path):
        print(f" Error: No se encontró la imagen {image_path}.")
        continue

    # Realizar OCR con Tesseract
    print(f"Ejecutando OCR en la página {i+1}...")
    try:
        raw_text = pytesseract.image_to_string(image_path, lang="spa")
        cleaned_text = clean_text(raw_text)

        if cleaned_text.strip():
            print(f"OCR completado en página {i+1}.")
            extracted_text.append(f"--- Página {i+1} ---\n{cleaned_text}")
        else:
            print(f"Advertencia: No se detectó texto en la página {i+1}.")
    except Exception as e:
        print(f" Error al realizar OCR en la página {i+1}: {e}")

# Guardar el texto extraído en un archivo
if extracted_text:
    try:
        with open(output_text_file, "w", encoding="utf-8") as f:
            f.write("\n\n".join(extracted_text))
        print(f"Texto extraído limpio guardado en {output_text_file}")
    except Exception as e:
        print(f" Error al guardar el archivo de texto: {e}")
else:
    print("⚠️ No se extrajo texto de ninguna página.")
