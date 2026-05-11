import os
html = open('app/templates/admin_walkarounds_page.html', 'r', encoding='utf-8').read()
html = html.replace('<title>Safety Observations - Employees</title>', '<title>Safety Observations - Walk-Around Forms</title>')
html = html.replace('<h1>👥 Employees</h1>', '<h1>🚶 Walk-Around Forms</h1>')
html = html.replace('1 employees registered', '0 forms')
html = html.replace('href="/admin/users" class="nav-item active"', 'href="/admin/users" class="nav-item"')
html = html.replace('href="/admin/walkarounds" class="nav-item"', 'href="/admin/walkarounds" class="nav-item active"')
with open('app/templates/admin_walkarounds_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done:', os.path.getsize('app/templates/admin_walkarounds_page.html'), 'bytes')
