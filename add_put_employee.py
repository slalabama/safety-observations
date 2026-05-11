content = open('app/routers/admin_users.py','r',encoding='utf-8').read()
new_endpoint = '''
@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    emp: EmployeeCreate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee.badge = emp.badge
    employee.name = emp.name
    employee.department = emp.department
    employee.role = emp.role
    employee.email = emp.email
    db.commit()
    db.refresh(employee)
    return EmployeeResponse(id=employee.id, badge=employee.badge, name=employee.name, department=employee.department)
'''
content = content + new_endpoint
open('app/routers/admin_users.py','w',encoding='utf-8').write(content)
print('API updated!')
