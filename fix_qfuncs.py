c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
old = 'async function logout()'
new = '''async function deleteWalkQuestion(formId, sectionId, questionId) {
    if (!confirm('Delete this question?')) return;
    const res = await fetch('/api/walkarounds/' + formId + '/sections/' + sectionId + '/questions/' + questionId, {method:'DELETE',credentials:'include'});
    if (res.ok) { toggleForm(formId); setTimeout(()=>toggleForm(formId),100); }
    else alert('Delete failed');
}

async function editQuestion(formId, sectionId, questionId, currentText, currentType) {
    const newText = prompt('Edit question text:', currentText);
    if (!newText || newText === currentText) return;
    const res = await fetch('/api/walkarounds/' + formId + '/sections/' + sectionId + '/questions/' + questionId, {
        method:'PUT',
        headers:{'Content-Type':'application/json'},
        credentials:'include',
        body:JSON.stringify({text:newText, question_type:currentType, order:0})
    });
    if (res.ok) { toggleForm(formId); setTimeout(()=>toggleForm(formId),100); }
    else alert('Edit failed');
}

async function logout()'''
c = c.replace(old, new)
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('Done:', len(c))
