content = open('app/routers/admin_users.py', 'r', encoding='utf-8').read()
old = 'class EmployeeCreate(BaseModel):\n    badge: str\n    name: str\n    department: str = None'
new = 'class EmployeeCreate(BaseModel):\n    badge: str\n    name: str\n    department: str = None\n    role: str = "basic"'
updated = content.replace(old, new)
old2 = '    employee = Employee(badge=emp.badge, name=emp.name, department=emp.department)'
new2 = '    employee = Employee(badge=emp.badge, name=emp.name, department=emp.department, role=emp.role)'
updated = updated.replace(old2, new2)
with open('app/routers/admin_users.py', 'w', encoding='utf-8') as f:
    f.write(updated)
print('API updated!')
