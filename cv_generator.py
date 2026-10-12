import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_cv(profile, email, pdf_filename):
    doc = SimpleDocTemplate(
        pdf_filename, 
        pagesize=letter, 
        rightMargin=40, 
        leftMargin=40, 
        topMargin=40, 
        bottomMargin=40
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Преміальна типографіка
    title_style = ParagraphStyle(
        'CVTitle', parent=styles['Heading1'], 
        fontSize=22, leading=26, textColor=colors.HexColor("#0f172a"), spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'CVSubtitle', parent=styles['Normal'], 
        fontSize=11, leading=16, textColor=colors.HexColor("#2563eb"), spaceAfter=6
    )
    meta_style = ParagraphStyle(
        'CVMeta', parent=styles['Normal'], 
        fontSize=9.5, leading=14, textColor=colors.HexColor("#475569"), spaceAfter=6
    )
    heading_style = ParagraphStyle(
        'CVHeading', parent=styles['Heading2'], 
        fontSize=12, leading=15, spaceBefore=10, spaceAfter=4, 
        textColor=colors.HexColor("#1e293b"), keepWithNext=True
    )
    body_style = ParagraphStyle(
        'CVBody', parent=styles['Normal'], 
        fontSize=9.5, leading=14, textColor=colors.HexColor("#0f172a"), spaceAfter=6
    )

    # 1. Шапка: ПІБ та Цільова посада (напр. FTTH / Telecom Specialist)
    name = profile.get("name", "")
    if name:
        story.append(Paragraph(name, title_style))
    
    titles = profile.get("job_titles", "")
    if titles:
        story.append(Paragraph(f"<b>Target Role:</b> {titles}", subtitle_style))
        
    # Блок контактів
    contacts = []
    phone = profile.get("phone", "")
    if phone:
        contacts.append(f"<b>Tel:</b> {phone}")
    if email:
        contacts.append(f"<b>Email:</b> {email}")
    address = profile.get("address", "")
    if address:
        contacts.append(f"<b>Location:</b> {address}")
        
    if contacts:
        story.append(Paragraph(" | ".join(contacts), meta_style))
        
    # Логістика, мови та мобільність
    logistics = []
    locs = profile.get("locations", "")
    if locs:
        logistics.append(f"<b>Availability/Regions:</b> {locs}")
    langs = profile.get("languages", "")
    if langs:
        logistics.append(f"<b>Languages:</b> {langs}")
        
    if logistics:
        story.append(Paragraph(" | ".join(logistics), meta_style))
        
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3b82f6"), spaceAfter=10))

    # 2. Професійний профіль (Summary)
    profile_summary = profile.get("professional_profile", "")
    if profile_summary:
        story.append(Paragraph("Professional Summary", heading_style))
        story.append(Paragraph(profile_summary.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 2))

    # 3. Досвід роботи (Telecom / Technical Experience)
    exp = profile.get("experience", "")
    if exp:
        story.append(Paragraph("Professional Experience", heading_style))
        story.append(Paragraph(exp.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 2))

    # 4. Освіта
    edu = profile.get("education", "")
    if edu:
        story.append(Paragraph("Education", heading_style))
        story.append(Paragraph(edu.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 2))

    # 5. Сертифікати та ліцензії (важливо для підрядів та телекому)
    certs = profile.get("certifications", "")
    if certs:
        story.append(Paragraph("Certifications & Technical Licenses", heading_style))
        story.append(Paragraph(certs.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 2))

    # 6. Дозвіл, обладнання та інші дані (Other Data / Driving license / Work Permit)
    other = profile.get("other_data", "")
    if other:
        story.append(Paragraph("Authorization, Driving & Logistics", heading_style))
        story.append(Paragraph(other.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 2))

    # 7. Додаткова інформація
    add_info = profile.get("additional_info", "")
    if add_info:
        story.append(Paragraph("Additional Skills & Tools", heading_style))
        story.append(Paragraph(add_info.replace("\n", "<br/>"), body_style))

    doc.build(story)
