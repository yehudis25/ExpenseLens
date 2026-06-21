# module to encrypt receipt data in transit
from cryptography.fernet import Fernet
import streamlit as st

# converts strings to bytes
def get_cipher():
    key = st.secrets["ENCRYPTION_KEY"].encode()
    return Fernet(key)

# takes text and returns encrypted text
def encrypt(text: str) -> str:
    if text is None:
        return None
    cipher = get_cipher()
    return cipher.encrypt(text.encode()).decode()

# decryptes the coded text
def decrypt(token: str) -> str:
    if token is None:
        return None
    cipher = get_cipher()
    return cipher.decrypt(token.encode()).decode()