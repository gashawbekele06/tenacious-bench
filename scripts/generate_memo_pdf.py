"""Generate memo.pdf — 2-page executive memo for Tenacious-Bench Path A."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUT = os.path.join(os.path.dirname(__file__), "..", "memo.pdf")

BLUE_DARK = colors.HexColor("#1F3864")
BLUE_MID  = colors.HexColor("#2E75B6")
BLUE_LITE = colors.HexColor("#EEF2F7")
RED_DARK  = colors.HexColor("#7B0000")
GREY      = colors.HexColor("#595959")
LTGREY    = colors.HexColor("#CCCCCC")

styles = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=11, textColor=BLUE_DARK,
    spaceBefore=10, spaceAfter=4)

H2 = ParagraphStyle("H2", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=10, textColor=RED_DARK,
    spaceBefore=10, spaceAfter=4)

BODY = ParagraphStyle("BODY", parent=styles["Normal"],
    fontName="Helvetica", fontSize=9, leading=13,
    spaceBefore=3, spaceAfter=3)

BULLET = ParagraphStyle("BULLET", parent=styles["Normal"],
    fontName="Helvetica", fontSize=9, leading=13,
    leftIndent=18, firstLineIndent=-12,
    spaceBefore=2, spaceAfter=2)

SMALL = ParagraphStyle("SMALL", parent=styles["Normal"],
    fontName="Helvetica", fontSize=8, textColor=GREY,
    spaceBefore=0, spaceAfter=6)

TITLE = ParagraphStyle("TITLE", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=14, textColor=BLUE_DARK,
    spaceBefore=0, spaceAfter=2)

TITLE2 = ParagraphStyle("TITLE2", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=13, textColor=RED_DARK,
    spaceBefore=0, spaceAfter=4)

def hr():
    return HRFlowable(width="100%", thickness=1.5, color=BLUE_MID,
                      spaceBefore=6, spaceAfter=6)

def h1(t):  return Paragraph(t, H1)
def h2(t):  return Paragraph(t, H2)
def p(t):   return Paragraph(t, BODY)
def bl(t):  return Paragraph(f"• {t}", BULLET)

table_data = [
    [Paragraph("<b>Metric</b>", BODY), Paragraph("<b>Value</b>", BODY)],
    ["Delta A (trained vs baseline)", "0.0000  |  p=1.0  |  NOT significant  (n=3)"],
    ["Delta B (trained vs prompted)",  "0.0000  |  p=1.0  |  NOT significant  (n=3)"],
    ["Delta C (vs τ²-Bench 0.61)",       "Trained mean: 0.5315  | −0.0785 gap  (informational)"],
    ["Output length reduction",        "−18%  (trained 210w vs baseline 256w)  ✓"],
    ["Loss curve",                     "3.08 → 0.42 over 80 steps  ·  convergence confirmed"],
    ["Total cost",                     "~$2.12 API + $0.00 compute  (free Colab T4)"],
]

table_style = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), BLUE_MID),
    ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",   (0, 0), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BLUE_LITE]),
    ("GRID",       (0, 0), (-1, -1), 0.5, LTGREY),
    ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING",   (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
])

story = []

# ── PAGE 1 ──────────────────────────────────────────────────────────────────
story.append(Paragraph("EXECUTIVE MEMO   |   Tenacious-Bench v0.1 — Path A SFT Experiment", TITLE))
story.append(Paragraph("Gashaw Bekele  ·  gashaw@10academy.org  ·  2026-04-29", SMALL))
story.append(hr())

story.append(h1("Decision"))
story.append(p("Train a LoRA adapter on Tenacious-Bench SFT pairs (Path A) targeting surface-level generation failures identified in Week 10. Publish as a reproducible baseline; do not deploy to production."))

story.append(h1("Evidence Summary"))
t = Table(table_data, colWidths=[2.3*inch, 4.3*inch])
t.setStyle(table_style)
story.append(t)
story.append(Spacer(1, 6))

story.append(h1("Root Cause Analysis — Why Delta A = 0.0"))
story.append(bl("0.5B backbone cannot enforce negative lexical constraints. All conditions reproduce “bench” from the input context via attention copying."))
story.append(bl("Two of three held-out tasks use metadata check values that auto-pass regardless of output content (rubric design artefact)."))
story.append(bl("Word count threshold (120 words): both trained (210w) and baseline (256w) clear it — the check is not discriminating at this cutoff."))

story.append(h1("Recommendation"))
story.append(p("The v0.1 adapter is not a null result — it learned concision (−18% length reduction) and the loss curve confirms style learning. The delta=0 finding is a measurement problem (n=3 held-out, metadata auto-pass) compounded by a backbone capacity problem. Recommended next action: re-run on Qwen2.5-1.5B with the same 221 pairs and a clean held-out set (n≥20, no metadata auto-pass tasks). The current adapter is published as a citable baseline."))

story.append(PageBreak())

# ── PAGE 2 ──────────────────────────────────────────────────────────────────
story.append(Paragraph("APPENDIX — Skeptic’s Corner", TITLE2))
story.append(hr())

story.append(h2("Four Failure Modes Not Captured by This Benchmark"))

story.append(bl("<b>1. Multi-turn memory decay.</b> The benchmark evaluates single outreach emails. The agent’s ability to maintain tone across a 5-turn objection-handling thread is not measured. Drift that only manifests at turn 4+ is invisible to Tenacious-Bench v0.1."))
story.append(bl("<b>2. Prospect-specific register calibration.</b> All tasks use a fixed style guide. The bench does not test whether the agent can modulate tone for different seniority levels (VP vs IC) or industries without being explicitly told to."))
story.append(bl("<b>3. Retrieval grounding under conflicting signals.</b> Tasks provide a single hiring signal. Real deployments may have conflicting signals (two signals, different dates, different team names). The bench does not test which signal the agent references."))
story.append(bl("<b>4. Calibrated uncertainty expression.</b> No task requires epistemic hedging (“we have limited data on your company”). The bench rewards confident grounding; it would penalise appropriate uncertainty on low-signal tasks."))

story.append(h2("Ground Truth Lossiness"))
story.append(p("Gold-standard SFT pairs were generated by Claude Haiku with the style guide as the system prompt. This conflates (1) the correct register for the task with (2) Claude Haiku’s specific phrasings. If Haiku has systematic stylistic preferences (e.g., always closing with a question), those preferences are baked into the gold standard and learned by the adapter regardless of whether they are required by the style guide."))

story.append(h2("Unresolved Failure"))
story.append(p("Probe P-010 (turn-4 vendor-speak trigger rate 0.38) is the most behaviorally significant failure from Week 10. It is not covered by any held-out task in v0.1. All three held-out tasks are single-turn email generation. Whether the adapter learned to suppress vendor-speak in multi-turn contexts is unknown."))

story.append(h2("Kill-Switch Triggers"))
story.append(p("Suspend the adapter immediately if any of the following are observed in production:"))
story.append(bl("Any output containing a competitor name not present in the input context."))
story.append(bl("Tone score below 3.5/5.0 on more than 10% of outputs in a 24-hour window."))
story.append(bl("Output length exceeding 300 words (regression past baseline)."))
story.append(bl("The word “bench” appearing in prospect-facing text after v0.2 ships on 1.5B backbone."))

doc = SimpleDocTemplate(
    OUT,
    pagesize=letter,
    rightMargin=0.75*inch,
    leftMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
)
doc.build(story)
print(f"Written: {os.path.abspath(OUT)}")
