import os
html = open('app/templates/admin_users_page.html', 'r', encoding='utf-8').read()

html = html.replace('Safety Observations - Employees', 'Safety Observations - Walk-Around Forms')
html = html.replace('href="/admin/users" class="nav-item active"', 'href="/admin/users" class="nav-item XX"')
html = html.replace('href="/admin/walkarounds" class="nav-item"', 'href="/admin/walkarounds" class="nav-item active"')
html = html.replace('nav-item XX', 'nav-item')

with open('app/templates/admin_walkarounds_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done:', os.path.getsize('app/templates/admin_walkarounds_page.html'))
