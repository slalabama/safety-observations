content = open('app/main.py','r',encoding='utf-8').read()
old = 'from app.routers import admin_auth, admin_users, admin_observations, admin_walkarounds, admin_pages'
new = 'from app.routers import admin_auth, admin_users, admin_observations, admin_walkarounds, admin_pages, setup'
content = content.replace(old, new)
old2 = 'app.include_router(admin_pages.router)'
new2 = 'app.include_router(admin_pages.router)\napp.include_router(setup.router)'
content = content.replace(old2, new2)
open('app/main.py','w',encoding='utf-8').write(content)
print('Done!')
