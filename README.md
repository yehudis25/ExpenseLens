# 🧾 ExpenseLens AI — Smart Receipt Tracker

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Tesseract OCR](https://img.shields.io/badge/OCR-Tesseract-green)
![Ollama](https://img.shields.io/badge/AI-Ollama-blue)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Overview

ExpenseLens AI is an intelligent receipt management system designed for freelancers, small business owners, and anyone looking for an easier way to organize and track expenses.

Instead of manually entering purchase information, users simply upload a receipt. The application extracts the text using **Tesseract OCR** and then uses a locally running **Llama 3.2:1B** model through **Ollama** to convert the text into structured expense data.

The extracted data is validated using **Pydantic** before being presented to the user for review and editing.

Before saving, users can review and edit the extracted information to ensure accuracy. Receipt data is encrypted before being stored in a SQLite database, helping keep sensitive financial information secure.

Because all AI processing is performed locally, receipt data never needs to be sent to external AI services.

---

## ✨ Features

### 📷 Receipt Upload
- Upload receipt image files
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

1. User uploads a receipt.
2. The image is automatically converted to grayscale, sharpened, and enhanced for improved OCR accuracy.
3. Tesseract OCR extracts the text from the image.
4. Llama 3.2:1B (running locally through Ollama) converts the OCR text into structured expense information.
5. The user reviews and edits the extracted data if needed.
6. Receipt information is encrypted and stored in a SQLite database.
7. Users can search, view, and manage their saved expenses.

---

## 🔐 Test Login (Demo Account)

To try ExpenseLens without creating an account, use the demo login:

**Username:** tester  
**Password:** testing123

This account is preloaded with sample receipts so you can explore the app’s features immediately.

# 🚀 Getting Started

### 1. Configure Encryption Key

ExpenseLens uses **Fernet encryption** to securely store uploaded receipt images.

Create a `.streamlit/secrets.toml` file in your project:

```toml
ENCRYPTION_KEY = "your_generated_fernet_key_here"
```

Generate your own encryption key using Python:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the generated key into `secrets.toml`.

⚠️ **Important:** Never upload `.streamlit/secrets.toml` or share your encryption key publicly. Each deployment should use its own unique key.


### 2. Clone the Repository

```bash
git clone https://github.com/yehudis25/ExpenseLens.git
cd ExpenseLens
```

### 3. Create and Activate a Virtual Environment

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

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```
### 5. Install Tesseract OCR

ExpenseLens uses **Tesseract OCR** to extract text from receipts.

Important:
- `pytesseract` (listed in `requirements.txt`) is only a Python wrapper.
- The actual **Tesseract OCR engine** must also be installed on the system.

---

### Streamlit Community Cloud

If deploying to Streamlit Community Cloud, Tesseract is installed automatically using the `packages.txt` file included in this repository.

No manual installation is required.

---

### Local Installation

If running ExpenseLens on your own computer, install Tesseract OCR before starting the application.

#### Windows

1. Download the Windows installer:

https://github.com/UB-Mannheim/tesseract/wiki

2. Install Tesseract using the default settings.

The default installation folder is:

```text
C:\Program Files\Tesseract-OCR
```
3. Add Tesseract to your Windows PATH:
- Open Start Menu
- Search for: Environment Variables
- Select Edit the system environment variables'
- Under User variables, select Path
- click edit and then new
- Add: C:\Program Files\Tesseract-OCR

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

#### If Tesseract is installed but ExpenseLens cannot find it, manually specify the executable path in utils/receipt_processor.py:

```bash
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
```

### 6. Install Ollama

ExpenseLens uses Ollama to run the **Llama 3.2:1B** model locally.

**Windows/macOS**

Download and install Ollama from:

https://ollama.com/download

**Linux (including GitHub Codespaces)**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 7. Pull the Required Model

```bash
ollama pull llama3.2:1b
```

### 8. Start the Ollama Server

In a separate terminal, run:

```bash
ollama serve
```

Leave this terminal open while using ExpenseLens.

### 9. Run the Streamlit App

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

