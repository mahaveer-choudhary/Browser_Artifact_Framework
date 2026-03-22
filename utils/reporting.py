from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import json
import datetime

def format_cell_text(s, max_chars=22):
    """Injects <br/> tags into long unbroken strings (emails, URLs) to force wrapping inside tables."""
    if not s: return ""
    s = str(s)
    # If contains spaces and not excessively long, standard Paragraph might fit
    if ' ' in s and len(s) < 40: return s
    
    parts = []
    curr = ""
    for char in s:
        curr += char
        # Break rule triggers
        if len(curr) >= max_chars or char in ['@'] or (char in ['/', '.', '?', '&', '='] and len(curr) > 10):
            parts.append(curr)
            parts.append('<br/>')
            curr = ""
    if curr: parts.append(curr)
    
    # Clean trailing breaks
    res = "".join(parts)
    if res.endswith('<br/>'): res = res[:-5]
    return res

def generate_pdf_report(full_data, system_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter, title="BAF Forensic Report", author="BAF")
    styles = getSampleStyleSheet()
    story = []

    # Custom Style
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.teal,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.blue,
        spaceBefore=10,
        spaceAfter=6
    )

    # Title
    story.append(Paragraph("Browser Artifact Framework (BAF) - Forensic Report", title_style))
    story.append(Paragraph(f"Generated On: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # 1. System OS Summary
    story.append(Paragraph("1. System OS Artifacts", header_style))
    
    # Wi-Fi
    story.append(Paragraph("Wi-Fi Profiles", styles['Heading3']))
    wifi_data = [["SSID", "Password"]]
    for w in system_data.get('wifi_profiles', []):
        wifi_data.append([
            Paragraph(str(w.get('ssid', '')), styles['Normal']), 
            Paragraph(str(w.get('password', '')), styles['Normal'])
        ])
    
    if len(wifi_data) > 1:
        t = Table(wifi_data, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No Wi-Fi profiles found.", styles['Normal']))
    
    story.append(Spacer(1, 12))

    # Anti-Forensics
    story.append(Paragraph("Anti-Forensics & Privacy Tools Detection", styles['Heading3']))
    af_data = [["Category", "Tool/Config", "Path"]]
    for a in system_data.get('anti_forensics', []):
        af_data.append([
            Paragraph(str(a.get('category', '')), styles['Normal']), 
            Paragraph(str(a.get('name', '')), styles['Normal']), 
            Paragraph(str(a.get('path', '')), styles['Normal'])
        ])
        
    if len(af_data) > 1:
        t = Table(af_data, colWidths=[120, 140, 240])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No Anti-Forensics tools or configurations detected.", styles['Normal']))

    story.append(Spacer(1, 12))

    # USB History
    story.append(Paragraph("USB Device History", styles['Heading3']))
    usb_data = [["Device Name", "Class/ID", "Serial Number"]]
    for u in system_data.get('usb_history', []):
        usb_data.append([
            Paragraph(format_cell_text(u.get('name', ''), 28), styles['Normal']), 
            Paragraph(format_cell_text(u.get('class', ''), 22), styles['Normal']), 
            Paragraph(format_cell_text(u.get('serial_number', ''), 30), styles['Normal'])
        ])
        
    if len(usb_data) > 1:
        t = Table(usb_data, colWidths=[180, 160, 160])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No USB device history found.", styles['Normal']))

    story.append(Spacer(1, 20))

    # 2. Browser Data
    story.append(Paragraph("2. Browser Artifacts", header_style))

    for db_name, b_data in full_data.items():
        if not b_data: continue
        story.append(Paragraph(f"Browser: {db_name.upper()}", styles['Heading3']))
        
        logins = b_data.get('logins', [])
        cookies = b_data.get('cookies', [])
        history = b_data.get('history', [])
        
        story.append(Paragraph(f"Extracted: {len(logins)} Logins, {len(cookies)} Cookies, {len(history)} History Items", styles['Normal']))
        story.append(Spacer(1, 6))

        if logins:
            story.append(Paragraph("Top 5 Logins (Sample)", styles['Heading4']))
            login_table = [["URL / Location", "User", "Password"]]
            for l in logins[:10]:
                u_val = str(l.get('origin') or l.get('action_url') or l.get('hostname') or 'N/A')
                login_table.append([
                    Paragraph(format_cell_text(u_val, 25), styles['Normal']),
                    Paragraph(format_cell_text(l.get('username', ''), 20), styles['Normal']),
                    Paragraph(format_cell_text(l.get('password', ''), 18), styles['Normal'])
                ])
            t = Table(login_table, colWidths=[200, 150, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), 
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

        if history:
             story.append(Paragraph("Top 5 Visited History (Sample)", styles['Heading4']))
             hist_table = [["Title", "URL"]]
             for h in history[:10]:
                 hist_table.append([
                     Paragraph(format_cell_text(h.get('title', 'No Title'), 25), styles['Normal']), 
                     Paragraph(format_cell_text(h.get('url', ''), 40), styles['Normal'])
                 ])
             t = Table(hist_table, colWidths=[180, 320])
             t.setStyle(TableStyle([
                 ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), 
                 ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
             ]))
             story.append(t)
             story.append(Spacer(1, 10))

        # Extensions
        extensions = b_data.get('intelligence', {}).get('extensions', [])
        if extensions:
            story.append(Paragraph("Installed Extensions (Sample)", styles['Heading4']))
            ext_table = [["Name", "Version", "Suspicious"]]
            for e in extensions[:10]:
                is_sus = "Yes" if e.get('suspicious') else "No"
                ext_table.append([
                    Paragraph(format_cell_text(e.get('name', 'Unknown'), 30), styles['Normal']), 
                    Paragraph(format_cell_text(e.get('version', 'N/A'), 12), styles['Normal']), 
                    Paragraph(is_sus, styles['Normal'])
                ])
            t = Table(ext_table, colWidths=[240, 100, 100])
            t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
            story.append(t)
            story.append(Spacer(1, 10))
            
        # IOCs
        iocs = b_data.get('intelligence', {}).get('iocs', [])
        if iocs:
            story.append(Paragraph("Threat Intel Matches (IOCs)", styles['Heading4']))
            ioc_table = [["Threat", "URL"]]
            for i in iocs[:5]:
                ioc_table.append([
                    Paragraph(format_cell_text(i.get('threat', 'Threat'), 20), styles['Normal']), 
                    Paragraph(format_cell_text(i.get('url', ''), 45), styles['Normal'])
                ])
            t = Table(ioc_table, colWidths=[150, 350])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), 
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey), 
                ('TEXTCOLOR', (0,1), (0,-1), colors.red)
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

    doc.build(story)
    return output_path
