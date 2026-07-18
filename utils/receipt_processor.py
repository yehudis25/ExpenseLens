import ollama
import re
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pathlib import Path
import streamlit as st
import pytesseract
from pydantic import BaseModel, Field, ValidationError
from typing import List

def receipt_check(text: str) -> bool:
    if not text:
        return False

    text_lower = text.lower()

    receipt_keywords = [
        "total", "subtotal", "tax", "amount", "change", "cash", "debit",
        "credit", "visa", "mastercard", "receipt", "thank you", "store",
        "item", "qty", "quantity", "price"
    ]

    invoice_keywords = ["invoice", "bill to", "ship to", "due date", "invoice number","balance due", "amount due"]

    # If any receipt or invoice keyword appears then it is a valid receipt/invoice
    return any(k in text_lower for k in receipt_keywords + invoice_keywords)

# Prevent duplicate reciept from being uploaded
def prevent_duplicate_receipt_by_text(raw_text):
    if "receipt_texts" not in st.session_state:
        st.session_state.receipt_texts = set()

    normalized = re.sub(r"\s+", " ", raw_text.lower()).strip()

    if normalized in st.session_state.receipt_texts:
        st.warning("⚠️ This receipt has already been uploaded.")
        st.stop()
    else:
        st.session_state.receipt_texts.add(normalized)

def clean_item_name(name: str) -> str:
    words = name.split()

    if not words or len(words) == 1:
        return ""

    first_word = words[0]

    if any(character.isdigit() for character in first_word):
        words = words[1:]

    return " ".join(words).strip()

def clean_receipt_ocr(raw_text: str) -> str:
    text = raw_text

    # Remove OCR table borders
    text = text.replace("|", " ") 

    # Replace decimal comma: 5,80 -> 5.80
    text = re.sub(r"(?<=\d),(?=\d{2}\b)", ".", text)
    
    # Fix formatting of 'X' or 'x' between quantity and price
    text = re.sub(r"(?<=\d)\s*[xX]\s*(?=\d)", " X ", text)
    
    # Correct decimal seperated by spaces so 2. 80 -> 2.80
    text = re.sub(r"(?<=\d)\.\s+(?=\d{2}\b)", ".", text)

    # Fix OCR incorrect extraction of '5', e.g: §.80 -> 5.80
    text = text.replace("Ã‚Â§", "5")

    # Fix OCR error of incorrect extraction of 'S'
    text = re.sub(r"\$(?=[A-Za-z]+)", "S", text)

    print("CORRECTED TEXT")
    print(text, flush=True)

    return text

def extract_raw_text(image_input) -> str:
    try:
        # Check if input is image_input is of type string  (for sample images) or Path 
        if isinstance(image_input, (str, Path)): 
            image = Image.open(image_input)
        # Check if input is uploaded file or camera photo
        elif hasattr(image_input, "read"): 
            image_input.seek(0) # read from beginning of file
            image = Image.open(image_input)
        # Check if input is image that was already opened
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            raise TypeError(f"Unsupported image input: {type(image_input).__name__}")
        # Make sure rotation is correct and specify pixel types for Tesseract
        image = ImageOps.exif_transpose(image).convert("RGB")

        # Reduce image size if large and use LANZOS for defining reduced pixels
        image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)

        # Improve receipt contrast for better extraction
        image = ImageOps.grayscale(image)
        image = ImageEnhance.Contrast(image).enhance(1.8)
        image = image.filter(ImageFilter.SHARPEN)

        # Perform OCR
        text = pytesseract.image_to_string(image, lang="eng",config="--oem 3 --psm 6",
            timeout=30) 

        return text.strip()

    except RuntimeError as exc:
        raise RuntimeError(
            f"Tesseract OCR timed out: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Tesseract OCR failed: {exc}") from exc
        
# Pydantic models for receipt
class Item(BaseModel):
    name: str = Field(default="")
    quantity: float = Field(default=1.0)
    price: float = Field(default=0.0)

class Receipt(BaseModel):
    store: str = Field(default="")
    date: str = Field(default="")
    total: float = Field(default=0.0)
    items: List[Item] = Field(default_factory=list)


