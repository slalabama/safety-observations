"""
Fix login.html: make doLogin() actually send the pin field.
Run from C:\\projects\\safety-observations:
    python fix_login_html.py
"""
import os

ROOT = os.getcwd()
path = os.path.join(ROOT, "app/templates/login.html")

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove the unused GPS variables
content = content.replace(
    "        let userLat = null;\r\n        let userLon = null;\r\n\r\n        // Get GPS location on load\r\n        \r\n",
    "",
)
content = content.replace(
    "        let userLat = null;\n        let userLon = null;\n\n        // Get GPS location on load\n        \n",
    "",
)

# 2. Replace the body of the fetch to send pin instead of lat/lon
old_body = """                    body: JSON.stringify({
                        first_name: firstName,
                        last_name: lastName,
                        latitude: userLat,
                        longitude: userLon
                    })"""
new_body = """                    body: JSON.stringify({
                        first_name: firstName,
                        last_name: lastName,
                        pin: document.getElementById('pin').value.trim()
                    })"""
content = content.replace(old_body, new_body)

# 3. Update the validation check to also require pin
old_check = """            if (!firstName || !lastName) {
                showError('Please enter both first and last name');
                return;
            }"""
new_check = """            const pin = document.getElementById('pin').value.trim();
            if (!firstName || !lastName || !pin) {
                showError('Please enter first name, last name, and PIN');
                return;
            }"""
content = content.replace(old_check, new_check)

# 4. Improve error display so we never see [object Object] again
old_err = "showError(data.detail || 'Login failed');"
new_err = "showError(typeof data.detail === 'string' ? data.detail : (JSON.stringify(data.detail) || 'Login failed'));"
content = content.replace(old_err, new_err)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("login.html fixed.")
print("Now run:")
print('  git add app/templates/login.html')
print('  git commit -m "Fix doLogin to send pin field"')
print('  git push')
