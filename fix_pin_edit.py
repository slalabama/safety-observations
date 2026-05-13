"""
Fix PIN admin management in Edit Employee modal.

Run from C:\\projects\\safety-observations:
    python fix_pin_edit.py
"""
import os
import re

ROOT = os.getcwd()

# -----------------------------------------------------------------------
# FRONTEND: admin_users_page.html
# -----------------------------------------------------------------------
path = os.path.join(ROOT, "app/templates/admin_users_page.html")
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Pass e.pin in the onclick handler
old_onclick = "openEdit(${e.id}, '', '${e.name}', '${e.department||''}', '${e.email||''}', '${e.role}')"
new_onclick = "openEdit(${e.id}, '', '${e.name}', '${e.department||''}', '${e.email||''}', '${e.role}', '${e.pin||''}')"
html = html.replace(old_onclick, new_onclick)

# 2. Add `pin` to openEdit() function signature
html = html.replace(
    "function openEdit(id, badge, name, dept, email, role) {",
    "function openEdit(id, badge, name, dept, email, role, pin) {",
)

# 3. Ensure the editEmail line is followed by editPin (some versions had bad concat)
# Strip any stray duplicate editPin assignments and rebuild cleanly
html = re.sub(
    r"document\.getElementById\('editEmail'\)\.value = email;\s*\n\s*document\.getElementById\('editPin'\)\.value = pin \|\| '';\s*\n\s*document\.getElementById\('editRole'\)",
    "document.getElementById('editEmail').value = email;\n            document.getElementById('editPin').value = pin || '';\n            document.getElementById('editRole')",
    html,
)
# Also handle the version without editPin yet
if "document.getElementById('editPin').value" not in html:
    html = html.replace(
        "document.getElementById('editEmail').value = email;",
        "document.getElementById('editEmail').value = email;\n            document.getElementById('editPin').value = pin || '';",
    )

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Fixed admin_users_page.html")

# -----------------------------------------------------------------------
# BACKEND: admin_users.py - ensure PUT endpoint accepts pin
# -----------------------------------------------------------------------
backend_path = os.path.join(ROOT, "app/routers/admin_users.py")
if os.path.exists(backend_path):
    with open(backend_path, "r", encoding="utf-8") as f:
        py = f.read()

    # Find any UserUpdate / EmployeeUpdate pydantic schema and add pin if missing
    # Look for the BaseModel class that has name/department/email/role fields
    pattern = re.compile(
        r"(class\s+\w+\(BaseModel\):.*?)(?=\nclass\s+|\n@router|\Z)",
        re.DOTALL,
    )
    changed = False
    for match in pattern.finditer(py):
        block = match.group(1)
        # If this is the update schema (has role/email) and lacks pin, add pin
        if (
            ("role" in block or "email" in block)
            and "pin" not in block
            and "department" in block
        ):
            new_block = block.rstrip() + "\n    pin: Optional[str] = None\n"
            py = py.replace(block, new_block)
            changed = True
            print(f"Added pin field to {match.group(1).splitlines()[0].strip()}")

    # Ensure typing.Optional is imported
    if "Optional" in py and "from typing import" not in py:
        py = "from typing import Optional\n" + py
        changed = True
        print("Added `from typing import Optional`")
    elif "from typing import" in py and "Optional" not in py.split("\n")[0:5][0]:
        # Try to add Optional to existing typing import
        py = re.sub(
            r"from typing import ([^\n]+)",
            lambda m: f"from typing import {m.group(1)}, Optional"
            if "Optional" not in m.group(1)
            else m.group(0),
            py,
            count=1,
        )

    # Ensure the PUT endpoint actually writes pin to the employee
    # Look for a line like `employee.email = update.email` and add pin line after it
    if "employee.pin" not in py:
        py = re.sub(
            r"(\w+\.email\s*=\s*\w+\.email[^\n]*\n)",
            r"\1        employee.pin = update.pin if update.pin is not None else employee.pin\n",
            py,
            count=1,
        )
        changed = True
        print("Added employee.pin assignment in PUT endpoint")

    if changed:
        with open(backend_path, "w", encoding="utf-8") as f:
            f.write(py)
        print("Updated admin_users.py")
    else:
        print("admin_users.py: no changes needed (pin already supported)")
else:
    print(f"WARNING: {backend_path} not found - backend may need manual update")

print("\nDone. Run:")
print('  git add -A')
print('  git commit -m "Wire PIN field through Edit Employee modal"')
print('  git push')
