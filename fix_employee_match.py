"""
Backend upgrade for flexible employee matching + working CSV import.

Run from C:\\projects\\safety-observations:
    python fix_employee_match.py
"""
import os
import re

ROOT = os.getcwd()

# ---------------------------------------------------------------
# 1. Replace the observe-login endpoint with smart matching
# ---------------------------------------------------------------
auth_path = os.path.join(ROOT, "app/routers/admin_auth.py")
with open(auth_path, "r", encoding="utf-8") as f:
    auth = f.read()

# Replace whatever observe-login is currently there with a smart version
smart_endpoint = '''

class ObserveLoginRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    badge: str = ""

def _match_employee(db, first: str, last: str, badge: str):
    """Smart matching: badge exact, else flexible name search."""
    badge = (badge or "").strip()
    first = (first or "").strip()
    last  = (last  or "").strip()

    if badge:
        return db.query(Employee).filter(Employee.badge == badge).first()

    if not (first and last):
        return None

    # Pull all active employees and match in Python so we can be flexible.
    employees = db.query(Employee).filter(Employee.status == "active").all()
    f_low = first.lower()
    l_low = last.lower()

    # PASS 1: exact first + exact last (case-insensitive)
    for e in employees:
        ef = (getattr(e, "first_name", None) or "").strip().lower()
        el = (getattr(e, "last_name",  None) or "").strip().lower()
        if ef == f_low and el == l_low:
            return e

    # PASS 2: first matches, and last is any whitespace-separated word of stored last
    for e in employees:
        ef = (getattr(e, "first_name", None) or "").strip().lower()
        el = (getattr(e, "last_name",  None) or "").strip().lower()
        if ef == f_low and l_low in el.split():
            return e

    # PASS 3: parse name column "Last, First Middle" and try
    for e in employees:
        full = (e.name or "").strip()
        if "," in full:
            stored_last, rest = full.split(",", 1)
            stored_last = stored_last.strip().lower()
            stored_first = rest.strip().split()[0].lower() if rest.strip() else ""
            if stored_first == f_low and (l_low == stored_last or l_low in stored_last.split()):
                return e
        # Also try "First Last" format
        parts = full.lower().split()
        if len(parts) >= 2 and parts[0] == f_low and l_low in parts[1:]:
            return e

    # PASS 4: substring fallback - first name matches start, last name matches any token
    for e in employees:
        ef = (getattr(e, "first_name", None) or "").strip().lower()
        el = (getattr(e, "last_name",  None) or "").strip().lower()
        name_l = (e.name or "").lower()
        if f_low in name_l and l_low in name_l:
            return e

    return None

@router.post("/observe-login")
def observe_login(req: ObserveLoginRequest, db: Session = Depends(get_db)):
    """Employee login for observations. No PIN, no GPS. Flexible name match or badge."""
    employee = _match_employee(db, req.first_name, req.last_name, req.badge)

    if not employee:
        if (req.badge or "").strip():
            raise HTTPException(status_code=404, detail="Employee ID not found.")
        if not (req.first_name and req.last_name):
            raise HTTPException(status_code=400, detail="Enter first and last name, or your Employee ID.")
        raise HTTPException(status_code=404, detail="No employee matched that name.")

    if employee.status != "active":
        raise HTTPException(status_code=403, detail="Employee account is inactive")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    db.add(SessionRecord(id=token, employee_id=employee.id, expires_at=expires_at))
    employee.last_login = datetime.utcnow()
    db.commit()

    response = Response(
        content='{"success": true, "employee_name": "' + employee.name + '", "badge": "' + (employee.badge or "") + '"}',
        media_type="application/json"
    )
    response.set_cookie("session_token", token, httponly=True, secure=True, samesite="lax", max_age=3600, path="/")
    return response
'''

# Drop any existing observe-login block first
auth = re.sub(
    r'\n*class ObserveLoginRequest\(BaseModel\):.*?(?=\n@router\.\w+\("(?!/observe-login)|\Z)',
    '\n',
    auth, flags=re.DOTALL,
)
auth = auth.rstrip() + "\n" + smart_endpoint + "\n"

with open(auth_path, "w", encoding="utf-8") as f:
    f.write(auth)
print("Updated observe-login with smart matching")

# ---------------------------------------------------------------
# 2. Add first_name/last_name columns to Employee model (optional fields)
# ---------------------------------------------------------------
models_path = os.path.join(ROOT, "app/models.py")
with open(models_path, "r", encoding="utf-8") as f:
    models = f.read()

