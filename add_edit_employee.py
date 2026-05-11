content = open('app/templates/admin_users_page.html','r',encoding='utf-8').read()

# Add email column to table header
old = '<th>Badge</th><th>Name</th><th>Department</th><th>Role</th><th>Action</th>'
new = '<th>Badge</th><th>Name</th><th>Department</th><th>Role</th><th>Email</th><th>Action</th>'
content = content.replace(old, new)

# Add email cell and edit button to table rows
old2 = '''<td><button class="btn-delete" onclick="deleteEmployee(, '')" title="Delete">🗑️</button></td>'''
new2 = '''<td style="font-size:12px;color:#666;"></td>
                    <td>
                        <button class="btn-delete" onclick="editEmployee(, '', '', '', '', '')" title="Edit" style="background:none;border:none;color:#1a2b4a;cursor:pointer;font-size:16px;margin-right:4px;">✏️</button>
                        <button class="btn-delete" onclick="deleteEmployee(, '')" title="Delete">🗑️</button>
                    </td>'''
content = content.replace(old2, new2)

# Add editEmployee function before logout
old3 = 'async function logout()'
new3 = '''async function editEmployee(id, name, badge, dept, role, email) {
    const newEmail = prompt('Edit email for ' + name + ':', email);
    if (newEmail === null) return;
    const res = await fetch('/api/users/' + id, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        credentials: 'include',
        body: JSON.stringify({badge, name, department: dept||null, role, email: newEmail||null})
    });
    if (res.ok) { loadEmployees(); }
    else alert('Update failed');
}

async function logout()'''
content = content.replace(old3, new3)

open('app/templates/admin_users_page.html','w',encoding='utf-8').write(content)
print('Done:', len(content))
