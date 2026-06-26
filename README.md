# 🧾 Expense Lens AI — Smart Receipt & Invoice Tracker

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![OCR](https://img.shields.io/badge/AI-OCR%20Powered-green)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

Expense Lens AI is an intelligent receipt and invoice management system designed especially for freelancers who need a simple way to track expenses.

Using OCR and AI-powered extraction, Expense Lens converts receipt images into organized digital expense records — eliminating the need for manual data entry.

Users can upload a receipt, automatically extract important information, review and edit the results, and securely store their expenses.

Built with privacy in mind: all AI processing runs locally using Ollama, keeping sensitive financial documents on the user's machine instead of sending data to external services.

---

## ✨ Features

### 📷 Receipt & Invoice Upload
- Upload receipt images and invoice files
- Supports common image formats
- Stores uploaded files securely

### 🔎 AI OCR Extraction
- Automatically extracts important receipt information:
  - Store/vendor name
  - Purchase date
  - Items
  - Prices
  - Total amount
Uses OCR + local AI processing to reduce manual data entry.

### ✏️ Review & Edit
- Users can review OCR results before saving
- Allows corrections to extracted information
- Improves accuracy of stored expense records

### 💾 Expense Database
- Stores receipt information using SQLite
- Saves:
  - Receipt details
  - Extracted OCR data
  - User information
  - Uploaded receipt files
Includes user-based data separation so each user only accesses their own expenses.

### 📊 Expense Tracking
- View saved receipts
- Search and manage expenses
- Track spending history

### 🔒 Data Encryption
- Sensitive receipt fields are encrypted before being stored
- Data is decrypted only when accessed by the application
- Helps protect stored financial information

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend logic |
| Streamlit | Web application interface |
| SQLite | Database storage |
| OCR | Receipt text extraction |
| Ollama | Local AI processing |
| Pandas | Data handling |
| PIL | Image processing |
| Cryptography | Data encryption |

---

1. User uploads a receipt image
2. OCR extracts text from the image
3. Local AI processes the extracted text
4. Structured expense data is created
5. User reviews and edits information
6. Data is encrypted and saved into SQLite

---



