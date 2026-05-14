"""
Mobile Walk-Around form flow:
  - Login by First/Last Name OR Employee ID (same as /observe)
  - Pick a walk-around form from a dropdown
  - Form renders its sections + questions:
      * pass_fail / yes_no_na  -> Yes / No / N/A buttons
      * text                   -> text input
  - One photo + one video for the whole form, 10 MB max each
  - Submit -> stored in walkaround_submissions
  - SL logo top-left
  - Adds a dashboard link

Run from C:\\projects\\safety-observations:
    python build_walkaround_flow.py
"""
import os, re

ROOT = os.getcwd()

# ---------------------------------------------------------------------------
# 1. Add photo_data / video_data columns to WalkaroundSubmission
# ---------------------------------------------------------------------------
models_path = os.path.join(ROOT, "app/models.py")
with open(models_path, "r", encoding="utf-8") as f:
    models = f.read()

if "photo_data" not in models.split("class WalkaroundSubmission")[1] if "class WalkaroundSubmission" in models else False:
    pass  # handled below

if "class WalkaroundSubmission" in models:
    sub_block = models.split("class WalkaroundSubmission")[1]
    if "photo_data" not in sub_block:
        models = models.replace(
            "    responses = Column(JSON, nullable=True)\n    \n    created_at = Column(DateTime, default=datetime.utcnow)\n    \n    employee = relationship(\"Employee\", back_populates=\"walkaround_submissions\")",
            "    responses = Column(JSON, nullable=True)\n"
            "    photo_data = Column(Text, nullable=True)\n"
            "    video_data = Column(Text, nullable=True)\n"
            "    \n    created_at = Column(DateTime, default=datetime.utcnow)\n"
            "    \n    employee = relationship(\"Employee\", back_populates=\"walkaround_submissions\")",
        )
        # Fallback: simpler anchor if the above didn't match
        if "photo_data" not in models.split("class WalkaroundSubmission")[1]:
            models = re.sub(
                r'(class WalkaroundSubmission.*?responses = Column\(JSON, nullable=True\))',
                r'\1\n    photo_data = Column(Text, nullable=True)\n    video_data = Column(Text, nullable=True)',
                models, flags=re.DOTALL,
            )
        with open(models_path, "w", encoding="utf-8") as f:
            f.write(models)
        print("Added photo_data/video_data to WalkaroundSubmission model")
    else:
        print("WalkaroundSubmission already has photo_data/video_data")

# ---------------------------------------------------------------------------
# 2. Auto-migrate the new columns on startup
# ---------------------------------------------------------------------------
main_path = os.path.join(ROOT, "app/main.py")
with open(main_path, "r", encoding="utf-8") as f:
    main = f.read()

if "ADD COLUMN IF NOT EXISTS photo_data" not in main or "walkaround_submissions" not in main:
    block = '''

@app.on_event("startup")
def _ensure_walkaround_submission_fields():
    from sqlalchemy import text
    from app.database import engine, Base
    try:
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE walkaround_submissions ADD COLUMN IF NOT EXISTS photo_data TEXT"))
            conn.execute(text("ALTER TABLE walkaround_submissions ADD COLUMN IF NOT EXISTS video_data TEXT"))
            conn.commit()
        print("[startup] walkaround_submissions columns ensured")
    except Exception as e:
        print(f"[startup] walkaround_submissions migration failed: {e}")
'''
    main = main.rstrip() + block + "\n"
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(main)
    print("Added auto-migration for walkaround_submissions media columns")

# ---------------------------------------------------------------------------
# 3. Add the /api/walkarounds/submit endpoint
# ---------------------------------------------------------------------------
wa_path = os.path.join(ROOT, "app/routers/admin_walkarounds.py")
with open(wa_path, "r", encoding="utf-8") as f:
    wa = f.read()

# Make sure Request is imported
if "Request" not in wa.split("\n")[0]:
    wa = wa.replace(
        "from fastapi import APIRouter, UploadFile, File, HTTPException, Depends",
        "from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request",
    )

