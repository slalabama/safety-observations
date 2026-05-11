#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path.cwd()

FILES = {
    "requirements.txt": """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pydantic-settings==2.1.0
jinja2==3.1.2
python-multipart==0.0.6
pdfplumber==0.10.3
aiofiles==23.2.1
python-dotenv==1.0.0
geopy==2.3.0
""",
    "run.py": """import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    print('''
    Safety Observations - Local Demo Server
    Starting on http://127.0.0.1:8000
    API Docs: http://127.0.0.1:8000/docs
    ''')
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
"""
}

def create_all_files():
    for filepath, content in FILES.items():
        path = ROOT / filepath
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created {filepath}")
    
    print("Done!")

if __name__ == "__main__":
    create_all_files()
