"""Offline executive PDF with readable typography and automatic pagination.

Content flows across pages: no shrinking text into fixed cards, cutting
sentences, screenshots, credentials, cloud requests, or data mutations.
"""
from __future__ import annotations
from io import BytesIO
from html import escape
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether, Flowable,
)
from src.dashboard_presentation import severity
from src.interview_demo import is_synthetic
from src.executive_report import (
    alert_reason, decision, hypotheses, kpi_definitions, recommended_checks,
    report_window, executive_headline, suggested_owner_role,
)
from src.financial_evidence import reporting_financial_evidence

INK = colors.HexColor('#111827')
MUTED = colors.HexColor('#5B6472')
LINE = colors.HexColor('#E3E6EB')
BLUE = colors.HexColor('#1D4FBF')
AMBER = colors.HexColor('#B54708')
PALE = colors.HexColor('#F4F5F7')


def plain(value) -> str:
    """Standard PDF fonts: normalize unsupported glyphs without losing text."""
    text = str(value or '')
    for before, after in {'\u2011':'-', '\u2013':'-', '\u2014':' - ', '\u2212':'-',
                          '\u2265':'>=', '\u2264':'<=', '\u2026':'...', '\u2192':'->'}.items():
        text = text.replace(before, after)
    return text


def para(value, style):
    return Paragraph(escape(plain(value)).replace('\n', '<br/>'), style)


