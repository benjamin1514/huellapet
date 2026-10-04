import os
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'huellapet-desarrollo-local-cambiar-en-produccion'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['UPLOAD_MASCOTAS'] = os.path.join(app.root_path, 'static', 'uploads', 'mascotas')
app.config['UPLOAD_DOCUMENTOS'] = os.path.join(app.root_path, 'static', 'uploads', 'documentos')

os.makedirs(app.config['UPLOAD_MASCOTAS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_DOCUMENTOS'], exist_ok=True)
