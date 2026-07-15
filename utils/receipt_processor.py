# import easyocr
import ollama
# import json
import re
# import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pathlib import Path
import streamlit as st
import pytesseract
# import torch
# from transformers import pipeline
from pydantic import BaseModel, Field, ValidationError
from typing import List
import hashlib

# USE_GPU = torch.cuda.is_available()
# DEVICE = 0 if USE_GPU else -1

@st.cache_resource(show_spinner="Loading OCR engine...")
def get_reader():
    import easyocr
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    return easyocr.Reader(['en'], gpu=False, verbose=False,)

# @st.cache_resource
# def get_hf_pipeline():
#     return pipeline(
#         "image-to-text", 
#         model="microsoft/trocr-base-printed", 
#         device=DEVICE
#     )

def warm_llm():
    try:
        ollama.generate(
            model="llama3.2:1b",
            prompt="ping",
            options={"num_predict": 1}
        )
    except Exception as e:
        print(f"LLM warming skipped or failed: {e}")

# warm_llm()

def receipt_check(text: str) -> bool:
    """
    Very simple keyword-based receipt/invoice detector.
    Works even with messy OCR.
    """
    if not text:
        return False

    text_lower = text.lower()

    receipt_keywords = [
        "total", "subtotal", "tax", "amount", "change", "cash", "debit",
        "credit", "visa", "mastercard", "receipt", "thank you", "store",
        "item", "qty", "quantity", "price"
    ]

    invoice_keywords = ["invoice", "bill to", "ship to", "due date", "invoice number","balance due", "amount due"]

    # If any receipt or invoice keyword appears → treat as valid
    return any(k in text_lower for k in receipt_keywords + invoice_keywords)

def prevent_duplicate_receipt_by_text(raw_text):
    if "receipt_texts" not in st.session_state:
        st.session_state.receipt_texts = set()

    normalized = re.sub(r"\s+", " ", raw_text.lower()).strip()

    if normalized in st.session_state.receipt_texts:
        st.error("This receipt has already been uploaded.")
        st.stop()
    else:
        st.session_state.receipt_texts.add(normalized)

def extract_raw_text(image_input) -> str:
    try:
        if isinstance(image_input, (str, Path)):
            image = Image.open(image_input)
        elif hasattr(image_input, "read"):
            image_input.seek(0)
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            raise TypeError(
                f"Unsupported image input: {type(image_input).__name__}"
            )

        image = ImageOps.exif_transpose(image).convert("RGB")

        # Avoid processing unnecessarily large images.
        image.thumbnail(
            (1800, 1800),
            Image.Resampling.LANCZOS,
        )

        # Improve receipt contrast.
        image = ImageOps.grayscale(image)
        image = ImageEnhance.Contrast(image).enhance(1.8)
        image = image.filter(ImageFilter.SHARPEN)

        text = pytesseract.image_to_string(
            image,
            lang="eng",
            config="--oem 3 --psm 6",
            timeout=30,
        )

        return text.strip()

    except RuntimeError as exc:
        raise RuntimeError(
            f"Tesseract OCR timed out: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Tesseract OCR failed: {exc}") from exc
# Pydantic models
class Item(BaseModel):
    name: str = Field(default="")
    price: float = Field(default=0.0)

class Receipt(BaseModel):
    store: str = Field(default="")
    date: str = Field(default="")
    total: float = Field(default=0.0)
    items: List[Item] = Field(default_factory=list)

# def structure_text_with_llm(raw_text: str) -> dict:
#     """
#     Sends OCR text to Llama and safely extracts valid JSON.
#     Repairs common LLL formatting issues before json.loads().
#     """
#     prompt = """
#     You are an extraction assistant for the ExpenseLens app.
#     Your job is to extract structured receipt data from messy OCR text.

#     ### REQUIRED FIELDS
#     - store: string (never blank)
#     - date: string (never blank)
#     - total: number (never blank)
#     - items: list of objects with:
#         - name: string
#         - price: number

#     ### EXTRACTION RULES
#     1. If the OCR text contains item lines (e.g., "Milk 3.99"), extract them.
#     2. If item names are missing, infer them from context (e.g., "Item 1").
#     3. If prices appear without names, still create an item with a placeholder name.
#     4. If store or date are missing, infer reasonable placeholders:
#         - store: "Unknown Store"
#         - date: "Unknown Date"
#     5. If total is missing, sum item prices.

