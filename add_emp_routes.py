content = open('app/routers/admin_pages.py','r',encoding='utf-8').read()
new_routes = '''
@router.get("/observe", response_class=HTMLResponse)
def observe_page(request: Request):
    return templates.TemplateResponse("employee_observe.html", {"request": request})

@router.get("/walkaround", response_class=HTMLResponse)
def walkaround_page(request: Request):
    return templates.TemplateResponse("employee_walkaround.html", {"request": request})
'''
content = content + new_routes
open('app/routers/admin_pages.py','w',encoding='utf-8').write(content)
print('Done!')
