c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
old = "onclick=\'editQuestion(" + form.id + ","
new = "onclick=\'editQuestion(" + f.id + ","
c = c.replace(old, new)
old2 = "onclick=\'deleteWalkQuestion(" + form.id + ","
new2 = "onclick=\'deleteWalkQuestion(" + f.id + ","
c = c.replace(old2, new2)
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('Done:', len(c))
