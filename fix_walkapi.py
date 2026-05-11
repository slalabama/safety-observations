content = open('app/routers/admin_walkarounds.py','r',encoding='utf-8').read()
new_endpoints = '''
@router.delete("/{form_id}/sections/{section_id}/questions/{question_id}")
def delete_question(form_id: int, section_id: int, question_id: int, db: Session = Depends(get_db), admin = Depends(get_current_employee)):
    q = db.query(WalkaroundQuestion).filter(WalkaroundQuestion.id == question_id, WalkaroundQuestion.section_id == section_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": "Question deleted"}

@router.put("/{form_id}/sections/{section_id}/questions/{question_id}")
def update_question(form_id: int, section_id: int, question_id: int, question: QuestionCreate, db: Session = Depends(get_db), admin = Depends(get_current_employee)):
    q = db.query(WalkaroundQuestion).filter(WalkaroundQuestion.id == question_id, WalkaroundQuestion.section_id == section_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.text = question.text
    q.question_type = question.question_type
    db.commit()
    db.refresh(q)
    return {"id": q.id, "text": q.text, "question_type": q.question_type}
'''
content = content + new_endpoints
open('app/routers/admin_walkarounds.py','w',encoding='utf-8').write(content)
print('Done:', len(content))
