c = open('app/templates/admin_users_page.html','r',encoding='utf-8').read()
old = "deleteEmployee(\, '\')" + '" title="Delete">🗑️</button></td>'
new = """editEmployee(\, '\', '\', '\', '\', '\')" style="background:none;border:none;color:#1a2b4a;cursor:pointer;font-size:16px;margin-right:4px;" title="Edit">✏️</button>
                    <button class="btn-delete" onclick="deleteEmployee(\, '\')" title="Delete">🗑️</button></td>"""
c = c.replace(old, new)
open('app/templates/admin_users_page.html','w',encoding='utf-8').write(c)
print('Done:', len(c))
