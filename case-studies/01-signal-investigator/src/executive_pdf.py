"""On-demand, two-page PDF executive brief from validated GA4 records.

Report styling follows the attached executive-report *layout*, but never imports
sample financial claims. Export is offline; no cloud calls or filesystem writes.
"""
from __future__ import annotations

from io import BytesIO
import re
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from src.dashboard_presentation import severity
from src.interview_demo import is_synthetic
from src.executive_report import (
    alert_reason, decision, email_brief, hypotheses, kpi_definitions,
    recommended_checks, report_window, short_summary, suggested_owner_role,
    executive_headline, display_action_title,
)

PAPER = '#F3F4F6'
DARK = '#111827'
NAVY = '#111827'
INK = '#202833'
MUTED = '#667085'
BORDER = '#E2E6EB'
ORANGE = '#BE4B07'
WARNING_BG = '#FFF2E7'
BLUE = '#21559F'


def color(value: str):
    return colors.HexColor(value)


def card(pdf, x, y, w, h, fill='#FFFFFF', stroke=BORDER, r=9):
    pdf.setLineWidth(.7)
    pdf.setStrokeColor(color(stroke))
    pdf.setFillColor(color(fill))
    pdf.roundRect(x, y, w, h, r, stroke=1, fill=1)


def text(pdf, x, y, value, *, font='Helvetica', size=10, fill=INK):
    pdf.setFillColor(color(fill))
    pdf.setFont(font, size)
    pdf.drawString(x, y, str(value))


def paragraph(pdf, value, x, top, width, *, size=9, leading=None, fill=INK, bold=False, max_height=200):
    """Fit a complete readable paragraph to its allocated PDF space.

    Do not insert '[excerpt]' or truncate a number mid-sentence. The fixed-size
    PDF is an executive *brief*; its text is intentionally concise upstream.
    """
    content = str(value).strip()
    original_leading = leading or size * 1.4
    font_name = 'Helvetica-Bold' if bold else 'Helvetica'
    # Reduce typography only when required, rather than cutting the content.
    for factor in (1, .95, .90, .85, .80, .75, .70, .65, .60):
        actual_size = max(6.2, size * factor)
        actual_leading = original_leading * (actual_size / size)
        style = ParagraphStyle('pdf_text', fontName=font_name,
                               fontSize=actual_size, leading=actual_leading,
                               textColor=color(fill), alignment=TA_LEFT)
        candidate = Paragraph(escape(content).replace('\n', '<br/>'), style)
        _, height = candidate.wrap(width, 10000)
        if height <= max_height + .1:
            candidate.drawOn(pdf, x, top-height)
            return top-height
    # Rare long free-text responses can exceed a fixed card even at 6.2 pt.
    # Keep complete sentences if possible; never end on a partial number.
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z(])', content)
    style = ParagraphStyle('pdf_text', fontName=font_name,
                           fontSize=6.2, leading=7.4,
                           textColor=color(fill), alignment=TA_LEFT)
    kept = []
    for sentence in sentences:
        proposal = ' '.join([*kept, sentence])
        candidate = Paragraph(escape(proposal), style)
        _, height = candidate.wrap(width, 10000)
        if height > max_height:
            break
        kept.append(sentence)
    if not kept:
        # A giant run-on sentence cannot be displayed inside the card;
        # the card shows an explicit referral, not misleading partial data.
        kept = ['See the live Maxim dashboard for the full investigation.']
    candidate = Paragraph(escape(' '.join(kept)), style)
    _, height = candidate.wrap(width, 10000)
    candidate.drawOn(pdf, x, top-height)
    return top-height


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


def label(pdf, x, y, message, col=MUTED):
    text(pdf, x, y, str(message).upper(), font='Helvetica-Bold', size=7, fill=col)


def wrap_words(pdf, words, x, y, max_width, size=8, leading=11, max_lines=4):
    return paragraph(pdf, words, x, y, max_width, size=size, leading=leading, max_height=max_lines * leading)


