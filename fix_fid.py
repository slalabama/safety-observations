c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
c = c.replace('form.id', 'formId')
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('Done. form.id remaining:', c.count('form.id'))
