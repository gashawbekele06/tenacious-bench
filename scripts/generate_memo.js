const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, BorderStyle, WidthType, ShadingType, HeadingLevel,
  PageBreak, ExternalHyperlink
} = require('docx');
const fs = require('fs');
const path = require('path');

const border = { style: BorderStyle.SINGLE, size: 4, color: "2E75B6" };
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const allThin = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const allNone = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function heading(text, level = 1) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: level === 1 ? 28 : 22, font: "Arial", color: "1F3864" })],
    spacing: { before: level === 1 ? 240 : 160, after: 80 },
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, size: 20, font: "Arial", ...opts })],
    spacing: { before: 60, after: 60 },
  });
}

function bullet(text, bold_prefix = null) {
  const children = [];
  if (bold_prefix) {
    children.push(new TextRun({ text: bold_prefix + " ", bold: true, size: 20, font: "Arial" }));
    children.push(new TextRun({ text, size: 20, font: "Arial" }));
  } else {
    children.push(new TextRun({ text, size: 20, font: "Arial" }));
  }
  return new Paragraph({
    children,
    bullet: { level: 0 },
    spacing: { before: 40, after: 40 },
    indent: { left: 720, hanging: 360 },
  });
}

function rule() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 1 } },
    spacing: { before: 120, after: 120 },
    children: [],
  });
}

function tableRow(label, value, shade = false) {
  const fill = shade ? "EEF2F7" : "FFFFFF";
  return new TableRow({
    children: [
      new TableCell({
        borders: allThin,
        width: { size: 2800, type: WidthType.DXA },
        shading: { fill, type: ShadingType.CLEAR },
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, size: 18, font: "Arial" })] })],
      }),
      new TableCell({
        borders: allThin,
        width: { size: 6560, type: WidthType.DXA },
        shading: { fill, type: ShadingType.CLEAR },
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: value, size: 18, font: "Arial" })] })],
      }),
    ],
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
      },
    },
    children: [
      // ── Page 1: Executive Decision Memo ─────────────────────────────
      new Paragraph({
        children: [
          new TextRun({ text: "EXECUTIVE MEMO", bold: true, size: 32, font: "Arial", color: "1F3864" }),
          new TextRun({ text: "  |  Tenacious-Bench v0.1 — Path A SFT Experiment", size: 22, font: "Arial", color: "595959" }),
        ],
        spacing: { before: 0, after: 80 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Gashaw Bekele  ·  gashaw@10academy.org  ·  2026-04-29", size: 18, font: "Arial", color: "767676" })],
        spacing: { before: 0, after: 160 },
      }),
      rule(),

      heading("Decision"),
      body("Train a LoRA adapter on Tenacious-Bench SFT pairs (Path A) targeting the surface-level generation failures identified in Week 10. Publish results as a reproducible baseline; do not deploy to production."),

      heading("Evidence Summary"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2800, 6560],
        rows: [
          tableRow("Delta A (trained vs baseline)", "0.0000  |  p=1.0  |  NOT significant  (n=3)", false),
          tableRow("Delta B (trained vs prompted)", "0.0000  |  p=1.0  |  NOT significant  (n=3)", true),
          tableRow("Delta C (vs τ²-Bench 0.61)", "Trained mean: 0.5315  |  −0.0785 gap  (informational)", false),
          tableRow("Output length reduction", "−18%  (trained 210w vs baseline 256w)  ✓", true),
          tableRow("Loss curve", "3.08 → 0.42 over 80 steps  ·  convergence confirmed", false),
          tableRow("Total cost", "~$2.12 API + $0.00 compute  (free Colab T4)", true),
        ],
      }),

      heading("Root Cause Analysis — Why Delta A = 0.0"),
      bullet("0.5B backbone cannot enforce negative lexical constraints. All conditions reproduce \"bench\" from the input context via attention copying."),
      bullet("Two of three held-out tasks use metadata check values that auto-pass regardless of output content (rubric design artefact)."),
      bullet("Word count threshold (120 words): both trained (210w) and baseline (256w) clear it — the check is not discriminating."),

      heading("Recommendation"),
      body("The v0.1 adapter is not a null result — it learned concision (−18% length reduction) and the loss curve confirms style learning. The delta=0 finding is a measurement problem (n=3 held-out, metadata auto-pass) compounded by a backbone capacity problem. Recommended next action: re-run on Qwen2.5-1.5B with the same 221 pairs and a clean held-out set (n≥20, no metadata auto-pass tasks). The current adapter is published as a citable baseline."),

      // ── Page 2: Skeptic's Appendix ──────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),

      new Paragraph({
        children: [new TextRun({ text: "APPENDIX — Skeptic's Corner", bold: true, size: 28, font: "Arial", color: "7B0000" })],
        spacing: { before: 0, after: 120 },
      }),
      rule(),

      heading("Four Failure Modes Not Captured by This Benchmark"),
      bullet("Multi-turn memory decay:", "1."),
      body("The benchmark evaluates single outreach emails. The agent's ability to maintain tone across a 5-turn objection-handling thread is not measured. Tenacious-Bench v0.1 cannot detect drift that only manifests at turn 4+.", { italic: true }),
      bullet("Prospect-specific register calibration:", "2."),
      body("All tasks use a fixed Tenacious style guide. The bench does not test whether the agent can modulate tone for different seniority levels (VP vs IC) or industries without being explicitly told to.", { italic: true }),
      bullet("Retrieval grounding under conflicting signals:", "3."),
      body("Tasks provide a single hiring signal. Real deployments may have conflicting signals (2 signals, different dates, different team names). The bench does not test which signal the agent chooses to reference.", { italic: true }),
      bullet("Calibrated uncertainty expression:", "4."),
      body("No task requires the agent to express uncertainty (\"we have limited data on your company\"). The bench rewards confident grounding; it would penalise appropriate epistemic hedging on low-signal tasks.", { italic: true }),

      heading("Ground Truth Lossiness"),
      body("The gold-standard SFT pairs were generated by Claude Haiku with the style guide as the system prompt. This conflates two things: (1) the correct register for the task, and (2) Claude Haiku's specific phrasings. If Haiku has systematic stylistic preferences (e.g., always ending with a question), those preferences are baked into the gold standard and will be learned by the adapter regardless of whether they are required by the style guide."),

      heading("Unresolved Failure"),
      body("Probe P-010 (turn-4 vendor-speak trigger rate 0.38) is the most behaviorally significant failure identified in Week 10. It is not covered by any held-out task in v0.1. The three held-out tasks are all single-turn email generation. Whether the adapter learned to suppress vendor-speak in multi-turn contexts is unknown."),

      heading("Kill-Switch Trigger"),
      body("If any of the following are observed in production, suspend the adapter immediately:"),
      bullet("Any output containing a competitor name not present in the input context."),
      bullet("Tone score below 3.5/5.0 on more than 10% of outputs in a 24-hour window."),
      bullet("Output length exceeding 300 words (regression past baseline)."),
      bullet("The word \"bench\" appearing in prospect-facing text after v0.2 ships on 1.5B backbone."),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const outPath = path.join(__dirname, '..', 'memo.docx');
  fs.writeFileSync(outPath, buf);
  console.log('Written:', outPath);
});