def rule_chart(pdf, rows, selected, x, y, w, h, field='sessions'):
    """Draw true actual/baseline measurements as a 2-series line chart."""
    if field == 'sessions':
        obs, baseline = 'observed_sessions', 'baseline_sessions'
        title_ = 'Daily sessions: actual vs prior-weekday baseline'
    else:
        obs, baseline = 'observed_purchase_rate_pct', 'baseline_purchase_rate_pct'
        title_ = 'Purchase-session rate: actual vs prior-weekday baseline'
    card(pdf, x, y, w, h)
    text(pdf, x+15, y+h-24, title_, font='Times-Bold', size=11)
    label(pdf, x+15, y+h-39, 'Observed', INK)
    label(pdf, x+94, y+h-39, 'Baseline', BLUE)
    cx, cy, cw, ch = x+48, y+30, w-73, h-94
    vals = [float(r[obs]) for r in rows] + [float(r[baseline]) for r in rows]
    bottom = min(vals) * .88 if vals else 0
    top = max(vals) * 1.06 if vals else 1
    rng = max(top-bottom, 1e-8)
    n = len(rows)
    for j in range(4):
        yy = cy + ch * j / 3
        pdf.setStrokeColor(color('#E4E8ED'))
        pdf.setLineWidth(.6)
        pdf.line(cx, yy, cx+cw, yy)
    for which, hue in ((baseline, BLUE), (obs, INK)):
        pdf.setStrokeColor(color(hue))
        pdf.setLineWidth(2 if which == obs else 1.2)
        for i in range(max(n-1, 0)):
            p, q = rows[i], rows[i+1]
            px = cx + i / max(n-1, 1) * cw
            qx = cx + (i+1) / max(n-1, 1) * cw
            py = cy + (float(p[which])-bottom)/rng * ch
            qy = cy + (float(q[which])-bottom)/rng * ch
            pdf.line(px, py, qx, qy)
    for i, row in enumerate(rows):
        if row['investigation_date'] == selected['investigation_date']:
            point_x = cx + i/max(n-1,1)*cw
            point_y = cy + (float(row[obs])-bottom)/rng*ch
            pdf.setFillColor(color(ORANGE))
            pdf.circle(point_x, point_y, 3.5, fill=1, stroke=0)
    if n:
        text(pdf, cx, cy-15, rows[0]['investigation_date'][5:], size=7, fill=MUTED)
        text(pdf, cx+cw-32, cy-15, rows[-1]['investigation_date'][5:], size=7, fill=MUTED)


