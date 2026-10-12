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
    
    # Кастомні стилі для професійного оформлення CV
    title_style = ParagraphStyle(
        'CVTitle', parent=styles['Heading1'], 
        fontSize=22, leading=26, textColor=colors.HexColor("#0f172a"), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'CVSubtitle', parent=styles['Normal'], 
        fontSize=12, leading=16, textColor=colors.HexColor("#334155"), spaceAfter=10
    )
    meta_style = ParagraphStyle(
        'CVMeta', parent=styles['Normal'], 
        fontSize=10, leading=14, textColor=colors.HexColor("#64748b"), spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'CVHeading', parent=styles['Heading2'], 
        fontSize=14, leading=18, spaceBefore=12, spaceAfter=6, 
        textColor=colors.HexColor("#1e293b"), keepWithNext=True
    )
    body_style = ParagraphStyle(
        'CVBody', parent=styles['Normal'], 
        fontSize=10.5, leading=15, textColor=colors.HexColor("#0f172a"), spaceAfter=8
    )

    # 1. Шапка резюме (Ім'я та контакти)
    story.append(Paragraph(profile.get("name", "Candidate CV"), title_style))
    
    # Бажані посади
    titles = profile.get("job_titles", "")
    if titles:
        story.append(Paragraph(f"<b>Target Roles:</b> {titles}", subtitle_style))
        
    # Контакти та мета-інформація
    meta_lines = []
    if email:
        meta_lines.append(f"<b>Email:</b> {email}")
    permit = profile.get("work_permit", "")
    if permit:
        meta_lines.append(f"<b>Work Auth / Visa:</b> {permit}")
    locs = profile.get("locations", "")
    if locs:
        meta_lines.append(f"<b>Locations:</b> {locs}")
    langs = profile.get("languages", "")
    if langs:
        meta_lines.append(f"<b>Languages:</b> {langs}")
        
    story.append(Paragraph(" | ".join(meta_lines), meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

    # 2. Досвід роботи
    exp = profile.get("experience", "")
    if exp:
        story.append(Paragraph("Professional Experience", heading_style))
        story.append(Paragraph(exp.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 6))

    # 3. Освіта
    edu = profile.get("education", "")
    if edu:
        story.append(Paragraph("Education", heading_style))
        story.append(Paragraph(edu.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 6))

    # 4. Сертифікати та ліцензії
    certs = profile.get("certifications", "")
    if certs:
        story.append(Paragraph("Certifications & Licenses", heading_style))
        story.append(Paragraph(certs.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 6))

    # 5. Додаткова інформація
    add_info = profile.get("additional_info", "")
    if add_info:
        story.append(Paragraph("Additional Information", heading_style))
        story.append(Paragraph(add_info.replace("\n", "<br/>"), body_style))

    doc.build(story)
