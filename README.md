# 🧾 ExpenseLens AI — Smart Receipt & Invoice Tracker

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Tesseract OCR](https://img.shields.io/badge/OCR-Tesseract-green)
![Ollama](https://img.shields.io/badge/AI-Ollama-blue)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Overview

ExpenseLens AI is an intelligent receipt and invoice management system designed for freelancers, small business owners, and anyone looking for an easier way to organize and track expenses.

Instead of manually entering purchase information, users simply upload a receipt or invoice. The application extracts the text using **Tesseract OCR** and then uses a locally running **Llama 3.2:1B** model through **Ollama** to convert the text into structured expense data.

The extracted data is validated using **Pydantic** before being presented to the user for review and editing.

Before saving, users can review and edit the extracted information to ensure accuracy. Receipt data is encrypted before being stored in a SQLite database, helping keep sensitive financial information secure.

Because all AI processing is performed locally, receipt data never needs to be sent to external AI services.

---

## ✨ Features

### 📷 Receipt & Invoice Upload
- Upload receipt images and invoice files
- Supports common image formats
- Stores uploaded files securely
- Detects duplicate receipt uploads using OCR text comparison
- Helps prevent storing the same receipt multiple times

### 🔎 Intelligent Receipt Processing

ExpenseLens automatically processes uploaded receipts by:

- Extracting text using **Tesseract OCR**
- Using **Llama 3.2:1B** through **Ollama** to identify:
  - Store/vendor
  - Purchase date
  - Purchased items
  - Item prices
  - Total amount

This significantly reduces manual data entry while allowing users to verify all extracted information before saving.


### ✏️ Review & Edit
- Review extracted receipt information
- Edit incorrect values
- Improve data accuracy before saving

### 💾 Expense Database
- Stores receipt information using SQLite
- Saves:
  - Receipt details
  - Extracted data
  - User information
  - Uploaded receipt files
Includes user-based data separation so each user only accesses their own expenses.

### 📊 Expense Tracking
- View saved receipts
- Search and manage expenses
- Monitor spending history
- Organize financial records

### 🔒 Data Encryption
ExpenseLens was designed with privacy in mind.

- AI processing runs locally using Ollama
- Sensitive receipt information is encrypted before storage
- Data is decrypted only when viewed by the application
- No receipt information is sent to external AI services

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend logic |
| Streamlit | Web application |
| SQLite | Database |
| Tesseract OCR (pytesseract) | Receipt text extraction |
| Ollama | Local AI inference |
| Llama 3.2:1B | Structured receipt information extraction |
| Pydantic | Data validation |
| Pillow (PIL) | Image preprocessing |
| Pandas | Data handling |
| Plotly | Expense visualization |
| Cryptography | Data encryption |

---
# 🔄 How It Works

1. User uploads a receipt or invoice.
2. The image is automatically converted to grayscale, sharpened, and enhanced for improved OCR accuracy.
3. Tesseract OCR extracts the text from the image.
4. Llama 3.2:1B (running locally through Ollama) converts the OCR text into structured expense information.
5. The user reviews and edits the extracted data if needed.
6. Receipt information is encrypted and stored in a SQLite database.
7. Users can search, view, and manage their saved expenses.

---

# 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yehudis25/ExpenseLens.git
cd ExpenseLens
```

### 2. Create and Activate a Virtual Environment

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
### 4. Install Tesseract OCR

ExpenseLens uses **Tesseract OCR** to extract text from receipts.

- **Streamlit Community Cloud:** Tesseract is installed automatically using `packages.txt`/`pkgs.txt`.
- **Local installation:** Install Tesseract OCR on your system and ensure it is available in your system PATH before running the application.

#### Windows

1. Download and install Tesseract OCR:

https://github.com/UB-Mannheim/tesseract/wiki


2. Add the Tesseract installation folder to your system PATH. The default installation location is usually:

```text
C:\Program Files\Tesseract-OCR
```

3. Restart your terminal and verify the installation:

```bash
tesseract --version
```

#### macOS

1. Install Tesseract using Homebrew:

```bash

brew install tesseract
```


2. Verify the installation:

```bash

tesseract --version
```


#### Linux

1. Install Tesseract using:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

2. Verify the installation:

```bash

tesseract --version
```

### 5. Install Ollama

ExpenseLens uses Ollama to run the **Llama 3.2:1B** model locally.

**Windows/macOS**

Download and install Ollama from:

https://ollama.com/download

**Linux (including GitHub Codespaces)**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 6. Pull the Required Model

```bash
ollama pull llama3.2:1b
```

### 7. Start the Ollama Server

In a separate terminal, run:

```bash
ollama serve
```

Leave this terminal open while using ExpenseLens.

### 8. Run the Streamlit App

In another terminal (with your virtual environment activated):

```bash
streamlit run app.py
```

The application will open in your browser, typically at:

```
http://localhost:8501
```
---

# 📝 Notes

- The Ollama server must be running before processing receipts.
- The AI model only needs to be downloaded once using `ollama pull`.
- The first model download may take several minutes depending on your internet connection.
- If you receive an Ollama connection error, verify that `ollama serve` is still running.
- Tesseract OCR must be installed before receipt processing will work.

---

# 📄 License

This project is licensed under the MIT License.

