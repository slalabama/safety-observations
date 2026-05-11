content = open('app/routers/admin_users.py','r',encoding='utf-8').read()
old = '    role: str = "basic"'
new = '    role: str = "basic"\n    email: str = None'
content = content.replace(old, new)
old2 = '    employee = Employee(badge=emp.badge, name=emp.name, department=emp.department, role=emp.role)'
new2 = '    employee = Employee(badge=emp.badge, name=emp.name, department=emp.department, role=emp.role, email=emp.email)'
content = content.replace(old2, new2)
open('app/routers/admin_users.py','w',encoding='utf-8').write(content)
print('API updated!')
