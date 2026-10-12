# 1. Шапка: ПІБ та Цільова посада (напр. FTTH / Telecom Specialist)
    name = profile.get("name", "")
    if name:
        story.append(Paragraph(name, title_style))
    
    titles = profile.get("job_titles", "")
    if titles:
        story.append(Paragraph(f"<b>Target Role:</b> {titles}", subtitle_style))
        
    # Блок контактів (Телефон, Email, LinkedIn, посилання)
    contacts = []
    phone = profile.get("phone", "")
    if phone:
        contacts.append(f"<b>Tel:</b> {phone}")
    if email:
        contacts.append(f"<b>Email:</b> {email}")
        
    # Додаємо посилання (LinkedIn, GitHub, портфоліо тощо)
    linkedin = profile.get("linkedin", "")
    if linkedin:
        contacts.append(f"<b>LinkedIn:</b> {linkedin}")
        
    website = profile.get("website", "")
    if website:
        contacts.append(f"<b>Web:</b> {website}")
        
    address = profile.get("address", "")
    if address:
        contacts.append(f"<b>Location:</b> {address}")
        
    if contacts:
        story.append(Paragraph(" | ".join(contacts), meta_style))
