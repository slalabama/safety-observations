content = open('app/routers/admin_observations.py','r',encoding='utf-8').read()
old = 'from fastapi import APIRouter, HTTPException, Depends'
new = 'from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File'
content = content.replace(old, new)
open('app/routers/admin_observations.py','w',encoding='utf-8').write(content)
print('Done!')
