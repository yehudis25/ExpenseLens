import easyocr
import ollama
import json
import re
import numpy as np
from PIL import Image
import streamlit as st
import torch
from transformers import pipeline

USE_GPU = torch.cuda.is_available()
DEVICE = 0 if USE_GPU else -1

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'], gpu=USE_GPU)

@st.cache_resource
def get_hf_pipeline():
    return pipeline(
        "image-to-text", 
        model="microsoft/trocr-base-printed", 
        device=DEVICE
    )
def warm_llm():
    try:
        ollama.generate(
            model="llama3.2:1b",
            prompt="ping",
            options={"num_predict": 1}
        )
    except Exception as e:
        print(f"LLM warming skipped or failed: {e}")

warm_llm()


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

    invoice_keywords = [
        "invoice", "bill to", "ship to", "due date", "invoice number",
        "balance due", "amount due"
    ]

    # If any receipt or invoice keyword appears → treat as valid
    return any(k in text_lower for k in receipt_keywords + invoice_keywords)


def extract_raw_text(image_input) -> str:
    """
    Uses EasyOCR to pull raw text lines out of the uploaded receipt image.
    Accepts a PIL Image or Streamlit UploadedFile object.
    """
    try:
        # Initialize the EasyOCR reader
        reader = get_reader()

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
    Sends OCR text to Llama and safely extracts valid JSON.
    Repairs common LLM formatting issues before json.loads().
    """
    prompt = f"""
    You are a data extraction assistant for the ExpenseLens app.
    Analyze the following raw OCR text extracted from a store receipt and return a valid JSON object.
    
    Return ONLY valid JSON.

    Format:
    {{
     "store": "",
     "date": "",
     "total": 0,
     "items": [
       {{
        "name": "",
        "price": 0
       }}
     ]
    }}

    Do not include explanations.

    Raw OCR Text:
    {raw_text}
    """

    try:
        response = ollama.generate(
            model='llama3.2:1b',
            prompt=prompt,
            options={"temperature": 0.0, "num_predict": 512}
        )

        raw = response["response"].strip()

        # Extract the first JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model output")

        json_text = match.group(0)

        # Remove trailing backslashes that break JSON
        json_text = re.sub(r"\\\s*$", "", json_text, flags=re.MULTILINE)
        json_text = json_text.replace('\\"', '"')
        return json.loads(json_text)

    except Exception as e:
        print("=" * 50)
        print("DEBUG ERROR:", repr(e))
        print("DEBUG RAW RESPONSE:", raw if 'raw' in locals() else "No response")
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