class PaginatedCanvas(canvas.Canvas):
    """Add true page x / total after content has finished flowing."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for page in self._pages:
            self.__dict__.update(page)
            self.setStrokeColor(LINE)
            self.line(38, 36, A4[0]-38, 36)
            self.setFillColor(MUTED)
            self.setFont('Helvetica', 7)
            self.drawString(38, 23, 'Historical GA4 case study | AI findings require factual review')
            self.drawRightString(A4[0]-38, 23, f'Page {self._pageNumber} / {total}')
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


class EvidenceChart(Flowable):
    """Sharp vector chart, labelled axes and exact input values in the table."""
    def __init__(self, rows, selected, field='sessions', width=A4[0]-76, height=120):
        super().__init__()
        self.width, self.height = width, height
        self.rows = rows
        self.selected = selected
        self.field = field

    def draw(self):
        c = self.canv
        if not self.rows:
            return
        rate = self.field == 'rate'
        obs, baseline = ('observed_purchase_rate_pct', 'baseline_purchase_rate_pct') if rate else ('observed_sessions', 'baseline_sessions')
        left, right, bottom, top = 43, self.width-22, 25, self.height-20
        values = [float(r[k]) for r in self.rows for k in (obs, baseline)]
        hi = max(values) * 1.13 or 1
        def x(i): return (left+right)/2 if len(self.rows) == 1 else left+(right-left)*i/(len(self.rows)-1)
        def y(value): return bottom+(top-bottom)*value/hi
        c.setFont('Helvetica', 6.8)
        for fraction in (0, .25, .5, .75, 1):
            at = y(fraction*hi)
            c.setStrokeColor(LINE)
            c.setLineWidth(.5)
            c.line(left, at, right, at)
            c.setFillColor(MUTED)
            label = f'{fraction*hi:.1f}%' if rate else f'{fraction*hi:,.0f}'
            c.drawRightString(left-7, at-2, label)
        for key, hue in ((baseline, colors.HexColor('#8A94A6')), (obs, BLUE)):
            c.setStrokeColor(hue)
            c.setLineWidth(1.6 if key == obs else 1)
            c.setDash([] if key == obs else [4, 3])
            for i in range(len(self.rows)-1):
                c.line(x(i), y(float(self.rows[i][key])), x(i+1), y(float(self.rows[i+1][key])))
        c.setDash([])
        for i, row in enumerate(self.rows):
            if row['investigation_date'] == self.selected['investigation_date']:
                c.setFillColor(AMBER)
                c.circle(x(i), y(float(row[obs])), 3.2, fill=1, stroke=0)
            if len(self.rows) <= 10 or i in (0, len(self.rows)-1):
                c.setFillColor(MUTED)
                c.drawCentredString(x(i), 10, row['investigation_date'][5:])
        c.setFillColor(BLUE)
        c.drawString(left, self.height-5, 'Observed')
        c.setFillColor(MUTED)
        c.drawString(left+65, self.height-5, 'Baseline (4 matching weekdays)')

def pdf_executive_brief(row: dict, financial: dict | None) -> str:
    """Complete, deterministic first-page business summary from validated data."""
    traffic = row['session_change_pct']
    traffic_word = 'rose' if traffic >= 0 else 'fell'
    rate = row['purchase_rate_change_pct']
    rate_word = 'fell' if rate < 0 else 'rose'
    summary = (
        f"Sessions {traffic_word} {abs(traffic):.1f}% to {row['observed_sessions']:,} "
        f"(four-weekday baseline {row['baseline_sessions']:,.0f}). "
        f"Purchase-session rate {rate_word} {abs(rate):.1f}% to "
        f"{row['observed_purchase_rate_pct']:.2f}% "
        f"(baseline {row['baseline_purchase_rate_pct']:.2f}%). "
    )
    if financial:
        evidence_type = financial.get('revenue_evidence_type', 'recorded')
        label = 'Modeled' if evidence_type == 'modeled' else 'Recorded'
        summary += f"{label} revenue was ${financial['purchase_revenue_usd']:,.2f}. "
        difference = financial.get('revenue_difference_usd')
        baseline = financial.get('baseline_revenue_usd')
        percentage = financial.get('relative_revenue_change_pct')
        if difference is not None and baseline is not None and percentage is not None:
            summary += (
                f"That is ${difference:+,.2f} ({percentage:+.1f}%) "
                f"versus the ${baseline:,.2f} Monday benchmark. "
            )
        if evidence_type == 'modeled':
            summary += 'This is a scenario estimate, not verified lost revenue.'
        else:
            summary += 'This comparison does not establish a causal effect.'
    else:
        summary += 'Revenue evidence is unavailable for this selected investigation.'
    return summary



def generate_pdf(row: dict, rows: list[dict], financial: dict | None = None) -> bytes:
    """Compact report with full selected assessment and natural page breaks."""
    financial = reporting_financial_evidence(row, financial)
    if is_synthetic(row):
        financial = None
    ordered = sorted(rows, key=lambda r: r['investigation_date'])
    output = BytesIO()
    width = A4[0]-76
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=38, rightMargin=38,
                            topMargin=65, bottomMargin=50, title='Maxim | Executive investigation',
                            author='Signal Investigator | Maxim')
    styles = {
        'title': ParagraphStyle('title', fontName='Times-Roman', fontSize=25, leading=28, textColor=INK, spaceAfter=12),
        'h2': ParagraphStyle('h2', fontName='Times-Roman', fontSize=18, leading=21, textColor=INK, spaceBefore=14, spaceAfter=10, keepWithNext=True),
        'h3': ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=INK, spaceBefore=9, spaceAfter=5, keepWithNext=True),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=9, leading=13, textColor=INK, spaceAfter=8),
        'small': ParagraphStyle('small', fontName='Helvetica', fontSize=7.7, leading=11, textColor=MUTED, spaceAfter=6),
        'label': ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=7, leading=10, textColor=MUTED, spaceAfter=4),
        'value': ParagraphStyle('value', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=INK, spaceAfter=4),
        'cell': ParagraphStyle('cell', fontName='Helvetica', fontSize=7.5, leading=11, textColor=INK),
    }
    story = []
    add = lambda text, kind='body': story.append(para(text, styles[kind]))
    kind = severity(row)
    status = {'red':'Action needed', 'yellow':'Watchlist', 'green':'No qualifying anomaly', 'unknown':'Verify data'}[kind]
    if is_synthetic(row):
        status = 'SYNTHETIC INTERVIEW ALERT - NOT A REAL HISTORICAL INCIDENT'
    add('EXECUTIVE INVESTIGATION REPORT', 'label')
    add(executive_headline(row), 'title')
    add(f'{row["investigation_date"]} | {status} | Window: {report_window(ordered)}', 'small')
    cards = []
    for item in kpi_definitions(row):
        cards.append([para(item['title'].upper(), styles['label']), para(item['value'], styles['value']), para(item['delta'], styles['small'])])
    grid = Table([cards[:3], cards[3:]], colWidths=[width/3]*3, hAlign='LEFT')
    grid.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),PALE),
                             ('BOX',(0,0),(-1,-1),.5,LINE),('INNERGRID',(0,0),(-1,-1),.5,LINE),
                             ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
                             ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.extend([grid, Spacer(1, 10)])
    # A concise deterministic brief retains financial provenance even if AI prose is old.
    add('Commercial context', 'h3')
    add(pdf_executive_brief(row, financial))
    add("Maxim's executive assessment", 'h2')
    assessment = row.get('executive_summary') if row.get('has_ai_investigation') else None
    if assessment:
        # Paragraphs may flow over pages; no maximum height or sentence truncation.
        for paragraph in re.split(r'\n\s*\n', str(assessment)):
            add(paragraph)
    else:
        add('No AI investigation was generated for this date. The report presents deterministic evidence only.')
    add('AI-generated interpretation; factual review pending. Hypotheses are unverified.' if row.get('has_ai_investigation')
        else 'Rule-based assessment; no AI-generated causes.', 'small')
    add('Detector decision', 'h3')
    add(alert_reason(row))
    d = decision(row)
    add('Recommended next step', 'h3')
    add(d['action'])
    add(f"{d['why']} Suggested owner role: {d['owner']} (illustrative, not assigned).", 'small')
    story.append(PageBreak())
    add('Hypotheses and proposed investigations', 'title')
    add('These are possibilities to validate, not established causes or probability rankings.', 'small')
    for i, item in enumerate(hypotheses(row), 1):
        add(f'{i:02d} | {item.get("title", "Hypothesis")}', 'h3')
        add(item.get('explanation', ''))
        needed = item.get('data_needed')
        if isinstance(needed, list) and needed:
            add('Evidence needed: ' + '; '.join(map(str, needed)), 'small')
        if item.get('validation_check'):
            add('Validation check: ' + str(item['validation_check']), 'small')
    add('Recommendations', 'h2')
    checks = recommended_checks(row)
    if not checks:
        add(d['action'])
    for i, item in enumerate(checks, 1):
        action = str(item.get('action', 'Review evidence'))
        add(f'{i:02d} | {action}', 'h3')
        add(item.get('purpose', ''))
        needed = item.get('inputs_needed')
        if isinstance(needed, list) and needed:
            add('Required inputs: ' + '; '.join(map(str, needed)), 'small')
        add(f'Suggested role: {suggested_owner_role(action)} | Proposed - review required | Impact not quantified.', 'small')
    story.append(PageBreak())
    add('Performance evidence and methodology', 'title')
    add('Purchase-session rate against historical baseline', 'h3')
    story.append(EvidenceChart(ordered, row, 'rate', width=width))
    add('Sessions against historical baseline', 'h3')
    story.append(EvidenceChart(ordered, row, 'sessions', width=width))
    add('Source evidence for the selected reporting window', 'h3')
    table_rows = [[para(v, styles['label']) for v in ['Date','Sessions','Baseline sessions','Rate','Baseline rate','Revenue USD']]]
    for record in ordered:
        revenue = reporting_financial_evidence(record)
        values = [record['investigation_date'],f'{record["observed_sessions"]:,}',f'{record["baseline_sessions"]:,.1f}',
                  f'{record["observed_purchase_rate_pct"]:.2f}%', f'{record["baseline_purchase_rate_pct"]:.2f}%',
                  f'${revenue["purchase_revenue_usd"]:,.2f}' if revenue else 'Unavailable']
        table_rows.append([para(v, styles['cell']) for v in values])
    table = Table(table_rows, colWidths=[width*f for f in (.18,.15,.18,.12,.15,.22)], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),PALE),
                              ('LINEBELOW',(0,0),(-1,-1),.4,LINE),('LEFTPADDING',(0,0),(-1,-1),6),
                              ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(table)
    add('Methodology and limitations', 'h3')
    add('Historical, obfuscated public GA4 ecommerce sample. Baseline: four previous matching weekdays. '
        'Purchase-rate alerts require at least 150 sessions, a relative rate decline of at least 35%, '
        'and an estimated purchasing-session gap of at least 15. These are descriptive heuristics, not '
        'statistical significance tests. Yellow watchlist is a separate follow-up policy. '
        'Purchasing sessions are not orders or proven lost revenue. Recorded and modeled revenue remain distinct. '
        'Daily aggregate evidence cannot establish channel, device, checkout, inventory or causal financial effects.', 'small')
    if is_synthetic(row):
        add('SYNTHETIC RED ALERT - INTERVIEW DEMONSTRATION ONLY. Not a real historical incident.', 'small')

    def header(c, _doc):
        c.saveState()
        c.setFillColor(INK)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(38, A4[1]-30, 'Signal Investigator')
        c.setFont('Helvetica', 7)
        c.setFillColor(MUTED)
        c.drawString(38, A4[1]-42, 'Maxim | AI Analytics Investigation Agent')
        c.drawRightString(A4[0]-38, A4[1]-32, row['investigation_date'])
        c.setStrokeColor(LINE)
        c.line(38, A4[1]-50, A4[0]-38, A4[1]-50)
        c.restoreState()

    doc.build(story, onFirstPage=header, onLaterPages=header, canvasmaker=PaginatedCanvas)
    return output.getvalue()
