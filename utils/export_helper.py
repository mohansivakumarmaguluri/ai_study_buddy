import re
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def markdown_to_html(text: str) -> str:
    """Converts simple markdown bold and italic formatting to HTML tags for ReportLab Paragraphs."""
    if not text:
        return ""
    # Escape XML entities
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold **text** -> <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Italic *text* -> <i>text</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Bullet marks at start of line
    text = re.sub(r"^-\s+(.*?)$", r"&bull; \1", text, flags=re.MULTILINE)
    # Newlines to line breaks
    text = text.replace("\n", "<br/>")
    return text

def export_to_txt(page: str, topic: str, content) -> str:
    """Converts session data to clean formatted text for download."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    text = f"===========================================\n"
    text += f"AI STUDY BUDDY - {page.upper()} SESSION\n"
    text += f"Topic: {topic}\n"
    text += f"Exported: {timestamp}\n"
    text += f"===========================================\n\n"
    
    if page == "explain":
        text += f"--- 1. SIMPLE EXPLANATION ---\n{content.get('simple_explanation', '')}\n\n"
        text += f"--- 2. TECHNICAL DETAILS ---\n{content.get('technical_details', '')}\n\n"
        text += "--- 3. KEY TAKEAWAYS ---\n"
        for i, item in enumerate(content.get('key_takeaways', []), 1):
            text += f"{i}. {item}\n"
        text += "\n--- 4. EXAM & INTERVIEW PREPARATION ---\n"
        for i, q in enumerate(content.get('exam_prep', []), 1):
            text += f"Q{i}: {q.get('question', '')}\n"
            text += f"A{i}: {q.get('answer', '')}\n\n"
            
    elif page == "summarize":
        text += f"--- 1. EXECUTIVE SUMMARY ---\n{content.get('summary', '')}\n\n"
        text += "--- 2. KEY CONCEPTS ---\n"
        for i, item in enumerate(content.get('key_concepts', []), 1):
            text += f"- {item}\n"
        text += f"\n--- 3. EXAM FOCUS ---\n{content.get('exam_focus', '')}\n\n"
        text += "--- 4. QUICK REVISION CHECKLIST ---\n"
        for item in content.get('revision_sheet', []):
            text += f"[ ] {item}\n"
            
    elif page == "quiz":
        for i, q in enumerate(content, 1):
            text += f"Question {i}: {q.get('question', '')}\n"
            for j, opt in enumerate(q.get('options', [])):
                letter_choice = chr(65 + j)
                text += f"  {letter_choice}) {opt}\n"
            correct_idx = q.get('correct_option_index', 0)
            correct_letter = chr(65 + correct_idx)
            correct_text = q.get('options', [])[correct_idx] if correct_idx < len(q.get('options', [])) else ""
            text += f"Correct Answer: {correct_letter} ({correct_text})\n"
            text += f"Explanation: {q.get('explanation', '')}\n\n"
            
    elif page == "flashcards":
        for i, card in enumerate(content, 1):
            text += f"Card {i}:\n"
            text += f"  FRONT: {card.get('front', '')}\n"
            text += f"  BACK:  {card.get('back', '')}\n\n"
            
    else:
        text += str(content)
        
    return text

def export_to_pdf(page: str, topic: str, content) -> bytes:
    """Generates a styled, educational PDF document using ReportLab and returns bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, 
        leftMargin=54, 
        topMargin=54, 
        bottomMargin=54
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom Palette
    primary_color = colors.HexColor("#1e3a8a")  # Deep Blue
    accent_color = colors.HexColor("#0f766e")   # Teal
    text_color = colors.HexColor("#1f2937")     # Dark Slate
    bg_light = colors.HexColor("#f8fafc")       # Off-White
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=accent_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=text_color,
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=text_color,
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=6
    )
    
    quiz_explanation_style = ParagraphStyle(
        'QuizExpl',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    story = []
    
    # Header Title Banner
    story.append(Paragraph(f"AI Study Buddy", title_style))
    story.append(Paragraph(f"Session: {page.capitalize()}  |  Topic: {topic}  |  Exported: {datetime.now().strftime('%Y-%m-%d')}", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=20))
    
    if page == "explain":
        story.append(Paragraph("1. Simple Explanation", h1_style))
        story.append(Paragraph(markdown_to_html(content.get('simple_explanation', '')), body_style))
        
        story.append(Paragraph("2. Technical Details", h1_style))
        story.append(Paragraph(markdown_to_html(content.get('technical_details', '')), body_style))
        
        story.append(Paragraph("3. Key Takeaways", h1_style))
        for item in content.get('key_takeaways', []):
            story.append(Paragraph(f"&bull; {markdown_to_html(item)}", bullet_style))
            
        story.append(Paragraph("4. Exam & Interview Preparation", h1_style))
        for i, q in enumerate(content.get('exam_prep', []), 1):
            story.append(Paragraph(f"<b>Q{i}: {markdown_to_html(q.get('question', ''))}</b>", body_style))
            story.append(Paragraph(f"<b>A:</b> {markdown_to_html(q.get('answer', ''))}", body_style))
            story.append(Spacer(1, 6))
            
    elif page == "summarize":
        story.append(Paragraph("1. Executive Summary", h1_style))
        story.append(Paragraph(markdown_to_html(content.get('summary', '')), body_style))
        
        story.append(Paragraph("2. Key Concepts & Terms", h1_style))
        for item in content.get('key_concepts', []):
            story.append(Paragraph(f"&bull; {markdown_to_html(item)}", bullet_style))
            
        story.append(Paragraph("3. Exam Focus Points", h1_style))
        story.append(Paragraph(markdown_to_html(content.get('exam_focus', '')), body_style))
        
        story.append(Paragraph("4. Quick Revision Sheet Checklist", h1_style))
        for item in content.get('revision_sheet', []):
            story.append(Paragraph(f"[  ] {markdown_to_html(item)}", bullet_style))
            
    elif page == "quiz":
        story.append(Paragraph("Study Quiz Questions & Explanations", h1_style))
        for i, q in enumerate(content, 1):
            story.append(Paragraph(f"<b>Q{i}. {markdown_to_html(q.get('question', ''))}</b>", body_style))
            for j, opt in enumerate(q.get('options', [])):
                letter_choice = chr(65 + j)
                story.append(Paragraph(f"&nbsp;&nbsp;{letter_choice}. {markdown_to_html(opt)}", bullet_style))
                
            correct_idx = q.get('correct_option_index', 0)
            correct_letter = chr(65 + correct_idx)
            correct_text = q.get('options', [])[correct_idx] if correct_idx < len(q.get('options', [])) else ""
            
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>Correct Answer: {correct_letter}</b> ({markdown_to_html(correct_text)})", body_style))
            story.append(Paragraph(f"<b>Explanation:</b> {markdown_to_html(q.get('explanation', ''))}", quiz_explanation_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=10, spaceAfter=15))
            
    elif page == "flashcards":
        story.append(Paragraph("Study Flashcards Deck", h1_style))
        story.append(Spacer(1, 10))
        
        table_data = [[
            Paragraph("<b>#</b>", body_style), 
            Paragraph("<b>Front (Question / Concept)</b>", body_style), 
            Paragraph("<b>Back (Answer / Definition)</b>", body_style)
        ]]
        
        for i, card in enumerate(content, 1):
            table_data.append([
                Paragraph(str(i), body_style),
                Paragraph(markdown_to_html(card.get('front', '')), body_style),
                Paragraph(markdown_to_html(card.get('back', '')), body_style)
            ])
            
        t = Table(table_data, colWidths=[30, 230, 240])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(t)
        
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
