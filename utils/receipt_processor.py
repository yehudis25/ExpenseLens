import easyocr
import ollama
import json
import re
import numpy as np
from PIL import Image

def extract_raw_text(image_input) -> str:
    """
    Uses EasyOCR to pull raw text lines out of the uploaded receipt image.
    Accepts a PIL Image or Streamlit UploadedFile object.
    """
    try:
        # Initialize the EasyOCR reader
        reader = easyocr.Reader(['en'], gpu=False)

        # Convert the uploaded file or image format into a numpy array for EasyOCR
        if hasattr(image_input, 'read'):
            img = Image.open(image_input)
            img_np = np.array(img)
        elif isinstance(image_input, Image.Image):
            img_np = np.array(image_input)
        else:
            img_np = image_input
        bounds = reader.readtext(img_np, detail=0)

        # Join lines together with line breaks to pass as a single document
        return "\n".join(bounds)
    except Exception as e:
        raise RuntimeError(f"EasyOCR text extraction failed: {str(e)}")

def structure_text_with_llm(raw_text: str) -> dict:
    """
    Feeds unstructured text to llama3.2:3b via Ollama to map it into clean JSON.
    """
    # prompt layout enforcing the fields required by project proposal
    prompt = f"""
    You are a data extraction assistant for the ExpenseLens app.
    Analyze the following raw OCR text extracted from a store receipt and return a valid JSON object.

    The JSON object MUST contain exactly these keys:
    - "store": (string, name of the store or merchant)
    - "date": (string, formatted as MM/DD/YYYY if found)
    - "total": (float, final absolute cost/total paid)
    - "items": (string, comma-separated names of products purchased)

    Do not include any introductory conversation, markdown code blocks (like ```json), or explanatory text.
    Only output the raw string containing the JSON object.

    Raw OCR Text:
    {raw_text}
    """

    try:
        # Generate token responses
        response = ollama.generate(
            model='llama3.2:3b',
            prompt=prompt,
            options={"temperature": 0.0}
        )

        response_text = response['response'].strip()

        # Strip away markdown code block symbols if Llama wraps the JSON output
        response_text = re.sub(r"^```json\s*|\s*```$", "", response_text, flags=re.MULTILINE).strip()

        # Convert the structural text string back into a real Python dictionary
        return json.loads(response_text)

    # except Exception:
    #     # fallback structure to ensure the app UI doesn't crash if processing fails
    #     return {
    #         "store": "Parsing Failure",
    #         "date": "Unknown Date",
    #         "total": 0.0,
    #         "items": "Could not format receipt data cleanly."
    #     }
    except Exception as e:
        print("=" * 50)
        print("DEBUG ERROR:", repr(e))
        try:
            print("DEBUG RAW RESPONSE:", response_text)
        except NameError:
            print("DEBUG: response_text was never set -- Ollama call itself failed")
            print("=" * 50)

        return {

            "store": "Parsing Failure",

            "date": "Unknown Date",

            "total": 0.0,

            "items": "Could not format receipt data cleanly."

        }

def process_receipt(image) -> dict:
    """
    Core Pipeline Orchestration: Chains the conversion steps together sequentially.
    """
    if image is None:
        return {"store": "", "date": "", "total": 0.0, "items": ""}

    raw_text = extract_raw_text(image)
    return structure_text_with_llm(raw_text)
