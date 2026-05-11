import uvicorn
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
