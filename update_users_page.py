html = open('app/templates/admin_users_page.html', 'r', encoding='utf-8').read()

old = '''                        <div class="form-group">
                            <label>Department</label>
                            <input type="text" id="dept" placeholder="e.g. Manufacturing">
                        </div>
                        <button class="btn-primary" onclick="addEmployee()">Add Employee</button>'''

new = '''                        <div class="form-group">
                            <label>Department</label>
                            <input type="text" id="dept" placeholder="e.g. Manufacturing">
                        </div>
                        <div class="form-group">
                            <label>Access Level</label>
                            <select id="role" style="width:100%;padding:10px 14px;border:2px solid #e0e0e0;border-radius:8px;font-size:14px;outline:none;">
                                <option value="basic">Basic User</option>
                                <option value="admin">Administrator</option>
                            </select>
                        </div>
                        <button class="btn-primary" onclick="addEmployee()">Add Employee</button>'''

updated = html.replace(old, new)

old2 = "body: JSON.stringify({ badge, name: empName, department: dept || null })"
new2 = "body: JSON.stringify({ badge, name: empName, department: dept || null, role: document.getElementById('role').value })"
updated = updated.replace(old2, new2)

old3 = '<th>Badge</th><th>Name</th><th>Department</th><th>Action</th>'
new3 = '<th>Badge</th><th>Name</th><th>Department</th><th>Role</th><th>Action</th>'
updated = updated.replace(old3, new3)

old4 = '''                    <td></td>
                    <td><button class="btn-delete"'''
new4 = '''                    <td></td>
                    <td><span class="badge-pill "></span></td>
                    <td><button class="btn-delete"'''
updated = updated.replace(old4, new4)

old5 = '        .badge-dept { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: #e8f0fe; color: #1a2b4a; }'
new5 = '''        .badge-dept { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: #e8f0fe; color: #1a2b4a; }
        .badge-pill { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
        .badge-admin { background: #1a2b4a; color: white; }
        .badge-basic { background: #e8f0fe; color: #1a2b4a; }'''
updated = updated.replace(old5, new5)

with open('app/templates/admin_users_page.html', 'w', encoding='utf-8') as f:
    f.write(updated)

import os
print('Updated! Size:', os.path.getsize('app/templates/admin_users_page.html'), 'bytes')
