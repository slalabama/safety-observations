from fastapi import APIRouter
from app.database import SessionLocal, Base, engine
from app.models import Employee, Facility, WalkaroundForm, WalkaroundSection, WalkaroundQuestion

router = APIRouter()

@router.get("/setup")
def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Facility
    if not db.query(Facility).first():
        db.add(Facility(name="Main Facility", latitude=32.9321, longitude=-85.9618, radius_miles=2.0))
        db.flush()

    # Admin users - idempotent (create if missing, update email if already exists)
    try:
        charles = db.query(Employee).filter(Employee.name == "Charles Burks").first()
        if not charles:
            charles = Employee(badge="00854", name="Charles Burks", department="HR", role="admin", email="charles@slalabama.com", status="active", pin="1234")
            db.add(charles)
        else:
            charles.email = "charles@slalabama.com"
            charles.status = "active"

        stephanie = db.query(Employee).filter(Employee.name == "Stephanie Jennings").first()
        if not stephanie:
            stephanie = Employee(badge="48457", name="Stephanie Jennings", department="HR", role="admin", email="stephanie@slalabama.com", status="active", pin="5678")
            db.add(stephanie)
        else:
            stephanie.email = "stephanie@slalabama.com"
            stephanie.status = "active"

        db.flush()

        # SWPPP Form
        if not db.query(WalkaroundForm).filter(WalkaroundForm.name == "SWPPP Field Inspection Checklist").first():
            form1 = WalkaroundForm(name="SWPPP Field Inspection Checklist", description="ESF-810-090 Rev.0 - SL Alabama, LLC. Pass/Fail inspection per Alabama NPDES requirements.", active=True)
            db.add(form1)
            db.flush()
            sections1 = [
                ("Header Information", [("Inspection Date","text"),("Inspector Name","text"),("Weather Conditions","text"),("Inspection Location","text"),("Permit No.","text")]),
                ("1. SWPPP Documentation", [("Current SWPPP available on site","pass_fail"),("SWPPP reflects current construction activities","pass_fail"),("Material inventory list up to date","pass_fail"),("Spill Response Plan included","pass_fail"),("SDS available for hazardous materials","pass_fail")]),
                ("2. Drainage Areas & Outfalls", [("Storm drains free of debris","pass_fail"),("Outfalls clearly identified","pass_fail"),("Evidence of discoloration, foam, sheen","pass_fail"),("Erosion at discharge points","pass_fail")]),
                ("3. Material Labeling", [("All drums, tanks, totes, and containers labeled","pass_fail"),("Labels clearly identify material contents","pass_fail"),("Labels are legible and weather resistant","pass_fail"),("No unlabeled or mislabeled containers","pass_fail"),("Temporary/secondary containers labeled","pass_fail"),("Labeled materials match those listed in the SWPPP","pass_fail")]),
                ("4. Hazard Identification", [("Hazard warnings present (flammable, corrosive, etc.)","pass_fail"),("OSHA/GHS labeling used where required","pass_fail"),("SDS matches labeled material","pass_fail"),("Incompatible materials stored separately","pass_fail")]),
                ("5. Material Storage & Stormwater Exposure", [("Containers closed when not in use","pass_fail"),("Materials stored under cover or indoors as required","pass_fail"),("No leaks, stains, or deteriorated containers","pass_fail"),("Materials not stored in drainage paths or low areas","pass_fail"),("Storage locations match SWPPP site map","pass_fail")]),
                ("6. Secondary Containment", [("Secondary containment provided where required","pass_fail"),("Containment in good condition and intact","pass_fail"),("No oil sheen, excessive debris, or contaminated stormwater","pass_fail"),("Containment capacity adequate","pass_fail"),("Containment clearly associated with stored materials","pass_fail")]),
                ("7. Designated Areas & Signage", [("Fuel storage areas clearly marked","pass_fail"),("Concrete washout area properly labeled","pass_fail"),("Waste collection areas labeled","pass_fail"),("No unauthorized storage areas observed","pass_fail")]),
                ("8. Waste Management", [("Waste containers labeled","pass_fail"),("Lids closed and containers not overfilled","pass_fail"),("Waste stored under cover","pass_fail"),("Waste removed at appropriate intervals","pass_fail")]),
                ("9. Spills & Leaks", [("No active spills or leaks observed","pass_fail"),("Spill kits present and stocked","pass_fail"),("Any spills since last inspection?","yes_no_na"),("If yes, Spill Report completed?","yes_no_na"),("Location of spill (if applicable)","text"),("Past spills cleaned and documented","pass_fail")]),
                ("10. Site Personnel Awareness", [("Employees aware of spill response procedures","pass_fail"),("Personnel know proper storage locations","pass_fail"),("SWPPP contact information known or posted","pass_fail"),("Site personnel can identify stored materials","pass_fail")]),
                ("11. Deficiencies & Corrective Actions", [("No deficiencies noted","pass_fail"),("Deficiencies documented","pass_fail"),("Corrective actions assigned","pass_fail"),("Timeline established for completion","pass_fail")]),
                ("12. Inspector Notes", [("Inspector notes and corrective actions","text"),("Inspector Signature","text")]),
            ]
            for sec_idx, (sname, questions) in enumerate(sections1):
                sec = WalkaroundSection(form_id=form1.id, name=sname, order=sec_idx, active=True)
                db.add(sec)
                db.flush()
                for q_idx, (qtext, qtype) in enumerate(questions):
                    db.add(WalkaroundQuestion(section_id=sec.id, text=qtext, question_type=qtype, order=q_idx, active=True))

        # Industrial Stormwater Form
        if not db.query(WalkaroundForm).filter(WalkaroundForm.name == "Industrial Stormwater Inspection Form").first():
            form2 = WalkaroundForm(name="Industrial Stormwater Inspection Form", description="ESF-810-091 Rev.0 - SL Alabama, LLC. Yes/No/NA inspection per Alabama NPDES requirements.", active=True)
            db.add(form2)
            db.flush()
            sections2 = [
                ("Facility & Inspection Information", [("Inspector Name & Title","text"),("Inspection Type (Quarterly/Corrective/Follow-Up)","text"),("Date of Inspection","text"),("Time of Inspection","text"),("Weather Conditions","text"),("Rainfall Amount (inches)","text")]),
                ("1. Drainage Areas & Outfalls", [("Storm drains free of debris","yes_no_na"),("Outfalls clearly identified","yes_no_na"),("Evidence of discoloration, foam, sheen","yes_no_na"),("Erosion at discharge points","yes_no_na")]),
                ("2. Material Handling & Storage", [("Materials stored under cover","yes_no_na"),("Containers properly labeled","yes_no_na"),("Secondary containment intact","yes_no_na"),("No leaks observed","yes_no_na")]),
                ("3. Good Housekeeping", [("Work areas clean","yes_no_na"),("Dumpsters closed & covered","yes_no_na"),("Spill kits available & stocked","yes_no_na"),("No leaks observed","yes_no_na")]),
                ("4. Spill & Leak Review", [("Any spills since last inspection?","yes_no_na"),("If yes, Spill Report completed?","yes_no_na"),("Location of spill (if applicable)","text")]),
                ("5. Corrective Actions", [("Issue Identified","text"),("Action Required","text"),("Responsible Person","text"),("Completion Date","text")]),
                ("Inspector Certification", [("I certify this inspection was conducted per SWPPP and Alabama NPDES requirements","yes_no_na"),("Inspector Signature","text"),("Date","text")]),
            ]
            for sec_idx, (sname, questions) in enumerate(sections2):
                sec = WalkaroundSection(form_id=form2.id, name=sname, order=sec_idx, active=True)
                db.add(sec)
                db.flush()
                for q_idx, (qtext, qtype) in enumerate(questions):
                    db.add(WalkaroundQuestion(section_id=sec.id, text=qtext, question_type=qtype, order=q_idx, active=True))

        db.commit()
        return {"status": "Setup complete! Login with First Name + Last Name (admin: Charles Burks)"}
    except Exception as e:
        db.rollback()
        return {"status": "Error during setup", "error": str(e)}
    finally:
        db.close()


@router.get("/debug/employees")
def debug_employees():
    """Public endpoint to list employee names for debugging. Remove later."""
    from app.database import SessionLocal
    from app.models import Employee
    db = SessionLocal()
    try:
        employees = db.query(Employee).all()
        return [{"id": e.id, "name": repr(e.name), "role": e.role} for e in employees]
    finally:
        db.close()


