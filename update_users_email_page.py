content = open('app/templates/admin_users_page.html','r',encoding='utf-8').read()
old = '                        <div class="form-group">\n                            <label>Department</label>\n                            <input type="text" id="dept" placeholder="e.g. Manufacturing">\n                        </div>'
new = '                        <div class="form-group">\n                            <label>Department</label>\n                            <input type="text" id="dept" placeholder="e.g. Manufacturing">\n                        </div>\n                        <div class="form-group">\n                            <label>Email (required for Admins)</label>\n                            <input type="email" id="empEmail" placeholder="e.g. john@company.com">\n                        </div>'
content = content.replace(old, new)
old2 = "body: JSON.stringify({ badge, name: empName, department: dept || null, role: document.getElementById('role').value })"
new2 = "body: JSON.stringify({ badge, name: empName, department: dept || null, role: document.getElementById('role').value, email: document.getElementById('empEmail').value || null })"
content = content.replace(old2, new2)
open('app/templates/admin_users_page.html','w',encoding='utf-8').write(content)
print('Users page updated!')
