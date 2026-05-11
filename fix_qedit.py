c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
old = 's.questions.map(q => "<div style=\'padding:8px 16px;border-bottom:1px solid #f5f5f5;font-size:13px\'>" + q.text + "</div>").join("")'
new = 's.questions.map(q => "<div style=\'padding:8px 16px;border-bottom:1px solid #f5f5f5;font-size:13px;display:flex;align-items:center;\'><span style=\'flex:1\'>" + q.text + "</span><span style=\'font-size:11px;background:#e8f0fe;color:#1a2b4a;padding:2px 8px;border-radius:10px;margin-right:8px;\'>" + q.question_type + "</span><button onclick=\'editQuestion(" + form.id + "," + s.id + "," + q.id + ",\\\'" + q.text + "\\\',\\\'" + q.question_type + "\\\')\' style=\'margin-right:4px;padding:3px 8px;background:#1a2b4a;color:white;border:none;border-radius:4px;font-size:11px;cursor:pointer;\'>Edit</button><button onclick=\'deleteWalkQuestion(" + form.id + "," + s.id + "," + q.id + ")\' style=\'padding:3px 8px;background:#dc3545;color:white;border:none;border-radius:4px;font-size:11px;cursor:pointer;\'>Delete</button></div>").join("")'
c = c.replace(old, new)
print('Replaced:', old in open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read())
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('Done:', len(c))
