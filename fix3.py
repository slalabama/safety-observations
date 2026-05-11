c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
start = c.find('container.innerHTML = form.questions')
end = c.find('} catch (err)', start)
new_code = 'container.innerHTML = form.sections.map(s => s.name + ": " + s.questions.length + " questions").join("<br>");\n            '
c = c[:start] + new_code + c[end:]
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('sort left:', c.count('.sort('))
print('questions left:', c.count('form.questions'))
