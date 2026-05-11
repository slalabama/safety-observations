c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
start = c.find('container.innerHTML = form.sections.map')
end = c.find('} catch (err)', start)
new_code = 'container.innerHTML = form.sections.map(s => "<div style=\'border-bottom:2px solid #e8f0fe\'><div style=\'padding:10px 16px;background:#1a2b4a;color:white;font-weight:700;font-size:13px;display:flex;justify-content:space-between\'><span>" + s.name + "</span><span style=\'font-size:11px;opacity:0.7\'>" + s.questions.length + " items</span></div>" + s.questions.map(q => "<div style=\'padding:8px 16px;border-bottom:1px solid #f5f5f5;font-size:13px\'>" + q.text + "</div>").join("") + "</div>").join("");\n            '
c = c[:start] + new_code + c[end:]
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('Done:', len(c))
