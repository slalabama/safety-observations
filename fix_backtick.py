c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
old = "+ ',\\' + q.text.replace(//g,'') + '\\' +"
new = "+ ',\"' + q.text.replace(/\"/g,'') + '\"' +"
c = c.replace(old, new)
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('Done:', len(c))