if "/submit" not in wa or "submit_walkaround" not in wa:
    submit_endpoint = '''

@router.post("/submit")
async def submit_walkaround(
    request: Request,
    db: Session = Depends(get_db)
):
    """Walk-around form submission. Identified by badge or observe-login session."""
    import json, base64
    from datetime import datetime
    from app.models import WalkaroundSubmission, Employee, SessionRecord

    MAX_BYTES = 10 * 1024 * 1024  # 10 MB

    form = await request.form()
    try:
        form_id = int(form.get("form_id", 0))
    except (TypeError, ValueError):
        form_id = 0
    badge = (form.get("badge") or "").strip()
    responses_raw = form.get("responses", "{}")
    try:
        responses = json.loads(responses_raw)
    except Exception:
        responses = {}

    if not form_id:
        raise HTTPException(status_code=400, detail="No walk-around form selected.")

    # Identify employee
    employee = None
    if badge:
        employee = db.query(Employee).filter(Employee.badge == badge).first()
    if not employee:
        token = request.cookies.get("session_token")
        if token:
            sr = db.query(SessionRecord).filter(SessionRecord.id == token).first()
            if sr and sr.expires_at > datetime.utcnow():
                employee = sr.employee
    if not employee:
        raise HTTPException(status_code=401, detail="Please log in again.")

    photo_data = None
    video_data = None

    photo = form.get("photo")
    if photo and hasattr(photo, "filename") and photo.filename:
        content = await photo.read()
        if len(content) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Photo exceeds 10 MB limit.")
        photo_data = base64.b64encode(content).decode("ascii")

    video = form.get("video")
    if video and hasattr(video, "filename") and video.filename:
        content = await video.read()
        if len(content) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Video exceeds 10 MB limit.")
        video_data = base64.b64encode(content).decode("ascii")

    record = WalkaroundSubmission(
        employee_id=employee.id,
        form_id=form_id,
        responses=responses,
        photo_data=photo_data,
        video_data=video_data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "submission_id": record.id,
        "employee_name": employee.name,
        "message": "Walk-around submitted successfully."
    }
'''
    wa = wa.rstrip() + "\n" + submit_endpoint + "\n"
    with open(wa_path, "w", encoding="utf-8") as f:
        f.write(wa)
    print("Added /api/walkarounds/submit endpoint")
else:
    print("walkaround submit endpoint already present")