#     ### OUTPUT FORMAT
#     Return ONLY valid JSON in this exact structure:

#     {
#     "store": "",
#     "date": "",
#     "total": 0,
#     "items": [
#         {
#         "name": "",
#         "price": 0
#         }
#     ]
#     }

#     OCR Text:
#     """ + raw_text

#     try:
#         response = ollama.generate(
#             model='llama3.2:1b',
#             prompt=prompt,
#             options={"temperature": 0.0, "num_predict": 512}
#         )

#         raw = response["response"].strip()

#         # Extract the first JSON object
#         match = re.search(r"\{.*\}", raw, re.DOTALL)
#         if not match:
#             raise ValueError("No JSON object found in model output")

#         json_text = match.group(0)

#         # Remove trailing backslashes that break JSON
#         json_text = re.sub(r"\\\s*$", "", json_text, flags=re.MULTILINE)
#         json_text = json_text.replace('\\"', '"')
#         print("RAW MODEL OUTPUT:")
#         print(raw)
#         data = json.loads(json_text)

#         # pydantic validation
#         validated = Receipt(**data)
#         return validated.model_dump()

#     except Exception as e:
#         print("=" * 50)
#         print("DEBUG ERROR:", repr(e))
#         print("DEBUG RAW RESPONSE:", raw if 'raw' in locals() else "No response")
#         print("=" * 50)

#         return {
#             "store": "Parsing Failure",
#             "date": "Unknown Date",
#             "total": 0.0,
#             "items": "Could not format receipt data cleanly."
#         }
def structure_text_with_llm(raw_text: str) -> dict:
    client = ollama.Client(
        host="http://127.0.0.1:11434",
        timeout=120,)

    # Avoid sending unnecessarily large or repeated OCR output.
    raw_text = raw_text[:8000]

    prompt = f"""
You are an extraction assistant for the ExpenseLens app.
Your job is to extract structured receipt data from messy OCR text.

### REQUIRED FIELDS
- store: string (never blank)
- date: string (never blank)
- total: number (never blank)
- items: list of objects with:
    - name: string
    - price: number

### EXTRACTION RULES
1. If the OCR text contains item lines (e.g., "Milk 3.99"), extract them.
2. If item names are missing, infer them from context (e.g., "Item 1").
3. If prices appear without names, still create an item with a placeholder name.
4. If store or date are missing, infer reasonable placeholders:
    - store: "Unknown Store"
    - date: "Unknown Date"
5. If total is missing, sum item prices.

### OUTPUT FORMAT
Return ONLY valid JSON in this exact structure — do NOT include explanations, markdown, or code fences:

{{
"store": "Unknown Store",
"date": "Unknown Date",
"total": 0.0,
"items": [
    {{
    "name": "",
    "price": 0
    }}
]
}}

### OCR TEXT TO PARSE
{raw_text}

### INSTRUCTIONS
Now extract and return ONLY the JSON object.
"""

    try:
        print("Starting structured extraction...", flush=True)

        response = client.generate(
            model="llama3.2:1b",
            prompt=prompt,
            format=Receipt.model_json_schema(),
            options={
                "temperature": 0,
                "num_predict": 256,
                "num_ctx": 2048,
            },
            keep_alive="5m",
        )

        raw_response = response["response"]

        print("RAW STRUCTURED RESPONSE:", flush=True)
        print(raw_response, flush=True)
        
        print("OCR characters sent:", len(raw_text), flush=True)
        print("OCR preview:", raw_text[:300], flush=True)
        validated = Receipt.model_validate_json(raw_response)

        # validated = Receipt.model_validate_json(
        #     response["response"]
        # )

        return validated.model_dump()

    except Exception as exc:
        print(f"Structured extraction failed: {exc}", flush=True)

        return {
            "store": "Parsing Failure",
            "date": "Uknown",
            "total": 0.0,
            "items": [],
        }

def process_receipt(raw_text: str):
    """
    Core Pipeline Orchestration: Chains the conversion steps together sequentially.
    # """
    # if image is None:
    #     return {"store": "", "date": "", "total": 0.0, "items": ""}

    # raw_text = extract_raw_text(image)
    # st.write("OCR Text:")
    # st.code(raw_text)
    return structure_text_with_llm(raw_text)