def structure_text_with_llm(raw_text: str) -> dict:
    # Use API to connect to ollama server
    client = ollama.Client(host="http://127.0.0.1:11434", timeout=120,)

    # Reduce amount of text sent to model to speed up processing
    raw_text = clean_receipt_ocr(raw_text)
    raw_text = raw_text[:8000]

    prompt = f"""
    Extract structured purchase data from the OCR text.

    DOCUMENT FIELDS

    store:
    - The merchant or company issuing the receipt.
    - Usually appears in the first few lines.
    - Do not use the customer, cashier, server, address, or tax heading.

    date:
    - The transaction, receipt, or invoice date.
    - Return YYYY-MM-DD when the day and month can be determined.
    - Do not use an order number, invoice number, or tax number.

    total:
    - Return the final amount paid or payable.
    - Inspect the receipt from bottom to top.
    - Prefer an anchored standalone "TOTAL:" line over subtotal,
    excluding-tax total and inclusive-tax total.
    - If a payment line such as VISA appears use its amount if no standalone 'TOTAL' 

   ITEM EXTRACTION

    Extract every purchased item between the item-table heading and the
    first summary line.

    For each item return:
    - name: product description without the item code
    - quantity: the number before "x"
    - price: the UNIT PRICE, not the line total

    Interpret item rows using this pattern:

    quantity x unit_price line_total

    Examples:
    - "3 x 1.00 3.00" means quantity=3 and price=1.00
    - "1 x 5.80 5.80" means quantity=1 and price=5.80
    - "2 x 12.80 25.60" means quantity=2 and price=12.80
    - "5 x 1.80 9.00" means quantity=5 and price=1.80
    - "2 x 2.80 5.60" means quantity=2 and price=2.80

    Rules:
    - Return one item for every description row.
    - Continue until the first subtotal, total, tax, service charge,
    rounding, cash, card, VISA, or balance line.
    - Do not stop after the first few items.
    - "$B01" and "$B02" are OCR errors for item codes "SB01" and "SB02".
    - A line beginning with "$B" followed by digits is an item row,
    not a price or summary line.
    - Do not include item codes in the product name.
    - Do not create items from summary or payment lines.

    Before returning:
    - Calculate quantity * price for each item.
    - Sum those calculated line totals.
    - If "Total Excluding GST" exists, the calculated item sum should
    equal it.
    - If the calculated sum is lower, inspect the table again for omitted
    item rows.

    RECONCILIATION

    - For each item, calculate quantity * price.
    - The calculated value should match the line total shown in the OCR.
    - The sum of all calculated item subtotals should approximately equal
    "Total Excluding GST" when that value is present.
    - If the calculated sum is lower, inspect the item table again for
    omitted rows or incorrect quantities.

    Return every required JSON-schema field.
    Return only the structured result.

    OCR TEXT:
    ---BEGIN OCR---
    {raw_text}
    ---END OCR---
    """

    try:
        print("Starting structured extraction...", flush=True)
        # Send request to llama to return json 
        response = client.generate(
            model="llama3.2:1b",
            prompt=prompt,
            format=Receipt.model_json_schema(),
            options={
                "temperature": 0,
                "num_predict": 768,
                "num_ctx": 4096,
            },
            keep_alive="5m",
        )

        raw_response = response["response"]
        print("RAW STRUCTURED RESPONSE:", flush=True)
        print(raw_response, flush=True)
        # print("OCR characters sent:", len(raw_text), flush=True)
        # print("OCR preview:", raw_text[:800], flush=True)
        # Validate response with pydantic models
        validated = Receipt.model_validate_json(raw_response)

        return validated.model_dump() # converts object to dictionary

    except Exception as exc:
        print(f"Structured extraction failed: {exc}", flush=True)
        return {
            "store": "Parsing Failure",
            "date": "Uknown",
            "total": 0.0,
            "items": [],
        }

def process_receipt(raw_text: str):
    prevent_duplicate_receipt_by_text(raw_text)
    result = structure_text_with_llm(raw_text)
    # Remove item codes before name
    for item in result["items"]:
        item["name"] = clean_item_name(item["name"])

    return result
