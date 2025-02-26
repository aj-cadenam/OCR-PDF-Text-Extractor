import base64
import requests
import os
import json
import time
from pdf2image import convert_from_path
from PIL import Image, ImageOps

# 🔹 Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llava"  # CHECK THIS with `ollama list`
SYSTEM_PROMPT = "Extract the exact text from the image. Preserve spacing, punctuation, and line breaks."
TIMEOUT = 120
MAX_RETRIES = 3
PAUSE_BETWEEN_REQUESTS = 2  # To prevent API overload

# 🔹 PDF to Images
pdf_path = "documento.pdf"
image_folder = "imagenes"
os.makedirs(image_folder, exist_ok=True)
pages = convert_from_path(pdf_path, dpi=300)
image_paths = [os.path.join(image_folder, f"page_{i+1}.png") for i in range(len(pages))]

for i, page in enumerate(pages):
    page.save(image_paths[i], "PNG")
    print(f"✅ Page {i+1} saved as {image_paths[i]}")


def process_image(image_path):
    """Preprocess and encode image in Base64."""
    try:
        with Image.open(image_path) as img:
            img.thumbnail((2000, 2000), Image.LANCZOS)
            img = ImageOps.grayscale(img)
            temp_path = image_path.replace(".png", "_optimized.jpg")
            img.save(temp_path, "JPEG", quality=85)

        with open(temp_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        os.remove(temp_path)

        return encoded_string
    except Exception as e:
        print(f"⚠️ Error processing image '{image_path}': {e}")
        return None


def perform_ocr(image_path):
    """Send image to Ollama for OCR processing, handling streaming responses."""
    base64_image = process_image(image_path)
    if not base64_image:
        return None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": SYSTEM_PROMPT,
                            "images": [base64_image],
                        }
                    ],
                },
                timeout=TIMEOUT,
                stream=True,  # Enable streaming
            )

            if response.status_code != 200:
                print(
                    f"⚠️ Attempt {attempt+1}: Error {response.status_code} - {response.text}"
                )
                continue

            full_text = ""  # Store the extracted text
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(
                            line.decode("utf-8")
                        )  # Process each JSON line separately
                        content = (
                            json_response.get("message", {}).get("content", "").strip()
                        )
                        if content:
                            full_text += content + " "
                    except json.JSONDecodeError:
                        print("⚠️ Ignoring a malformed JSON line in response.")

            return full_text.strip() if full_text else None

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt+1}: Request error - {e}")

        time.sleep(PAUSE_BETWEEN_REQUESTS)

    print(
        f"❌ Failed to extract text from '{image_path}' after {MAX_RETRIES} attempts."
    )
    return None


def save_to_markdown(text, markdown_path):
    """Save extracted text to a Markdown file."""
    if text:
        with open(markdown_path, "w", encoding="utf-8") as md_file:
            md_file.write(text)
        print(f"✅ Text saved in '{markdown_path}'")
    else:
        print(f"⚠️ No text extracted for '{markdown_path}'.")


if __name__ == "__main__":
    if not image_paths:
        print("❌ No images generated from PDF.")
        exit(1)

    start_time = time.time()

    # Sequential processing (no parallel execution)
    for img_path in image_paths:
        text = perform_ocr(img_path)
        if text:
            save_to_markdown(text, img_path.replace(".png", ".md"))
        time.sleep(PAUSE_BETWEEN_REQUESTS)  # Prevents API overload

    print(f"⏳ Total processing time: {time.time() - start_time:.2f} seconds")