def generate_pdf(row: dict, rows: list[dict], financial: dict | None = None) -> bytes:
    """Create a branded two-page PDF. All data is input-derived."""
    from src.financial_evidence import reporting_financial_evidence
    financial = reporting_financial_evidence(row, financial)
    if is_synthetic(row):
        financial = None  # No financial revenue or lost-sales amounts simulated.
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=1)
    pdf.setTitle('Signal Investigator | Executive anomaly report')
    pdf.setAuthor('Maxim — Signal Investigator AI')
    W, H = A4
    margin, cw = 34, W-68
    ordered = sorted(rows, key=lambda x: x['investigation_date'])
    kind = severity(row)
    status_color = {'red': '#BE4B07','yellow':'#C17913','green':'#237A4B','unknown':'#64748B'}[kind]
    status_name = {'red':'ACTION NEEDED','yellow':'WATCHLIST', 'green':'NO QUALIFYING ALERT', 'unknown':'VERIFY DATA'}[kind]

    if is_synthetic(row):
        status_name = "SIMULATED RED ALERT"

    def backdrop(page):
        pdf.setFillColor(color(PAPER))
        pdf.rect(0, 0, W, H, fill=1, stroke=0)
        pdf.setFillColor(color('#FFFFFF'))
        pdf.rect(0, H-48, W, 48, fill=1, stroke=0)
        card(pdf, margin, H-36, 23, 23, DARK, DARK, r=5)
        text(pdf, margin+6, H-28, 'M', font='Helvetica-Bold', size=11, fill='#FFFFFF')
        text(pdf, margin+32, H-23, 'Signal Investigator', font='Helvetica-Bold', size=10)
        text(pdf, margin+32, H-35, 'Maxim | AI Performance Investigation Analyst', size=7, fill=MUTED)
        text(pdf, W-99, H-29, f'PAGE {page} / 2', size=7, fill=MUTED)

    backdrop(1)
    card(pdf, margin, 649, cw, 132)
    label(pdf, margin+16, 762, 'Executive investigation report')
    paragraph(pdf, executive_headline(row), margin+16, 751, cw-166,
              size=15.2, leading=18.2, bold=True, max_height=39)
    pdf.setFillColor(color(status_color))
    pdf.roundRect(W-155, 731, 105, 22, 10, fill=1, stroke=0)
    text(pdf, W-145, 738, status_name, font='Helvetica-Bold', size=7.5, fill='#FFFFFF')
    meta = [
        ('REPORTING WINDOW', report_window(ordered)),
        ('SELECTED INVESTIGATION', row['investigation_date']),
        ('COMPARED WITH', '4 matching weekdays'),
        ('DATA SOURCE', 'GA4-derived case-study metrics'),
    ]
    inner_w = (cw-40)/4
    for i, (heading, value) in enumerate(meta):
        mx = margin + 16 + i*(inner_w+3)
        card(pdf, mx, 669, inner_w-2, 48, '#F5F6F8', '#F5F6F8', r=6)
        label(pdf, mx+7, 700, heading)
        wrap_words(pdf, value, mx+7, 688, inner_w-15, size=8, leading=10, max_lines=2)
    text(pdf, margin+16, 657, 'SYNTHETIC INTERVIEW ALERT - NOT A REAL HISTORICAL INCIDENT' if is_synthetic(row) else 'Executive brief. Full investigation and analytical evidence are in Maxim online.', size=7, fill=ORANGE if is_synthetic(row) else MUTED)

    left_w = 322
    right_x = margin + left_w + 12
    right_w = cw-left_w-12
    card(pdf, margin, 450, left_w, 186)
    label(pdf, margin+14, 617, "MAXIM'S EXECUTIVE ASSESSMENT")
    paragraph(pdf, pdf_executive_brief(row, financial), margin+14, 604,
              left_w-28, size=9.2, leading=13.1, max_height=128)
    text(pdf, margin+14, 463, 'Synthetic authored example; Gemini was not called' if is_synthetic(row) else ('AI pending review' if row.get('has_ai_investigation') else 'Rule-based brief; no AI investigation'), size=7.5, fill=MUTED)
    card(pdf, right_x, 450, right_w, 186, DARK, DARK)
    label(pdf, right_x+12, 617, 'RECOMMENDED NEXT STEP', '#CFD5E4')
    d = decision(row)
    paragraph(pdf, display_action_title(d['action']), right_x+12, 593, right_w-24, size=11, leading=15.5, fill='#FFFFFF', bold=True, max_height=75)
    pdf.setStrokeColor(color('#5C6778'))
    pdf.line(right_x+12, 515, right_x+right_w-12, 515)
    paragraph(pdf, d['why'], right_x+12, 504, right_w-24, size=7.5, leading=9.4, fill='#E5E7EB', max_height=36)
    text(pdf, right_x+12, 462, 'Proposed role*: ' + d['owner'], size=7.0, fill='#CBD5E1')

    text(pdf, margin, 432, 'Key metrics', font='Times-Bold', size=15)
    text(pdf, margin+91, 434, 'Relative to matching-weekday baseline; no significance test', size=7, fill=MUTED)
    metrics = kpi_definitions(row)
    if financial:
        metrics[1] = {
            'title': ('Modeled revenue (USD)' if financial['revenue_evidence_type'] == 'modeled'
                      else 'Recorded revenue (USD)'),
            'value': '$'+format(financial['purchase_revenue_usd'], ',.0f'),
            'delta': (f"{financial['relative_revenue_change_pct']:+.1f}% vs baseline" if financial.get('relative_revenue_change_pct') is not None else 'baseline pending'),
        }
    card_w = (cw-5*7)/6
    for i, item in enumerate(metrics):
        mx = margin + i*(card_w+7)
        card(pdf, mx, 332, card_w, 87)
        wrap_words(pdf, item['title'], mx+8, 405, card_w-16, size=7.4, leading=8.8, max_lines=2)
        text(pdf, mx+8, 367, item['value'], font='Helvetica-Bold', size=15.8)
        wrap_words(pdf, item['delta'], mx+8, 350, card_w-15, size=7, leading=9, max_lines=2)

    card(pdf, margin, 74, cw, 241, '#FFFFFF', '#E8D8CB')
    pdf.setFillColor(color('#FBEEE7'))
    pdf.roundRect(margin+.6, 268, cw-1.2, 46, 7, fill=1, stroke=0)
    label(pdf, margin+14, 298, 'SELECTED SIGNAL  |  ' + status_name, ORANGE)
    text(pdf, margin+14, 278, 'Performance change versus historical baseline', font='Times-Bold', size=13)
    text(pdf, margin+14, 256, 'WHY THIS DAY WAS CLASSIFIED', font='Helvetica-Bold', size=8, fill=ORANGE)
    wrap_words(pdf, alert_reason(row), margin+14, 244, 197, size=8.6, leading=12, max_lines=5)
    text(pdf, margin+14, 156, 'EVIDENCE QUALITY', font='Helvetica-Bold', size=8, fill=ORANGE)
    wrap_words(pdf, 'GA4 sessions and weekday baseline with synthetic purchasing sessions. No real checkout or channel evidence was added.' if is_synthetic(row) else 'Selected GA4-derived sessions and purchase rates; channel, device and funnel diagnostics are not included.', margin+14, 143, 197, size=8.2, leading=11.4, max_lines=5)
    rule_chart(pdf, ordered, row, margin+220, 92, cw-233, 163, field='rate' if is_synthetic(row) else 'sessions')
    pdf.showPage()

    backdrop(2)
    card(pdf, margin, 582, cw, 198)
    text(pdf, margin+14, 756, 'Hypotheses to investigate', font='Times-Bold', size=16)
    text(pdf, margin+14, 739, 'Hypotheses are unverified. Order is not a confidence ranking.', size=8, fill=MUTED)
    hyp = hypotheses(row)
    if hyp:
        width = (cw-42)/min(3,max(1,len(hyp)))
        for i, h in enumerate(hyp[:3]):
            x = margin+14 + i*(width+7)
            card(pdf, x, 597, width, 128, fill='#FFFFFF')
            label(pdf, x+9, 710, f'HYPOTHESIS {i+1}')
            paragraph(pdf, h.get('title','Hypothesis'), x+9, 695, width-18, size=9.2, leading=12, bold=True, max_height=40)
            label(pdf, x+9, 647, 'EVIDENCE NEEDED')
            needed = ', '.join(map(str, h.get('data_needed', [])))
            paragraph(pdf, needed or 'Not specified', x+9, 637, width-18, size=7.5, leading=10, max_height=33)
            text(pdf, x+9, 603, 'Unverified | ' + suggested_owner_role(h.get('title', '')), size=7, fill=ORANGE)
    else:
        paragraph(pdf, 'No AI hypotheses available for this date. Maxim has not run an investigation here.', margin+14, 695, cw-28, size=9.5)

    card(pdf, margin, 398, cw, 171)
    text(pdf, margin+14, 544, 'Recommended checks', font='Times-Bold', size=16)
    text(pdf, margin+14, 527, 'Owner roles illustrative; financial impact and deadlines remain unverified.', size=8, fill=MUTED)
    checks = recommended_checks(row)
    if checks:
        for i, check in enumerate(checks[:3]):
            top = 507-i*38
            text(pdf, margin+14, top, f'{i+1:02d}', font='Helvetica-Bold', size=9, fill=ORANGE)
            paragraph(pdf, check.get('action','Follow-up'), margin+40, top+5, 170, size=8.5, leading=11.3, bold=True, max_height=30)
            needed = ', '.join(map(str, check.get('inputs_needed', [])))
            paragraph(pdf, 'Evidence: ' + (needed or 'not specified'), margin+230, top+5, cw-246, size=7.2, leading=9.7, max_height=17)
            paragraph(pdf, 'Proposed role*: ' + suggested_owner_role(check.get('action', '')), margin+230, top-13, cw-246, size=7.2, leading=9.7, max_height=12)
            if i<2:
                pdf.setStrokeColor(color(BORDER))
                pdf.line(margin+14, top-30, margin+cw-14, top-30)
    else:
        paragraph(pdf, decision(row)['action'], margin+14, 510, cw-28, size=9)

    rule_chart(pdf, ordered, row, margin, 183, cw, 202, field='sessions' if is_synthetic(row) else 'rate')
    card(pdf, margin, 67, cw, 103)
    text(pdf, margin+14, 150, 'Appendix | scope and methodology', font='Times-Bold', size=13)
    details = [
        ('SIMULATED ALERT, NOT HISTORICAL: GA4 sessions/baseline + synthetic purchasing sessions.' if is_synthetic(row) else 'Data: GA4-derived case study (daily metrics may be modified); not live.'),
        'Baseline: mean of four previous matching weekdays; expected range and statistical confidence not estimated.',
        'Purchasing sessions are not orders. Shortfall is not proven lost sales, revenue or ROAS.',
        ('Synthetic scenario: no revenue figures, lost-sales or business impact is asserted.' if is_synthetic(row) else (('Modeled' if financial['revenue_evidence_type'] == 'modeled' else 'Recorded') + ' revenue: $' + format(financial['purchase_revenue_usd'], ',.0f') + ' USD; baseline variance not confirmed lost sales.') if financial else 'Model text requires factual review. Root cause and financial impact unconfirmed.'),
    ]
    for i, msg in enumerate(details):
        text(pdf, margin+14, 132-i*16, f'• {msg}' if False else '- '+msg, size=7.7, fill=MUTED)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
