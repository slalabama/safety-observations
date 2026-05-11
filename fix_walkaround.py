import os

with open('app/templates/admin_users_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('Safety Observations - Employees', 'Safety Observations - Walk-Around Forms')
html = html.replace('Walk-Around Forms</h1>', 'Walk-Around Forms - TEMP</h1>')
html = html.replace('nav-item active', 'nav-item')
html = html.replace('/admin/walkarounds" class="nav-item"', '/admin/walkarounds" class="nav-item active"')
html = html.replace('Walk-Around Forms - TEMP</h1>', 'Walk-Around Forms</h1>')

with open('app/templates/admin_walkarounds_page.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Written:', os.path.getsize('app/templates/admin_walkarounds_page.html'), 'bytes')
