content = open('app/routers/admin_users.py','r',encoding='utf-8').read()
old = '''            existing = db.query(Employee).filter(Employee.badge == badge).first()
            if existing:
                duplicates.append({"row": idx, "badge": badge, "name": name})
                skipped += 1
                continue
            
            employee = Employee(badge=badge, name=name, department=department)
            db.add(employee)
            imported += 1'''
new = '''            existing = db.query(Employee).filter(Employee.badge == badge).first()
            if existing:
                duplicates.append({"row": idx, "badge": badge, "name": name})
                skipped += 1
                continue
            
            employee = Employee(badge=badge, name=name, department=department)
            db.add(employee)
            try:
                db.flush()
                imported += 1
            except Exception:
                db.rollback()
                duplicates.append({"row": idx, "badge": badge, "name": name})
                skipped += 1'''
content = content.replace(old, new)
open('app/routers/admin_users.py','w',encoding='utf-8').write(content)
print('Done!')
