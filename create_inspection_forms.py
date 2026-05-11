"""
Creates both SL Alabama inspection forms directly in the database.
Run: python create_inspection_forms.py
"""

from app.database import SessionLocal
from app.models import WalkaroundForm, WalkaroundSection, WalkaroundQuestion

db = SessionLocal()

# ─────────────────────────────────────────────
# FORM 1: SWPPP Field Inspection Checklist
# ─────────────────────────────────────────────

# Check if already exists
existing1 = db.query(WalkaroundForm).filter(WalkaroundForm.name == "SWPPP Field Inspection Checklist").first()
if existing1:
    print("SWPPP form already exists, skipping...")
else:
    form1 = WalkaroundForm(
        name="SWPPP Field Inspection Checklist",
        description="ESF-810-090 Rev.0 - SL Alabama, LLC. Pass/Fail inspection per Alabama NPDES requirements.",
        active=True
    )
    db.add(form1)
    db.flush()

    sections1 = [
        {
            "name": "Header Information",
            "questions": [
                ("Inspection Date", "text"),
                ("Inspector Name", "text"),
                ("Weather Conditions", "text"),
                ("Inspection Location", "text"),
                ("Permit No.", "text"),
            ]
        },
        {
            "name": "1. SWPPP Documentation",
            "questions": [
                ("Current SWPPP available on site", "pass_fail"),
                ("SWPPP reflects current construction activities", "pass_fail"),
                ("Material inventory list up to date", "pass_fail"),
                ("Spill Response Plan included", "pass_fail"),
                ("SDS available for hazardous materials", "pass_fail"),
            ]
        },
        {
            "name": "2. Drainage Areas & Outfalls",
            "questions": [
                ("Storm drains free of debris", "pass_fail"),
                ("Outfalls clearly identified", "pass_fail"),
                ("Evidence of discoloration, foam, sheen", "pass_fail"),
                ("Erosion at discharge points", "pass_fail"),
            ]
        },
        {
            "name": "3. Material Labeling",
            "questions": [
                ("All drums, tanks, totes, and containers labeled", "pass_fail"),
                ("Labels clearly identify material contents", "pass_fail"),
                ("Labels are legible and weather resistant", "pass_fail"),
                ("No unlabeled or mislabeled containers", "pass_fail"),
                ("Temporary/secondary containers labeled (if not for immediate use)", "pass_fail"),
                ("Labeled materials match those listed in the SWPPP", "pass_fail"),
            ]
        },
        {
            "name": "4. Hazard Identification (If Applicable)",
            "questions": [
                ("Hazard warnings present (flammable, corrosive, etc.)", "pass_fail"),
                ("OSHA/GHS labeling used where required", "pass_fail"),
                ("SDS matches labeled material", "pass_fail"),
                ("Incompatible materials stored separately", "pass_fail"),
            ]
        },
        {
            "name": "5. Material Storage & Stormwater Exposure",
            "questions": [
                ("Containers closed when not in use", "pass_fail"),
                ("Materials stored under cover or indoors as required", "pass_fail"),
                ("No leaks, stains, or deteriorated containers", "pass_fail"),
                ("Materials not stored in drainage paths or low areas", "pass_fail"),
                ("Storage locations match SWPPP site map", "pass_fail"),
            ]
        },
        {
            "name": "6. Secondary Containment",
            "questions": [
                ("Secondary containment provided where required", "pass_fail"),
                ("Containment in good condition and intact", "pass_fail"),
                ("No oil sheen, excessive debris, or contaminated stormwater", "pass_fail"),
                ("Containment capacity adequate", "pass_fail"),
                ("Containment clearly associated with stored materials", "pass_fail"),
            ]
        },
        {
            "name": "7. Designated Areas & Signage",
            "questions": [
                ("Fuel storage areas clearly marked", "pass_fail"),
                ("Concrete washout area properly labeled", "pass_fail"),
                ("Waste collection areas labeled", "pass_fail"),
                ("No unauthorized storage areas observed", "pass_fail"),
            ]
        },
        {
            "name": "8. Waste Management",
            "questions": [
                ("Waste containers labeled (e.g. 'Used Oil', 'Waste Paint')", "pass_fail"),
                ("Lids closed and containers not overfilled", "pass_fail"),
                ("Waste stored under cover", "pass_fail"),
                ("Waste removed at appropriate intervals", "pass_fail"),
            ]
        },
        {
            "name": "9. Spills & Leaks",
            "questions": [
                ("No active spills or leaks observed", "pass_fail"),
                ("Spill kits present and stocked", "pass_fail"),
                ("Any spills since last inspection?", "yes_no_na"),
                ("If yes, Spill Report completed?", "yes_no_na"),
                ("Location of spill (if applicable)", "text"),
                ("Past spills cleaned and documented", "pass_fail"),
            ]
        },
        {
            "name": "10. Site Personnel Awareness",
            "questions": [
                ("Employees aware of spill response procedures", "pass_fail"),
                ("Personnel know proper storage locations", "pass_fail"),
                ("SWPPP contact information known or posted", "pass_fail"),
                ("Site personnel can identify stored materials", "pass_fail"),
            ]
        },
        {
            "name": "11. Deficiencies & Corrective Actions",
            "questions": [
                ("No deficiencies noted", "pass_fail"),
                ("Deficiencies documented (see notes below)", "pass_fail"),
                ("Corrective actions assigned", "pass_fail"),
                ("Timeline established for completion", "pass_fail"),
            ]
        },
        {
            "name": "12. Inspector Notes / Corrective Actions Required",
            "questions": [
                ("Inspector notes and corrective actions", "text"),
                ("Inspector Signature", "text"),
            ]
        },
    ]

    for sec_idx, sec in enumerate(sections1):
        section = WalkaroundSection(
            form_id=form1.id,
            name=sec["name"],
            order=sec_idx,
            active=True
        )
        db.add(section)
        db.flush()

        for q_idx, (q_text, q_type) in enumerate(sec["questions"]):
            question = WalkaroundQuestion(
                section_id=section.id,
                text=q_text,
                question_type=q_type,
                order=q_idx,
                active=True
            )
            db.add(question)

    print(f"✓ SWPPP Field Inspection Checklist created with {len(sections1)} sections")