if "first_name = Column" not in models:
    models = models.replace(
        '    pin = Column(String, nullable=True)',
        '    pin = Column(String, nullable=True)\n    first_name = Column(String, nullable=True)\n    last_name = Column(String, nullable=True)',
    )
    with open(models_path, "w", encoding="utf-8") as f:
        f.write(models)
    print("Added first_name/last_name columns to Employee model")
else:
    print("first_name/last_name already in Employee model")

# ---------------------------------------------------------------
# 3. Auto-migrate first_name/last_name columns on startup
# ---------------------------------------------------------------
main_path = os.path.join(ROOT, "app/main.py")
with open(main_path, "r", encoding="utf-8") as f:
    main = f.read()

if "ADD COLUMN IF NOT EXISTS first_name" not in main:
    main = main.replace(
        'ALTER TABLE employees ADD COLUMN IF NOT EXISTS pin VARCHAR',
        'ALTER TABLE employees ADD COLUMN IF NOT EXISTS pin VARCHAR"))\n            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS first_name VARCHAR"))\n            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS last_name VARCHAR',
    )
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(main)
    print("Added auto-migration for first_name/last_name")

# ---------------------------------------------------------------
# 4. Fix admin_users.py CSV import to handle badge, position, first/last
# ---------------------------------------------------------------
users_path = os.path.join(ROOT, "app/routers/admin_users.py")
with open(users_path, "r", encoding="utf-8") as f:
    users = f.read()

# Replace the entire import_csv function with one that handles our new schema
new_import = '''@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Employee = Depends(get_current_employee)
):
    """
    Import employees from CSV.
    Accepted headers (case-insensitive): badge, name, first_name, last_name, department, role, email
    Matches by badge (unique); skips dupes.
    """
    contents = await file.read()
    text = contents.decode("utf-8-sig")
    sample = text[:500]
    delim = "\\t" if "\\t" in sample else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    # Normalize header names
    reader.fieldnames = [(h or "").strip().lower().replace(" ", "_") for h in (reader.fieldnames or [])]

    imported = 0
    skipped = 0
    duplicates = []
    total = 0
    for idx, row in enumerate(reader, 1):
        total += 1
        try:
            badge = (row.get("badge") or row.get("emp_id") or row.get("employee_id") or "").strip()
            name  = (row.get("name") or "").strip()
            first = (row.get("first_name") or row.get("first") or "").strip()
            last  = (row.get("last_name")  or row.get("last")  or "").strip()
            dept  = (row.get("department") or row.get("position") or "").strip() or None
            role  = (row.get("role") or "basic").strip().lower() or "basic"
            email = (row.get("email") or "").strip() or None

            if not name and first and last:
                name = f"{first} {last}".strip()
            if not name:
                skipped += 1
                duplicates.append({"row": idx, "error": "no name"})
                continue
            if not badge:
                skipped += 1
                duplicates.append({"row": idx, "name": name, "error": "no badge/emp id"})
                continue

            existing = db.query(Employee).filter(Employee.badge == badge).first()
            if existing:
                # Update first/last/position if we now have them
                if first and not existing.first_name: existing.first_name = first
                if last  and not existing.last_name:  existing.last_name  = last
                if dept and not existing.department:  existing.department = dept
                duplicates.append({"row": idx, "name": name, "badge": badge})
                skipped += 1
                continue

            db.add(Employee(
                badge=badge,
                name=name,
                first_name=first or None,
                last_name=last or None,
                department=dept,
                role=role,
                email=email,
                status="active",
            ))
            try:
                db.flush()
                imported += 1
            except Exception as e:
                db.rollback()
                skipped += 1
                duplicates.append({"row": idx, "name": name, "error": str(e)})
        except Exception as e:
            skipped += 1
            duplicates.append({"row": idx, "error": str(e)})

    db.commit()
    return CSVImportResponse(total=total, imported=imported, skipped=skipped, duplicates=duplicates)
'''

users = re.sub(
    r'@router\.post\("/import-csv"\).*?(?=\n@router\.)',
    new_import + "\n",
    users, flags=re.DOTALL,
)

with open(users_path, "w", encoding="utf-8") as f:
    f.write(users)
print("Rewrote /api/users/import-csv to handle badge + first/last/position")

print("\nDone. Run:")
print('  git add -A')
print('  git commit -m "Flexible name matching + working CSV import"')
print('  git push')
