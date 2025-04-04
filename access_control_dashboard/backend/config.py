import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# API Ayarları
API_HOST = '0.0.0.0'
API_PORT = 5000
DEBUG = True

# MSSQL Veritabanı Ayarları
DB_SERVER = '10.34.5.7'
DB_DATABASE = 'VipasXDb2025'
DB_USERNAME = 'sa'
DB_PASSWORD = 'tpsy@z09!'
DB_ENCRYPTION_KEY = 'Z546B8DF278CD5931069B522E695D4E8'

# CORS ayarları
ALLOWED_ORIGINS = ['http://localhost:8050', 'http://127.0.0.1:8050']

# Chatbot Ayarları
GEMINI_API_KEY = os.getenv('AIzaSyBkOST2i0RCsfr0xzYuJV1sIBxA-sqUsyA', '')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1' 