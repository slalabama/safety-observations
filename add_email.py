content = open('app/models.py','r',encoding='utf-8').read()
old = '    role = Column(String, default="basic")'
new = '    role = Column(String, default="basic")\n    email = Column(String, nullable=True)'
content = content.replace(old, new)
open('app/models.py','w',encoding='utf-8').write(content)
print('Model updated!')
