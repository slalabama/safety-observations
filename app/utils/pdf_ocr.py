import pdfplumber
from typing import List, Dict

def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract text from PDF and structure it into sections with questions.
    
    Strategy:
    - Large font text → section headers
    - Bullet points / numbered items → questions
    - Checkboxes/lines → question types (pass/fail, yes/no)
    
    Returns list of sections with questions for admin review.
    """
    sections = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                lines = text.split('\n')
                
                current_section = None
                
                for line in lines:
                    stripped = line.strip()
                    
                    if not stripped:
                        continue
                    
                    # Heuristic: all-caps or short text → section header
                    if stripped.isupper() and len(stripped) > 3:
                        if current_section:
                            sections.append(current_section)
                        
                        current_section = {
                            "name": stripped,
                            "order": len(sections),
                            "questions": []
                        }
                    
                    # Heuristic: lines with checkboxes or bullets → questions
                    elif current_section and (
                        "□" in stripped or "☐" in stripped or 
                        stripped.startswith("•") or 
                        stripped.startswith("-") or
                        stripped[0].isdigit() or
                        "?" in stripped
                    ):
                        # Clean the line
                        question_text = stripped.replace("□", "").replace("☐", "").replace("•", "").replace("-", "").strip()
                        
                        # Remove leading numbers (1., 2., etc.)
                        if question_text and question_text[0].isdigit():
                            question_text = question_text.split(".", 1)[-1].strip()
                        
                        if question_text:
                            current_section["questions"].append({
                                "text": question_text,
                                "question_type": "pass_fail",
                                "order": len(current_section["questions"])
                            })
                
                # Add last section
                if current_section:
                    sections.append(current_section)
        
        return sections if sections else [
            {
                "name": "General",
                "order": 0,
                "questions": [{"text": "Sample question - please edit", "question_type": "pass_fail", "order": 0}]
            }
        ]
    
    except Exception as e:
        # Fallback: return generic structure for admin to fill
        return [
            {
                "name": "Section 1",
                "order": 0,
                "questions": [
                    {
                        "text": f"Error extracting PDF: {str(e)}. Please manually add questions.",
                        "question_type": "text",
                        "order": 0
                    }
                ]
            }
        ]