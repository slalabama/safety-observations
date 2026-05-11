from app.database import SessionLocal, engine, Base
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

# Update models.py
content = open('app/models.py', 'r', encoding='utf-8').read()
old = '    created_at = Column(DateTime, default=datetime.utcnow)\n    \n    observations'
new = '    role = Column(String, default="basic")\n    created_at = Column(DateTime, default=datetime.utcnow)\n    \n    observations'
updated = content.replace(old, new)
with open('app/models.py', 'w', encoding='utf-8') as f:
    f.write(updated)
print('models.py updated!')

# Verify
from app.models import Employee
db = SessionLocal()
emps = db.query(Employee).all()
for e in emps:
    print(e.name, e.badge, e.role)
db.close()
