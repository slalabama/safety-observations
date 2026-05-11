html = open('app/templates/admin_observations_page.html', 'r', encoding='utf-8').read()
html = html.replace('Safety Observations - Observation Forms', 'Safety Observations - Walk-Around Forms')
html = html.replace('Observation Forms</h1>', 'Walk-Around Forms</h1>')
html = html.replace('href="/admin/observations" class="nav-item active"', 'href="/admin/observations" class="nav-item"')
html = html.replace('href="/admin/walkarounds" class="nav-item"', 'href="/admin/walkarounds" class="nav-item active"')
html = html.replace('/api/observations/forms/', '/api/walkarounds/')
with open('app/templates/admin_walkarounds_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
import os
print('Done:', os.path.getsize('app/templates/admin_walkarounds_page.html'), 'bytes')
