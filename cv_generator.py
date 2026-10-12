import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
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
    
    # Стилі
    title_style = ParagraphStyle(
        'CVTitle', parent=styles['Heading1'], 
        fontSize=20, leading=24, textColor=colors.HexColor("#0f172a"), spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'CVSubtitle', parent=styles['Normal'], 
        fontSize=11, leading=15, textColor=colors.HexColor("#334155"), spaceAfter=6
    )
    meta_style = ParagraphStyle(
        'CVMeta', parent=styles['Normal'], 
        fontSize=9.5, leading=13, textColor=colors.HexColor("#475569"), spaceAfter=10
    )
    heading_style = ParagraphStyle(
        'CVHeading', parent=styles['Heading2'], 
        fontSize=13, leading=16, spaceBefore=10, spaceAfter=4, 
        textColor=colors.HexColor("#1e293b"), keepWithNext=True
    )
    body_style = ParagraphStyle(
        'CVBody', parent=styles['Normal'], 
        fontSize=10, leading=14.5, textColor=colors.HexColor("#0f172a"), spaceAfter=6
    )

    # 1. Шапка: Ім'я, Посади, Контакти
    story.append(Paragraph(profile.get("name", "Candidate CV"), title_style))
    
    titles = profile.get("job_titles", "")
    if titles:
        story.append(Paragraph(f"<b>Target Roles:</b> {titles}", subtitle_style))
        
    # Контакти (Телефон, Email, Адреса)
    contacts = []
    phone = profile.get("phone", "")
    if phone:
        contacts.append(f"<b>Phone:</b> {phone}")
    if email:
        contacts.append(f"<b>Email:</b> {email}")
    address = profile.get("address", "")
    if address:
        contacts.append(f"<b>Address:</b> {address}")
        
    if contacts:
        story.append(Paragraph(" | ".join(contacts), meta_style))
        
    # Логістика / Доступність / Мови (Другий рядок шапки)
    logistics = []
    locs = profile.get("locations", "")
    if locs:
        logistics.append(f"<b>Locations/Remote:</b> {locs}")
    permit = profile.get("work_permit", "")
    if permit:
        logistics.append(f"<b>Work Auth:</b> {permit}")
    langs = profile.get("languages", "")
    if langs:
        logistics.append(f"<b>Languages:</b> {langs}")
        
    if logistics:
        story.append(Paragraph(" | ".join(logistics), meta_style))
        
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # 2. Професійний профіль (Summary)
    profile_summary = profile.get("professional_profile", "")
    if profile_summary:
        story.append(Paragraph("Professional Profile", heading_style))
        story.append(Paragraph(profile_summary.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 4))

    # 3. Досвід роботи
    exp = profile.get("experience", "")
    if exp:
        story.append(Paragraph("Professional Experience", heading_style))
        story.append(Paragraph(exp.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 4))

    # 4. Освіта
    edu = profile.get("education", "")
    if edu:
        story.append(Paragraph("Education", heading_style))
        story.append(Paragraph(edu.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 4))

    # 5. Сертифікати та ліцензії
    certs = profile.get("certifications", "")
    if certs:
        story.append(Paragraph("Certifications & Licenses", heading_style))
        story.append(Paragraph(certs.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 4))

    # 6. Інші дані (Права, авто, переїзд тощо)
    other = profile.get("other_data", "")
    if other:
        story.append(Paragraph("Other Data & Availability", heading_style))
        story.append(Paragraph(other.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 4))

    # 7. Додаткова інформація
    add_info = profile.get("additional_info", "")
    if add_info:
        story.append(Paragraph("Additional Information", heading_style))
        story.append(Paragraph(add_info.replace("\n", "<br/>"), body_style))

    doc.build(story)