# ─────────────────────────────────────────────
# FORM 2: Industrial Stormwater Inspection Form
# ─────────────────────────────────────────────

existing2 = db.query(WalkaroundForm).filter(WalkaroundForm.name == "Industrial Stormwater Inspection Form").first()
if existing2:
    print("Stormwater form already exists, skipping...")
else:
    form2 = WalkaroundForm(
        name="Industrial Stormwater Inspection Form",
        description="ESF-810-091 Rev.0 - SL Alabama, LLC. Yes/No/NA inspection per Alabama NPDES requirements.",
        active=True
    )
    db.add(form2)
    db.flush()

    sections2 = [
        {
            "name": "Facility & Inspection Information",
            "questions": [
                ("Inspector Name & Title", "text"),
                ("Inspection Type (Quarterly / Corrective / Follow-Up)", "text"),
                ("Date of Inspection", "text"),
                ("Time of Inspection", "text"),
                ("Weather Conditions (Dry / Raining / Within 72 hrs of rainfall)", "text"),
                ("Rainfall Amount (if known, in inches)", "text"),
            ]
        },
        {
            "name": "1. Drainage Areas & Outfalls",
            "questions": [
                ("Storm drains free of debris", "yes_no_na"),
                ("Outfalls clearly identified", "yes_no_na"),
                ("Evidence of discoloration, foam, sheen", "yes_no_na"),
                ("Erosion at discharge points", "yes_no_na"),
            ]
        },
        {
            "name": "2. Material Handling & Storage",
            "questions": [
                ("Materials stored under cover", "yes_no_na"),
                ("Containers properly labeled", "yes_no_na"),
                ("Secondary containment intact", "yes_no_na"),
                ("No leaks observed", "yes_no_na"),
            ]
        },
        {
            "name": "3. Good Housekeeping",
            "questions": [
                ("Work areas clean", "yes_no_na"),
                ("Dumpsters closed & covered", "yes_no_na"),
                ("Spill kits available & stocked", "yes_no_na"),
                ("No leaks observed", "yes_no_na"),
            ]
        },
        {
            "name": "4. Spill & Leak Review",
            "questions": [
                ("Any spills since last inspection?", "yes_no_na"),
                ("If yes, Spill Report completed?", "yes_no_na"),
                ("Location(s) of spill (if applicable)", "text"),
            ]
        },
        {
            "name": "5. Corrective Actions",
            "questions": [
                ("Issue Identified", "text"),
                ("Action Required", "text"),
                ("Responsible Person", "text"),
                ("Completion Date", "text"),
            ]
        },
        {
            "name": "Inspector Certification",
            "questions": [
                ("I certify this inspection was conducted in accordance with the facility SWPPP and Alabama NPDES requirements.", "yes_no_na"),
                ("Inspector Signature", "text"),
                ("Date", "text"),
            ]
        },
    ]

    for sec_idx, sec in enumerate(sections2):
        section = WalkaroundSection(
            form_id=form2.id,
            name=sec["name"],
            order=sec_idx,
            active=True
        )
        db.add(section)
        db.flush()

        for q_idx, (q_text, q_type) in enumerate(sec["questions"]):
            question = WalkaroundQuestion(
                section_id=section.id,
                text=q_text,
                question_type=q_type,
                order=q_idx,
                active=True
            )
            db.add(question)

    print(f"✓ Industrial Stormwater Inspection Form created with {len(sections2)} sections")

db.commit()
db.close()
print("\n✓ All forms created successfully!")
print("View them at: http://localhost:8000/admin/walkarounds")