# ---------------------------------------------------------------------------
# 4. Create the mobile /walkaround page
# ---------------------------------------------------------------------------
html_path = os.path.join(ROOT, "app/templates/employee_walkaround.html")
walkaround_html = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Walk-Around Inspection</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a2b4a; min-height: 100vh; color: #333; }
        .page-logo { position: fixed; top: 16px; left: 16px; z-index: 10; }
        .page-logo img { max-width: 110px; height: auto; display: block; }
        .screen { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px 16px; }
        .card { background: white; border-radius: 12px; padding: 32px; width: 100%; max-width: 560px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        h1 { color: #1a2b4a; font-size: 22px; font-weight: 700; margin-bottom: 4px; }
        h2 { color: #1a2b4a; font-size: 16px; font-weight: 700; margin: 20px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #eef; }
        .subtitle { color: #666; font-size: 14px; margin-bottom: 20px; }
        label { display: block; color: #333; font-size: 14px; font-weight: 600; margin: 12px 0 6px; }
        input[type=text], select, textarea {
            width: 100%; padding: 12px 14px; border: 2px solid #e0e0e0; border-radius: 8px;
            font-size: 16px; outline: none; font-family: inherit; background: white;
        }
        textarea { min-height: 70px; resize: vertical; }
        input:focus, select:focus, textarea:focus { border-color: #1a2b4a; }
        .or-divider { text-align: center; color: #999; margin: 14px 0 4px; font-size: 13px; }
        .btn { display: block; width: 100%; padding: 14px; background: #1a2b4a; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 18px; }
        .btn:hover { background: #243d6b; }
        .btn:disabled { background: #999; cursor: not-allowed; }
        .btn-submit { background: #28a745; }
        .btn-submit:hover { background: #218838; }
        .greeting { background: #eaf3ff; border-radius: 8px; padding: 12px; margin-bottom: 16px; font-size: 14px; color: #1a2b4a; }
        .q-card { background: #fafbfc; border: 1px solid #eee; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
        .q-label { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #333; }
        .ynna { display: flex; gap: 8px; }
        .ynna button {
            flex: 1; padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px;
            font-size: 14px; font-weight: 600; cursor: pointer; background: white; transition: all 0.15s;
        }
        .ynna button.sel-yes { border-color: #28a745; background: #d4edda; color: #155724; }
        .ynna button.sel-no  { border-color: #dc3545; background: #f8d7da; color: #721c24; }
        .ynna button.sel-na  { border-color: #6c757d; background: #e2e3e5; color: #383d41; }
        .media-row { display: flex; gap: 10px; margin-top: 8px; }
        .media-btn { flex: 1; padding: 14px; border: 2px dashed #c0c0c0; border-radius: 8px; text-align: center; cursor: pointer; background: #fafafa; font-size: 14px; color: #555; }
        .media-btn:hover { border-color: #1a2b4a; background: #f0f4ff; }
        .media-btn .icon { display: block; font-size: 22px; margin-bottom: 4px; }
        #photoInput, #videoInput { display: none; }
        .preview { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
        .preview-item { position: relative; padding: 6px 10px; background: #eaf3ff; border-radius: 6px; font-size: 13px; }
        .preview-item .remove { margin-left: 8px; color: #d33; cursor: pointer; font-weight: bold; }
        .error-msg { display: none; background: #fff0f0; border: 1px solid #dc3545; color: #dc3545; padding: 10px 14px; border-radius: 8px; font-size: 14px; margin: 10px 0; }
        .success-icon { font-size: 64px; text-align: center; margin-bottom: 16px; }
        .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; vertical-align: middle; margin-right: 6px; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="page-logo">
        <img src="https://www.sl-america.com/wp-content/uploads/logo.png" alt="SL Logo">
    </div>

    <!-- LOGIN -->
    <div class="screen" id="loginScreen">
        <div class="card">
            <h1>Walk-Around Inspection</h1>
            <div class="subtitle">SL Alabama, LLC</div>
            <div style="font-size:13px;color:#666;margin-bottom:8px;">
                Enter your <strong>First and Last Name</strong>, or your <strong>Employee ID</strong>.
            </div>
            <label for="firstName">First Name</label>
            <input type="text" id="firstName" placeholder="First Name">
            <label for="lastName">Last Name</label>
            <input type="text" id="lastName" placeholder="Last Name">
            <div class="or-divider">— OR —</div>
            <label for="badge">Employee ID</label>
            <input type="text" id="badge" placeholder="Employee ID" inputmode="numeric">
            <div class="error-msg" id="loginError"></div>
            <button class="btn" id="loginBtn" onclick="doLogin()">Continue →</button>
        </div>
    </div>

    <!-- FORM PICKER -->
    <div class="screen" id="pickerScreen" style="display:none;">
        <div class="card">
            <div class="greeting">Inspecting as <strong id="empNameDisplay"></strong></div>
            <h1>Select a Walk-Around Form</h1>
            <div class="subtitle">Choose the inspection you want to complete.</div>
            <label for="formSelect">Walk-Around Form</label>
            <select id="formSelect">
                <option value="">— Select a form —</option>
            </select>
            <div class="error-msg" id="pickerError"></div>
            <button class="btn" onclick="loadForm()">Open Form →</button>
            <button class="btn" style="background:#ddd;color:#333;margin-top:10px;" onclick="logout()">Cancel</button>
        </div>
    </div>

    <!-- FORM FILL -->
    <div class="screen" id="formScreen" style="display:none;">
        <div class="card">
            <div class="greeting">Inspecting as <strong id="empNameDisplay2"></strong></div>
            <h1 id="formTitle"></h1>
            <div class="subtitle" id="formDesc"></div>

            <div id="sectionsContainer"></div>

            <label>Photo (optional, max 10 MB)</label>
            <div class="media-row">
                <div class="media-btn" onclick="pickFile('photoInput')">
                    <span class="icon">📷</span><span id="photoBtnLabel">Add Photo</span>
                </div>
            </div>
            <input type="file" id="photoInput" accept="image/*" capture="environment" onchange="handleFile(this,'photo')">

            <label>Video (optional, max 10 MB)</label>
            <div class="media-row">
                <div class="media-btn" onclick="pickFile('videoInput')">
                    <span class="icon">🎥</span><span id="videoBtnLabel">Add Video</span>
                </div>
            </div>
            <input type="file" id="videoInput" accept="video/*" capture="environment" onchange="handleFile(this,'video')">

            <div class="preview" id="mediaPreview"></div>

            <div class="error-msg" id="formError"></div>
            <button class="btn btn-submit" id="submitBtn" onclick="submitForm()">Submit Walk-Around</button>
            <button class="btn" style="background:#ddd;color:#333;margin-top:10px;" onclick="backToPicker()">Back</button>
        </div>
    </div>

    <!-- SUCCESS -->
    <div class="screen" id="successScreen" style="display:none;">
        <div class="card" style="text-align:center;">
            <div class="success-icon">✅</div>
            <h1>Submitted!</h1>
            <div class="subtitle">Your walk-around inspection has been recorded.</div>
            <button class="btn" onclick="backToPicker()">Do Another</button>
            <button class="btn" style="background:#ddd;color:#333;margin-top:10px;" onclick="logout()">Done</button>
        </div>
    </div>

    <script>
        const MAX_BYTES = 10 * 1024 * 1024;
        let currentEmployee = null;
        let currentForm = null;
        let answers = {};
        let photoFile = null, videoFile = null;

        function showError(id, msg) { const e = document.getElementById(id); e.textContent = msg; e.style.display = 'block'; }
        function hideError(id) { document.getElementById(id).style.display = 'none'; }

        async function doLogin() {
            hideError('loginError');
            const firstName = document.getElementById('firstName').value.trim();
            const lastName  = document.getElementById('lastName').value.trim();
            const badge     = document.getElementById('badge').value.trim();
            if (!badge && (!firstName || !lastName)) {
                showError('loginError', 'Enter first and last name, or your Employee ID.');
                return;
            }
            const btn = document.getElementById('loginBtn');
            btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Verifying...';
            try {
                const res = await fetch('/api/auth/observe-login', {
                    method: 'POST', headers: {'Content-Type':'application/json'}, credentials: 'include',
                    body: JSON.stringify({ first_name: firstName, last_name: lastName, badge: badge })
                });
                const data = await res.json();
                if (res.ok) {
                    currentEmployee = { name: data.employee_name, badge: data.badge };
                    document.getElementById('empNameDisplay').textContent = data.employee_name;
                    document.getElementById('empNameDisplay2').textContent = data.employee_name;
                    await loadFormList();
                    document.getElementById('loginScreen').style.display = 'none';
                    document.getElementById('pickerScreen').style.display = 'flex';
                } else {
                    showError('loginError', typeof data.detail === 'string' ? data.detail : 'Login failed.');
                }
            } catch (e) {
                showError('loginError', 'Connection error. Please try again.');
            } finally {
                btn.disabled = false; btn.textContent = 'Continue →';
            }
        }

        async function loadFormList() {
            const sel = document.getElementById('formSelect');
            sel.innerHTML = '<option value="">— Select a form —</option>';
            try {
                const res = await fetch('/api/walkarounds/', { credentials: 'include' });
                if (res.ok) {
                    const forms = await res.json();
                    forms.filter(f => f.active !== false).forEach(f => {
                        const opt = document.createElement('option');
                        opt.value = f.id;
                        opt.textContent = f.name;
                        sel.appendChild(opt);
                    });
                }
            } catch (e) { /* ignore */ }
        }

        async function loadForm() {
            hideError('pickerError');
            const formId = document.getElementById('formSelect').value;
            if (!formId) { showError('pickerError', 'Please select a form.'); return; }
            try {
                const res = await fetch('/api/walkarounds/' + formId, { credentials: 'include' });
                if (!res.ok) { showError('pickerError', 'Could not load that form.'); return; }
                currentForm = await res.json();
                renderForm();
                document.getElementById('pickerScreen').style.display = 'none';
                document.getElementById('formScreen').style.display = 'flex';
            } catch (e) {
                showError('pickerError', 'Connection error. Please try again.');
            }
        }

        function renderForm() {
            answers = {};
            photoFile = null; videoFile = null;
            document.getElementById('mediaPreview').innerHTML = '';
            document.getElementById('photoBtnLabel').textContent = 'Add Photo';
            document.getElementById('videoBtnLabel').textContent = 'Add Video';
            document.getElementById('formTitle').textContent = currentForm.name || 'Walk-Around';
            document.getElementById('formDesc').textContent  = currentForm.description || '';

            const container = document.getElementById('sectionsContainer');
            container.innerHTML = '';
            (currentForm.sections || []).forEach(section => {
                const h = document.createElement('h2');
                h.textContent = section.name;
                container.appendChild(h);
                (section.questions || []).forEach(q => {
                    const card = document.createElement('div');
                    card.className = 'q-card';
                    const label = document.createElement('div');
                    label.className = 'q-label';
                    label.textContent = q.text;
                    card.appendChild(label);

                    if (q.question_type === 'text') {
                        const inp = document.createElement('input');
                        inp.type = 'text';
                        inp.placeholder = 'Enter response...';
                        inp.oninput = e => { answers[q.id] = e.target.value; };
                        card.appendChild(inp);
                    } else {
                        // pass_fail and yes_no_na both render Yes / No / N/A
                        const group = document.createElement('div');
                        group.className = 'ynna';
                        ['Yes','No','N/A'].forEach(val => {
                            const b = document.createElement('button');
                            b.type = 'button';
                            b.textContent = val;
                            b.onclick = () => {
                                answers[q.id] = val;
                                Array.from(group.children).forEach(c => c.className = '');
                                b.className = val === 'Yes' ? 'sel-yes' : (val === 'No' ? 'sel-no' : 'sel-na');
                            };
                            group.appendChild(b);
                        });
                        card.appendChild(group);
                    }
                    container.appendChild(card);
                });
            });
        }

        function pickFile(id) { const el = document.getElementById(id); el.value = null; el.click(); }

        function handleFile(input, type) {
            hideError('formError');
            const file = input.files[0];
            if (!file) return;
            if (file.size > MAX_BYTES) {
                showError('formError', (type === 'photo' ? 'Photo' : 'Video') + ' exceeds 10 MB limit.');
                input.value = null;
                return;
            }
            if (type === 'photo') { photoFile = file; document.getElementById('photoBtnLabel').textContent = 'Replace Photo'; }
            else { videoFile = file; document.getElementById('videoBtnLabel').textContent = 'Replace Video'; }
            renderPreview();
        }

        function renderPreview() {
            const c = document.getElementById('mediaPreview');
            c.innerHTML = '';
            if (photoFile) {
                const i = document.createElement('div');
                i.className = 'preview-item';
                i.innerHTML = '📷 ' + photoFile.name + ' (' + (photoFile.size/1024/1024).toFixed(2) + ' MB) <span class="remove" onclick="clearMedia(\'photo\')">×</span>';
                c.appendChild(i);
            }
            if (videoFile) {
                const i = document.createElement('div');
                i.className = 'preview-item';
                i.innerHTML = '🎥 ' + videoFile.name + ' (' + (videoFile.size/1024/1024).toFixed(2) + ' MB) <span class="remove" onclick="clearMedia(\'video\')">×</span>';
                c.appendChild(i);
            }
        }

        function clearMedia(type) {
            if (type === 'photo') { photoFile = null; document.getElementById('photoInput').value = null; document.getElementById('photoBtnLabel').textContent = 'Add Photo'; }
            else { videoFile = null; document.getElementById('videoInput').value = null; document.getElementById('videoBtnLabel').textContent = 'Add Video'; }
            renderPreview();
        }

        async function submitForm() {
            hideError('formError');
            const btn = document.getElementById('submitBtn');
            btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Submitting...';

            const fd = new FormData();
            fd.append('form_id', currentForm.id);
            fd.append('responses', JSON.stringify(answers));
            if (currentEmployee && currentEmployee.badge) fd.append('badge', currentEmployee.badge);
            if (photoFile) fd.append('photo', photoFile);
            if (videoFile) fd.append('video', videoFile);

            try {
                const res = await fetch('/api/walkarounds/submit', {
                    method: 'POST', credentials: 'include', body: fd
                });
                const data = await res.json();
                if (res.ok) {
                    document.getElementById('formScreen').style.display = 'none';
                    document.getElementById('successScreen').style.display = 'flex';
                } else {
                    showError('formError', typeof data.detail === 'string' ? data.detail : 'Submission failed.');
                }
            } catch (e) {
                showError('formError', 'Connection error. Please try again.');
            } finally {
                btn.disabled = false; btn.textContent = 'Submit Walk-Around';
            }
        }

        function backToPicker() {
            document.getElementById('formScreen').style.display = 'none';
            document.getElementById('successScreen').style.display = 'none';
            document.getElementById('formSelect').value = '';
            document.getElementById('pickerScreen').style.display = 'flex';
        }

        function logout() {
            currentEmployee = null; currentForm = null; answers = {};
            photoFile = null; videoFile = null;
            ['firstName','lastName','badge'].forEach(id => document.getElementById(id).value = '');
            document.getElementById('pickerScreen').style.display = 'none';
            document.getElementById('formScreen').style.display = 'none';
            document.getElementById('successScreen').style.display = 'none';
            document.getElementById('loginScreen').style.display = 'flex';
        }

        ['firstName','lastName','badge'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('keypress', e => { if (e.key === 'Enter') doLogin(); });
        });
    </script>
</body>
</html>
"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(walkaround_html)
print("Created app/templates/employee_walkaround.html")

# ---------------------------------------------------------------------------
# 5. Add a dashboard link to the walk-around submission page
# ---------------------------------------------------------------------------
dash_path = os.path.join(ROOT, "app/templates/dashboard.html")
if os.path.exists(dash_path):
    with open(dash_path, "r", encoding="utf-8") as f:
        dash = f.read()

    if 'href="/walkaround"' not in dash:
        # Add the link right after the "Submit Observation" nav item
        m = re.search(
            r'(<a href="/observe"[^>]*>.*?</a>)',
            dash, flags=re.DOTALL,
        )
        if m:
            observe_link = m.group(1)
            new_link = observe_link + '\n            <a href="/walkaround" class="nav-item" target="_blank"><span class="nav-icon">\U0001f6b6</span> Submit Walk-Around</a>'
            dash = dash.replace(observe_link, new_link)
            with open(dash_path, "w", encoding="utf-8") as f:
                f.write(dash)
            print("Added 'Submit Walk-Around' link to dashboard")
        else:
            print("WARNING: could not find Submit Observation link in dashboard - add /walkaround link manually")
    else:
        print("Dashboard already has /walkaround link")
else:
    print("WARNING: dashboard.html not found")

print("\nDone. Run:")
print('  git add -A')
print('  git commit -m "Add mobile walk-around inspection flow"')
print('  git push')
