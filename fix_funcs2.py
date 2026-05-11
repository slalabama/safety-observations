c = open('app/templates/admin_walkarounds_page.html','r',encoding='utf-8').read()
old = 'async function deleteQuestion(formId, questionId)'
new = '''async function deleteWalkQuestion(formId, sectionId, questionId) {
    if (!confirm('Delete this question?')) return;
    const res = await fetch('/api/walkarounds/' + formId + '/sections/' + sectionId + '/questions/' + questionId, {method:'DELETE',credentials:'include'});
    if (res.ok) { document.querySelectorAll('.form-item-body').forEach(b=>b.classList.remove('open')); loadForms(); setTimeout(()=>{const el=document.getElementById('body-'+formId);if(el){el.classList.add('open');loadQuestions(formId);}},300); }
    else alert('Delete failed - check console');
}
async function editQuestion(formId, sectionId, questionId, currentText, currentType) {
    const newText = prompt('Edit question:', currentText);
    if (!newText || newText === currentText) return;
    const res = await fetch('/api/walkarounds/' + formId + '/sections/' + sectionId + '/questions/' + questionId, {method:'PUT',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({text:newText,question_type:currentType,order:0})});
    if (res.ok) { document.querySelectorAll('.form-item-body').forEach(b=>b.classList.remove('open')); loadForms(); setTimeout(()=>{const el=document.getElementById('body-'+formId);if(el){el.classList.add('open');loadQuestions(formId);}},300); }
    else alert('Edit failed');
}
async function deleteQuestion(formId, questionId)'''
c = c.replace(old, new)
open('app/templates/admin_walkarounds_page.html','w',encoding='utf-8').write(c)
print('Done:', len(c))
