"""
Comprehensive PIN-based login fix.
Run from C:\\projects\\safety-observations:
    python fix_login_final.py
Then:
    git add -A
    git commit -m "Comprehensive PIN login fix"
    git push
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
# If running from project root directly, ROOT is the project. Otherwise default to cwd.
if not os.path.exists(os.path.join(ROOT, "app")):
    ROOT = os.getcwd()

def read(path):
    full = os.path.join(ROOT, path)
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

def write(path, content):
    full = os.path.join(ROOT, path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote {path}")

# ----------------------------------------------------------------------
# 1. Ensure models.py Employee has pin column
# ----------------------------------------------------------------------
print("\n[1/5] Ensuring Employee model has pin column...")
models = read("app/models.py")

if "pin: Mapped" not in models and "pin = Column" not in models and "pin: " not in models:
    # Insert pin after status field in Employee class
    pattern = r'(class Employee[^:]*:.*?status:\s*Mapped\[[^\]]+\]\s*=\s*mapped_column\([^\)]*\))'
    match = re.search(pattern, models, re.DOTALL)
    if match:
        old = match.group(1)
        new = old + '\n    pin: Mapped[str | None] = mapped_column(String, nullable=True)'
        models = models.replace(old, new)
        write("app/models.py", models)
        print("  added pin column to Employee model")
    else:
        print("  WARNING: could not find Employee.status field to anchor pin column")
else:
    print("  Employee model already has pin")

# ----------------------------------------------------------------------
# 2. Add startup migration in main.py to ALTER TABLE on every deploy
# ----------------------------------------------------------------------
print("\n[2/5] Adding startup migration to main.py...")
main_py = read("app/main.py")

migration_block = '''
# --- Auto-migration: ensure pin column exists on employees ----------------
@app.on_event("startup")
def _ensure_pin_column():
    from sqlalchemy import text
    from app.database import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS pin VARCHAR"))
            conn.commit()
            print("[startup] pin column ensured")
    except Exception as e:
        print(f"[startup] pin column migration failed: {e}")
# --------------------------------------------------------------------------
'''

if "_ensure_pin_column" not in main_py:
    # Find the `app = FastAPI(...)` line and insert migration after it
    # We'll just append to the bottom of the file, which is safe.
    main_py = main_py.rstrip() + "\n" + migration_block + "\n"
    write("app/main.py", main_py)
    print("  added startup migration to main.py")
else:
    print("  startup migration already in main.py")

# ----------------------------------------------------------------------
# 3. Clean up setup.py: ensure ALTER TABLE runs first, set PINs
# ----------------------------------------------------------------------
print("\n[3/5] Cleaning up setup.py...")
setup = read("app/routers/setup.py")

# Remove any prior partial ALTER TABLE attempts to avoid duplicates
setup = re.sub(
    r'\n\s*# Ensure pin column exists.*?db\.commit\(\)\n',
    '\n',
    setup,
    flags=re.DOTALL,
)

# Make sure setup explicitly sets PINs on Charles and Stephanie
# Replace the Charles creation block
def fix_admin_seed(text_in, name, badge, email, default_pin):
    # Add pin to Employee(...) constructor if missing
    pattern = r'Employee\(badge="' + badge + r'"[^\)]*\)'
    m = re.search(pattern, text_in)
    if m:
        old = m.group(0)
        if "pin=" not in old:
            new = old[:-1] + f', pin="{default_pin}")'
            text_in = text_in.replace(old, new)
    # Also ensure existing record gets PIN set
    # Add a line: target.pin = target.pin or "xxxx" after status update
    return text_in

setup = fix_admin_seed(setup, "Charles Burks", "00854", "charles@slalabama.com", "1234")
setup = fix_admin_seed(setup, "Stephanie Jennings", "48457", "stephanie@slalabama.com", "5678")

# Ensure existing employees get their default PIN if missing
# Look for `charles.status = "active"` and append pin line if not already there
if 'charles.pin = charles.pin or "1234"' not in setup:
    setup = setup.replace(
        'charles.status = "active"',
        'charles.status = "active"\n            charles.pin = charles.pin or "1234"',
        1,
    )

if 'stephanie.pin = stephanie.pin or "5678"' not in setup:
    setup = setup.replace(
        'stephanie.status = "active"',
        'stephanie.status = "active"\n            stephanie.pin = stephanie.pin or "5678"',
        1,
    )

write("app/routers/setup.py", setup)
print("  setup.py updated with PIN seeds")

# ----------------------------------------------------------------------
# 4. Ensure admin_auth.py uses PIN validation, not GPS
# ----------------------------------------------------------------------
print("\n[4/5] Fixing admin_auth.py login function...")
auth = read("app/routers/admin_auth.py")

# Ensure LoginRequest has pin
auth = re.sub(
    r'class LoginRequest\(BaseModel\):\s*\n(\s*first_name:\s*str\s*\n\s*last_name:\s*str\s*\n)(\s*latitude:[^\n]*\n\s*longitude:[^\n]*\n)?',
    r'class LoginRequest(BaseModel):\n\1    pin: str\n',
    auth,
)

# Replace the GPS facility/distance block with PIN check
gps_pattern = re.compile(
    r'\n\s*facility\s*=\s*db\.query\(Facility\)\.first\(\).*?if distance_miles > facility\.radius_miles:.*?\)\s*\n\s*\)\s*\n',
    re.DOTALL,
)
pin_replacement = '''

    # Validate PIN
    if not employee.pin:
        raise HTTPException(status_code=403, detail="PIN not set. Contact an admin.")
    if employee.pin != request.pin:
        raise HTTPException(status_code=401, detail="Invalid PIN")
'''

if gps_pattern.search(auth):
    auth = gps_pattern.sub(pin_replacement, auth)
    print("  replaced GPS block with PIN validation")
elif "Validate PIN" in auth:
    print("  PIN validation already present")
else:
    print("  WARNING: could not find GPS block; manual review needed")

write("app/routers/admin_auth.py", auth)

# ----------------------------------------------------------------------
# 5. Ensure login.html has PIN input and posts pin field
# ----------------------------------------------------------------------
print("\n[5/5] Verifying login.html has PIN field...")
login_html = read("app/templates/login.html")

if 'id="pin"' not in login_html:
    print("  WARNING: login.html missing pin input. Adding...")
    # Insert PIN field after last name input
    login_html = re.sub(
        r'(<input[^>]*id="lastName"[^>]*>)',
        r'''\1
          <label for="pin" style="margin-top:12px;display:block;">PIN</label>
          <input type="password" id="pin" placeholder="4-digit PIN" maxlength="4" inputmode="numeric">''',
        login_html,
        count=1,
    )

# Ensure doLogin sends pin not lat/lon
if "latitude: userLat" in login_html:
    login_html = login_html.replace(
        "body: JSON.stringify({first_name: firstName, last_name: lastName, latitude: userLat, longitude: userLon})",
        'body: JSON.stringify({first_name: firstName, last_name: lastName, pin: document.getElementById("pin").value})',
    )

write("app/templates/login.html", login_html)

print("\n" + "=" * 60)
print("DONE. Now run:")
print("  git add -A")
print('  git commit -m "Comprehensive PIN login fix"')
print("  git push")
print("\nThen wait 2 min for Railway, hit /setup ONCE,")
print("then login: Charles / Burks / 1234")
print("=" * 60)
