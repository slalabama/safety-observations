html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Safety Observations - Employees</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; display: flex; min-height: 100vh; }
        .sidebar { width: 260px; background: #1a2b4a; color: white; display: flex; flex-direction: column; position: fixed; height: 100vh; z-index: 100; }
        .sidebar-logo { padding: 24px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-logo h2 { font-size: 16px; font-weight: 700; color: white; }
        .sidebar-logo p { font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 2px; }
        .sidebar-logo .logo-icon { font-size: 28px; margin-bottom: 8px; }
        .nav-section { padding: 16px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .nav-section-title { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; padding: 0 20px 8px; }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 20px; color: rgba(255,255,255,0.7); text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .nav-item:hover, .nav-item.active { background: rgba(255,255,255,0.1); color: white; }
        .nav-item.active { border-left: 3px solid #4a9eff; }
        .nav-icon { font-size: 18px; width: 24px; }
        .sidebar-footer { margin-top: auto; padding: 16px 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .user-info { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .user-avatar { width: 36px; height: 36px; background: #4a9eff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }
        .user-name { font-size: 13px; font-weight: 600; color: white; }
        .user-role { font-size: 11px; color: rgba(255,255,255,0.5); }
        .btn-logout { width: 100%; padding: 8px; background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.7); border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
        .btn-logout:hover { background: rgba(255,0,0,0.2); color: white; }
        .main { margin-left: 260px; flex: 1; display: flex; flex-direction: column; }
        .topbar { background: white; padding: 16px 32px; border-bottom: 1px solid #e0e0e0; display: flex; align-items: center; justify-content: space-between; }
        .topbar h1 { font-size: 20px; color: #1a2b4a; font-weight: 700; }
        .content { padding: 32px; flex: 1; }
        .top-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
        .card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
        .card-header { padding: 16px 20px; border-bottom: 1px solid #f0f0f0; }
        .card-header h3 { font-size: 15px; font-weight: 700; color: #1a2b4a; }
        .card-body { padding: 20px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; font-size: 13px; font-weight: 600; color: #333; margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 14px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; transition: border-color 0.2s; }
        .form-group input:focus { border-color: #1a2b4a; }
        .btn-primary { width: 100%; padding: 11px; background: #1a2b4a; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; }
        .btn-primary:hover { background: #243d6b; }
        .upload-area { border: 2px dashed #e0e0e0; border-radius: 8px; padding: 24px; text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 16px; }
        .upload-area:hover { border-color: #1a2b4a; background: #f8f9ff; }
        .upload-icon { font-size: 32px; margin-bottom: 8px; }
        .upload-text { font-size: 14px; color: #666; }
        .upload-sub { font-size: 12px; color: #999; margin-top: 4px; }
        #csvFile { display: none; }
        .import-result { margin-top: 12px; padding: 12px; border-radius: 8px; font-size: 13px; display: none; }
        .import-result.success { background: #d4edda; color: #155724; }
        .import-result.error { background: #f8d7da; color: #721c24; }
        .table-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
        .table-header { padding: 16px 20px; border-bottom: 1px solid #f0f0f0; display: flex; align-items: center; justify-content: space-between; }
        .table-header h3 { font-size: 15px; font-weight: 700; color: #1a2b4a; }
        .search-bar { padding: 12px 20px; border-bottom: 1px solid #f0f0f0; }
        .search-bar input { width: 100%; padding: 9px 14px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
        .search-bar input:focus { border-color: #1a2b4a; }
        table { width: 100%; border-collapse: collapse; }
        th { padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 600; color: #999; text-transform: uppercase; background: #fafafa; border-bottom: 1px solid #f0f0f0; }
        td { padding: 13px 16px; font-size: 14px; color: #333; border-bottom: 1px solid #f5f5f5; }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: #fafafa; }
        .btn-delete { background: none; border: none; color: #dc3545; cursor: pointer; font-size: 16px; padding: 4px 8px; border-radius: 4px; }
        .btn-delete:hover { background: #fff0f0; }
        .badge-dept { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: #e8f0fe; color: #1a2b4a; }
        .empty-state { padding: 40px; text-align: center; color: #999; font-size: 14px; }
        .alert { padding: 12px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 16px; display: none; }
        .alert.success { background: #d4edda; color: #155724; }
        .alert.error { background: #f8d7da; color: #721c24; }
        code { font-size: 11px; background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-logo">
            <div class="logo-icon">🦺</div>
            <h2>Safety Observations</h2>
            <p>Admin Portal</p>
        </div>
        <div class="nav-section">
            <div class="nav-section-title">Main</div>
            <a href="/admin/" class="nav-item"><span class="nav-icon">📊</span> Dashboard</a>
        </div>
        <div class="nav-section">
            <div class="nav-section-title">Management</div>
            <a href="/admin/users" class="nav-item active"><span class="nav-icon">👥</span> Employees</a>
            <a href="/admin/observations" class="nav-item"><span class="nav-icon">📋</span> Observation Forms</a>
            <a href="/admin/walkarounds" class="nav-item"><span class="nav-icon">🚶</span> Walk-Around Forms</a>
        </div>
        <div class="sidebar-footer">
            <div class="user-info">
                <div class="user-avatar" id="userAvatar">C</div>
                <div>
                    <div class="user-name" id="userName">Admin</div>
                    <div class="user-role">Administrator</div>
                </div>
            </div>
            <button class="btn-logout" onclick="logout()">🚪 Sign Out</button>
        </div>
    </div>
    <div class="main">
        <div class="topbar">
            <h1>👥 Employees</h1>
            <span style="font-size:13px;color:#666;" id="empCount">Loading...</span>
        </div>
        <div class="content">
            <div class="top-row">
                <div class="card">
                    <div class="card-header"><h3>➕ Add Employee</h3></div>
                    <div class="card-body">
                        <div class="alert" id="addAlert"></div>
                        <div class="form-group">
                            <label>Badge Number *</label>
                            <input type="text" id="badge" placeholder="e.g. 00123">
                        </div>
                        <div class="form-group">
                            <label>Full Name *</label>
                            <input type="text" id="empName" placeholder="e.g. John Smith">
                        </div>
                        <div class="form-group">
                            <label>Department</label>
                            <input type="text" id="dept" placeholder="e.g. Manufacturing">
                        </div>
                        <button class="btn-primary" onclick="addEmployee()">Add Employee</button>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header"><h3>📥 Import from CSV</h3></div>
                    <div class="card-body">
                        <div class="upload-area" onclick="document.getElementById('csvFile').click()">
                            <div class="upload-icon">📄</div>
                            <div class="upload-text">Click to select CSV file</div>
                            <div class="upload-sub">Format: badge, name, department</div>
                        </div>
                        <input type="file" id="csvFile" accept=".csv" onchange="importCSV(this)">
                        <div style="font-size:12px;color:#666;margin-bottom:8px;">
                            Example:<br>
                            <code>00001,John Smith,Manufacturing</code><br>
                            <code>00002,Jane Doe,Safety</code>
                        </div>
                        <div class="import-result" id="importResult"></div>
                    </div>
                </div>
            </div>
            <div class="table-card">
                <div class="table-header">
                    <h3>All Employees</h3>
                    <span style="font-size:13px;color:#666;" id="tableCount">0 employees</span>
                </div>
                <div class="search-bar">
                    <input type="text" id="searchInput" placeholder="🔍 Search by name, badge, or department..." oninput="filterTable()">
                </div>
                <table>
                    <thead>
                        <tr><th>Badge</th><th>Name</th><th>Department</th><th>Action</th></tr>
                    </thead>
                    <tbody id="empTable">
                        <tr><td colspan="4" class="empty-state">Loading employees...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
        let allEmployees = [];
        const name = localStorage.getItem('employee_name') || 'Admin';
        document.getElementById('userName').textContent = name;
        document.getElementById('userAvatar').textContent = name.charAt(0).toUpperCase();

        async function checkAuth() {
            const res = await fetch('/api/auth/me', { credentials: 'include' });
            if (!res.ok) window.location.href = '/admin/login';
        }

        async function loadEmployees() {
            try {
                const res = await fetch('/api/users/list', { credentials: 'include' });
                if (!res.ok) { window.location.href = '/admin/login'; return; }
                allEmployees = await res.json();
                renderTable(allEmployees);
                document.getElementById('empCount').textContent = allEmployees.length + ' employees registered';
                document.getElementById('tableCount').textContent = allEmployees.length + ' employees';
            } catch (err) { console.error(err); }
        }

        function renderTable(employees) {
            const tbody = document.getElementById('empTable');
            if (employees.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No employees found</td></tr>';
                return;
            }
            tbody.innerHTML = employees.map(e => `
                <tr>
                    <td><strong>${e.badge}</strong></td>
                    <td>${e.name}</td>
                    <td>${e.department ? '<span class="badge-dept">' + e.department + '</span>' : '<span style="color:#999">—</span>'}</td>
                    <td><button class="btn-delete" onclick="deleteEmployee(${e.id}, '${e.name}')" title="Delete">🗑️</button></td>
                </tr>
            `).join('');
        }

        function filterTable() {
            const q = document.getElementById('searchInput').value.toLowerCase();
            const filtered = allEmployees.filter(e =>
                e.name.toLowerCase().includes(q) ||
                e.badge.toLowerCase().includes(q) ||
                (e.department && e.department.toLowerCase().includes(q))
            );
            renderTable(filtered);
        }

        async function addEmployee() {
            const badge = document.getElementById('badge').value.trim();
            const empName = document.getElementById('empName').value.trim();
            const dept = document.getElementById('dept').value.trim();
            if (!badge || !empName) { showAlert('addAlert', 'error', 'Badge number and name are required'); return; }
            try {
                const res = await fetch('/api/users/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ badge, name: empName, department: dept || null })
                });
                const data = await res.json();
                if (res.ok) {
                    showAlert('addAlert', 'success', empName + ' added successfully!');
                    document.getElementById('badge').value = '';
                    document.getElementById('empName').value = '';
                    document.getElementById('dept').value = '';
                    loadEmployees();
                } else {
                    showAlert('addAlert', 'error', data.detail || 'Failed to add employee');
                }
            } catch (err) { showAlert('addAlert', 'error', 'Connection error'); }
        }

        async function deleteEmployee(id, name) {
            if (!confirm('Delete ' + name + '? This cannot be undone.')) return;
            try {
                const res = await fetch('/api/users/' + id, { method: 'DELETE', credentials: 'include' });
                if (res.ok) { loadEmployees(); } else { alert('Failed to delete employee'); }
            } catch (err) { alert('Connection error'); }
        }

        async function importCSV(input) {
            const file = input.files[0];
            if (!file) return;
            const resultDiv = document.getElementById('importResult');
            resultDiv.style.display = 'block';
            resultDiv.className = 'import-result';
            resultDiv.textContent = 'Importing...';
            const formData = new FormData();
            formData.append('file', file);
            try {
                const res = await fetch('/api/users/import-csv', { method: 'POST', credentials: 'include', body: formData });
                const data = await res.json();
                if (res.ok) {
                    resultDiv.className = 'import-result success';
                    resultDiv.innerHTML = 'Import complete! Imported: <strong>' + data.imported + '</strong> | Skipped: <strong>' + data.skipped + '</strong> | Total: <strong>' + data.total + '</strong>' + (data.duplicates.length > 0 ? '<br>' + data.duplicates.length + ' duplicates skipped' : '');
                    loadEmployees();
                } else {
                    resultDiv.className = 'import-result error';
                    resultDiv.textContent = 'Import failed: ' + (data.detail || 'Unknown error');
                }
            } catch (err) {
                resultDiv.className = 'import-result error';
                resultDiv.textContent = 'Connection error';
            }
            input.value = '';
        }

        function showAlert(id, type, msg) {
            const el = document.getElementById(id);
            el.className = 'alert ' + type;
            el.textContent = msg;
            el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 4000);
        }

        async function logout() {
            await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
            localStorage.removeItem('employee_name');
            window.location.href = '/admin/login';
        }

        checkAuth();
        loadEmployees();
    </script>
</body>
</html>"""

with open('app/templates/admin_users_page.html', 'w', encoding='utf-8') as f:
    f.write(html)

import os
print('Written:', os.path.getsize('app/templates/admin_users_page.html'), 'bytes')
print('Done!')
