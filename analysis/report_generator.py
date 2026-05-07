"""
report_generator.py — Session Report (English, data-focused)
=============================================================
Magazine-style visual design, but informational copy.
"""

import base64
import io
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd

from analysis.statistics_engine import SessionStatistics
from config import REPORT_DIR, EventType


# Color palette (magazine inspired)
INK       = "#1A1A1A"
PAPER     = "#FAF7F2"
ACCENT    = "#C8471D"
ACCENT_2  = "#2B5F7F"
SOFT      = "#E8DFD3"
MUTED     = "#6B6158"
FOCUS_GR  = "#3A7A3A"
WARN_OR   = "#C8741D"
BAD_RD    = "#A62626"

rcParams.update({
    "font.family": "serif",
    "font.serif":  ["Georgia", "DejaVu Serif", "Times New Roman"],
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlelocation": "left",
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelsize": 10,
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "savefig.edgecolor": "none",
    "grid.color": "#D9D2C4",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
})


EVENT_LABELS_EN = {
    EventType.FOCUSED:        "Focused",
    EventType.LOOKING_AWAY:   "Looking away",
    EventType.EYES_CLOSED:    "Eyes closed",
    EventType.FACE_ABSENT:    "Not at desk",
    EventType.PHONE_DETECTED: "Phone visible",
    EventType.SOCIAL_MEDIA:   "Social media",
    EventType.PRODUCTIVE_APP: "Productive app",
    EventType.UNKNOWN_APP:    "Other app",
}

# English recommendation mapping
RECOMMENDATION_MAP = {
    "Ortalama odak skorun düşük. 25 dakika Pomodoro + 5 dakika mola dene.":
        "Average focus score is low. Try a 25-min Pomodoro + 5-min break cycle.",
    "Oturumun %15'inden fazlasında telefon görüldü. Telefonu başka odaya koymayı düşün.":
        "The phone was visible in more than 15% of the session. Consider moving it to another room.",
    "Sosyal medya kullanımın yüksek. Cold Turkey veya Freedom gibi site engelleyici kullanmayı düşün.":
        "Social media usage is high. Consider a site blocker like Cold Turkey or Freedom.",
    "Uyuklama belirtileri gözlemlendi. Uyku düzenini gözden geçir.":
        "Signs of drowsiness were observed. Consider reviewing your sleep schedule.",
    "Odaklanma seviyen zamanla düştü. Oturum başına daha kısa süreler planla.":
        "Focus level declined over time. Plan shorter sessions to maintain performance.",
    "Odaklanma seviyen zamanla arttı — ısınma etkisi. Isınma rutini oluşturabilirsin.":
        "Focus level improved over time (warm-up effect). A warm-up routine could accelerate this.",
    "Odak skorunun varyansı yüksek — tutarsız çalışıyorsun. Düzenli aralıklarla kısa molalar verebilirsin.":
        "Focus score variance is high — inconsistent work pattern. Regular short breaks may help.",
    "Harika bir oturum! Dengeli ve sürdürülebilir görünüyor.":
        "Excellent session. Balanced and sustainable pattern.",
    "Oturum çok kısa; analiz için yeterli veri yok.":
        "Session too short; not enough data for analysis.",
}


# ============================================================
#                        HTML TEMPLATE
# ============================================================
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Focus Session Report — {date_short}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink: {ink};
    --paper: {paper};
    --accent: {accent};
    --accent-2: {accent2};
    --soft: {soft};
    --muted: {muted};
    --rule: #D9D2C4;
    --max: 820px;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: "Fraunces", Georgia, serif;
    background: var(--paper);
    color: var(--ink);
    line-height: 1.6;
    font-size: 17px;
    padding: 0 24px 80px;
    font-variant-numeric: oldstyle-nums;
  }}

  /* ======= MASTHEAD ======= */
  .masthead {{
    max-width: var(--max);
    margin: 72px auto 28px;
    padding-bottom: 16px;
    border-bottom: 3px double var(--ink);
  }}
  .kicker {{
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 14px;
  }}
  .masthead h1 {{
    font-family: "Fraunces", serif;
    font-weight: 800;
    font-size: clamp(38px, 5.4vw, 56px);
    line-height: 1.05;
    letter-spacing: -0.02em;
    margin-bottom: 14px;
    font-variation-settings: "opsz" 144;
  }}
  .masthead h1 .hl {{
    color: var(--accent);
  }}
  .byline {{
    display: flex;
    justify-content: space-between;
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding-top: 10px;
  }}

  /* ======= LEDE ======= */
  .lede {{
    max-width: var(--max);
    margin: 36px auto 52px;
    font-size: 18px;
    line-height: 1.65;
    color: var(--ink);
  }}
  .lede strong {{ font-weight: 600; }}

  /* ======= HERO SCORE ======= */
  .hero-score {{
    max-width: var(--max);
    margin: 0 auto 56px;
    padding: 44px 0;
    border-top: 1px solid var(--rule);
    border-bottom: 1px solid var(--rule);
    text-align: center;
  }}
  .hero-score .label {{
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
  }}
  .hero-score .value {{
    font-family: "Fraunces", serif;
    font-size: clamp(96px, 16vw, 180px);
    font-weight: 800;
    line-height: 0.9;
    letter-spacing: -0.04em;
    font-variation-settings: "opsz" 144;
  }}
  .hero-score .value .suffix {{
    font-size: 0.22em;
    font-weight: 400;
    color: var(--muted);
    margin-left: 6px;
    font-variant-numeric: normal;
  }}
  .hero-score .verdict {{
    margin-top: 14px;
    font-size: 16px;
    color: var(--muted);
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
  }}
  .v-good  .value {{ color: {focus}; }}
  .v-mid   .value {{ color: {warn_or}; }}
  .v-low   .value {{ color: {bad_rd}; }}

  /* ======= STAT STRIP ======= */
  .stat-strip {{
    max-width: var(--max);
    margin: 0 auto 72px;
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0;
  }}
  .stat-strip > div {{
    padding: 20px 12px;
    border-left: 1px solid var(--rule);
    text-align: left;
  }}
  .stat-strip > div:first-child {{ border-left: none; }}
  .stat-strip .n {{
    font-family: "Fraunces", serif;
    font-size: 26px;
    font-weight: 600;
    line-height: 1.1;
    font-variation-settings: "opsz" 96;
  }}
  .stat-strip .l {{
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 6px;
  }}

  /* ======= SECTIONS ======= */
  section {{
    max-width: var(--max);
    margin: 0 auto 60px;
  }}
  .section-kicker {{
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 8px;
  }}
  section h2 {{
    font-family: "Fraunces", serif;
    font-size: 32px;
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.01em;
    margin-bottom: 12px;
    max-width: 620px;
    font-variation-settings: "opsz" 96;
  }}
  .deck {{
    font-size: 16px;
    color: var(--muted);
    margin-bottom: 24px;
    max-width: 560px;
  }}
  section p {{ margin-bottom: 16px; font-size: 16px; }}
  section p strong {{ font-weight: 600; }}
  section p .hl {{ color: var(--accent-2); font-weight: 500; }}

  /* ======= CHARTS ======= */
  .chart-wrap {{
    margin: 24px 0;
    background: var(--paper);
  }}
  .chart-wrap img {{
    width: 100%;
    display: block;
  }}
  .chart-caption {{
    font-family: "Inter", sans-serif;
    font-size: 12.5px;
    color: var(--muted);
    margin-top: 6px;
    padding-left: 8px;
    border-left: 2px solid var(--accent);
  }}

  /* ======= KEY FINDING ======= */
  .key-finding {{
    margin: 40px auto;
    padding: 28px 36px;
    background: var(--soft);
    border-left: 4px solid var(--accent);
  }}
  .key-finding .lab {{
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 8px;
  }}
  .key-finding .txt {{
    font-family: "Fraunces", serif;
    font-size: 20px;
    line-height: 1.45;
    color: var(--ink);
    font-weight: 500;
  }}

  /* ======= TABLE ======= */
  table.ledger {{
    width: 100%;
    border-collapse: collapse;
    font-family: "Inter", sans-serif;
    font-size: 14px;
    margin-top: 14px;
  }}
  table.ledger th {{
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid var(--ink);
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 600;
  }}
  table.ledger td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--rule);
    font-variant-numeric: tabular-nums;
  }}
  table.ledger td:last-child, table.ledger th:last-child {{ text-align: right; }}
  table.ledger tr:hover {{ background: var(--soft); }}

  /* ======= RECOMMENDATIONS ======= */
  .rx-item {{
    display: grid;
    grid-template-columns: 32px 1fr;
    gap: 16px;
    padding: 18px 0;
    border-top: 1px solid var(--rule);
    align-items: start;
  }}
  .rx-item:last-child {{ border-bottom: 1px solid var(--rule); }}
  .rx-num {{
    font-family: "Fraunces", serif;
    font-size: 20px;
    color: var(--accent);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }}
  .rx-text {{ font-size: 16px; line-height: 1.55; }}

  /* ======= TEST BOX ======= */
  .test-box {{
    background: var(--soft);
    padding: 24px 28px;
    margin-top: 20px;
    font-family: "Inter", sans-serif;
    font-size: 14px;
    line-height: 1.6;
  }}
  .test-box .test-kicker {{
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 8px;
  }}
  .test-box .p-val {{
    font-family: "Fraunces", serif;
    font-size: 30px;
    font-weight: 600;
    margin: 2px 0 8px;
  }}
  .test-box code {{
    font-family: "JetBrains Mono", monospace;
    font-size: 12.5px;
    background: #FFF;
    padding: 2px 6px;
    border-radius: 2px;
  }}

  /* ======= FOOTER ======= */
  footer {{
    max-width: var(--max);
    margin: 80px auto 0;
    padding-top: 24px;
    border-top: 3px double var(--ink);
    text-align: center;
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted);
  }}
  footer .mark {{
    font-family: "Fraunces", serif;
    font-size: 15px;
    letter-spacing: 0.04em;
    color: var(--ink);
    font-weight: 600;
    text-transform: none;
    margin-bottom: 10px;
  }}

  .num {{ font-variant-numeric: tabular-nums; }}

  @media (max-width: 640px) {{
    body {{ font-size: 15px; padding: 0 16px 60px; }}
    .masthead {{ margin-top: 40px; }}
    .stat-strip {{ grid-template-columns: repeat(2, 1fr); }}
    .stat-strip > div {{ border-left: none; border-top: 1px solid var(--rule); }}
    .stat-strip > div:nth-child(-n+2) {{ border-top: none; }}
  }}
</style>
</head>
<body>

<header class="masthead">
  <div class="kicker">◆ Focus Session · Report {issue}</div>
  <h1>Focus Session <span class="hl">Report</span></h1>
  <div class="byline">
    <span>{date_long}</span>
    <span>FOCUSGUARD · {duration_min} MIN</span>
  </div>
</header>

<p class="lede">
  This report summarizes a <strong>{duration_min}-minute</strong> study session.
  Webcam frames, head orientation, eye state, and active windows were
  continuously monitored. Events were stored in custom data structures,
  indexed by time, and analyzed statistically. The findings are presented below.
</p>

<div class="hero-score {verdict_class}">
  <div class="label">Productivity Score</div>
  <div class="value"><span class="num">{productivity}</span><span class="suffix">/100</span></div>
  <div class="verdict">{verdict_text}</div>
</div>

<div class="stat-strip">
  <div><div class="n num">{avg}</div><div class="l">mean focus</div></div>
  <div><div class="n num">{median}</div><div class="l">median focus</div></div>
  <div><div class="n num">{std}</div><div class="l">std. dev.</div></div>
  <div><div class="n num">{iqr}</div><div class="l">IQR</div></div>
  <div><div class="n num">{minv}–{maxv}</div><div class="l">min–max</div></div>
  <div><div class="n num">{total_events}</div><div class="l">total events</div></div>
</div>

<section>
  <div class="section-kicker">I · Time Series</div>
  <h2>Focus Over Time</h2>
  <p class="deck">
    Minute-by-minute focus score and its 5-minute moving average.
  </p>
  <p>
    The linear regression slope is <span class="hl">{slope}</span> points/minute.
    {trend_sentence}
    The dashed red line marks the 50-point warning threshold; minutes below this
    line indicate low-focus periods.
  </p>
  <div class="chart-wrap">
    <img src="data:image/png;base64,{chart_timeseries}" alt="Focus time series">
    <div class="chart-caption">
      Figure 1 — Focus score per minute (dots) with 5-min moving average (orange).
    </div>
  </div>
</section>

<section>
  <div class="section-kicker">II · Distribution</div>
  <h2>Event Breakdown</h2>
  <p class="deck">
    How the session time was distributed across event categories.
  </p>

  <div class="chart-wrap">
    <img src="data:image/png;base64,{chart_distribution}" alt="Event distribution">
    <div class="chart-caption">
      Figure 2 — Event counts by category. Green: productive, Orange: mild distractions,
      Red: severe distractions.
    </div>
  </div>

  <table class="ledger">
    <thead>
      <tr><th>Category</th><th>Count</th><th>Share</th></tr>
    </thead>
    <tbody>
      {ledger_rows}
    </tbody>
  </table>
</section>

<div class="key-finding">
  <div class="lab">Key Finding</div>
  <div class="txt">{key_finding}</div>
</div>

{correlation_section}

<section>
  <div class="section-kicker">IV · Statistical Test</div>
  <h2>Normality of Focus Distribution</h2>
  <p class="deck">
    Shapiro–Wilk test applied to per-minute focus scores.
  </p>
  <div class="test-box">
    <div class="test-kicker">Shapiro–Wilk Test</div>
    <div class="p-val num">p = {p_value}</div>
    <p style="color: var(--muted);">
      H<sub>0</sub>: The data follows a normal distribution.
      Significance level: <code>α = 0.05</code>.
      Result: <strong>{normality_verdict}</strong>.
      {normality_interp}
    </p>
  </div>
</section>

<section>
  <div class="section-kicker">V · Recommendations</div>
  <h2>Action Items</h2>
  <p class="deck">
    Data-driven suggestions for the next session.
  </p>
  <div>
    {recommendations_html}
  </div>
</section>

<footer>
  <div class="mark">FocusGuard · {date_short}</div>
  <div>data structures &nbsp;·&nbsp; computer vision &nbsp;·&nbsp; statistics</div>
</footer>

</body>
</html>"""


class ReportGenerator:

    def __init__(self, report_dir: str = REPORT_DIR):
        self.dir = Path(report_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def generate(self, stats: SessionStatistics, df: pd.DataFrame) -> Path:
        chart_ts   = self._chart_timeseries(df, stats)
        chart_dist = self._chart_distribution(stats)

        # Ledger rows
        sorted_items = sorted(
            stats.event_breakdown.items(), key=lambda x: -x[1]
        )
        ledger_rows = "\n".join(
            f"<tr><td>{EVENT_LABELS_EN.get(k, k)}</td>"
            f"<td class='num'>{v}</td>"
            f"<td class='num'>{stats.event_percentages.get(k, 0):.1f}%</td></tr>"
            for k, v in sorted_items if v > 0
        )

        # Recommendations — English
        recs_html = "\n".join(
            f'<div class="rx-item">'
            f'<div class="rx-num">{i:02d}</div>'
            f'<div class="rx-text">{RECOMMENDATION_MAP.get(r, r)}</div>'
            f'</div>'
            for i, r in enumerate(stats.recommendations, 1)
        )

        # Verdict
        p = stats.productivity_score
        if p >= 75:
            verdict_class, verdict_text = "v-good", "Balanced and productive session."
        elif p >= 50:
            verdict_class, verdict_text = "v-mid",  "Mixed results; improvement areas identified."
        else:
            verdict_class, verdict_text = "v-low",  "Challenging session; see notes below."

        # Trend sentence
        slope = stats.focus_trend_slope
        if slope > 0.5:
            trend_sentence = ("This indicates <span class='hl'>improving focus</span> "
                              "over time — a warm-up effect.")
        elif slope < -0.5:
            trend_sentence = ("This indicates <span class='hl'>declining focus</span> "
                              "over time — a fatigue signal.")
        else:
            trend_sentence = ("Focus remained <span class='hl'>relatively stable</span> "
                              "throughout the session.")

        # Normality
        if stats.normality_p_value is None:
            p_val_str = "—"
            norm_verdict = "insufficient data"
            norm_interp  = "A longer session would yield a more reliable result."
        elif stats.is_focus_normal:
            p_val_str = f"{stats.normality_p_value:.3f}"
            norm_verdict = "H₀ not rejected"
            norm_interp  = ("The focus score distribution does not significantly "
                            "deviate from normal — a consistent session pattern.")
        else:
            p_val_str = f"{stats.normality_p_value:.3f}"
            norm_verdict = "H₀ rejected"
            norm_interp  = ("The distribution is not normal. This may indicate the "
                            "session had two distinct phases (e.g., a focused phase "
                            "followed by a distracted phase).")

        # Correlation
        if stats.correlation_matrix:
            chart_corr = self._chart_correlation(stats.correlation_matrix)
            correlation_section = f"""
<section>
  <div class="section-kicker">III · Patterns</div>
  <h2>Distraction Correlations</h2>
  <p class="deck">
    Pearson correlation measures whether two event types tend to
    co-occur within the same minute.
  </p>
  <div class="chart-wrap">
    <img src="data:image/png;base64,{chart_corr}" alt="Correlation matrix">
    <div class="chart-caption">
      Figure 3 — Pearson correlations between distraction types.
      Dark red: strong positive relationship (events co-occur).
    </div>
  </div>
</section>"""
        else:
            correlation_section = ""

        key_finding = self._build_key_finding(stats)

        html = HTML.format(
            ink=INK, paper=PAPER, accent=ACCENT, accent2=ACCENT_2,
            soft=SOFT, muted=MUTED,
            focus=FOCUS_GR, warn_or=WARN_OR, bad_rd=BAD_RD,
            issue=datetime.now().strftime("%d.%m.%Y"),
            date_short=datetime.now().strftime("%d %b %Y"),
            date_long=datetime.now().strftime("%d %B %Y · %H:%M").upper(),
            duration_min=f"{stats.duration_minutes:.0f}",
            productivity=f"{stats.productivity_score:.0f}",
            verdict_class=verdict_class,
            verdict_text=verdict_text,
            avg=f"{stats.avg_focus_score:.1f}",
            median=f"{stats.median_focus_score:.1f}",
            std=f"{stats.std_focus_score:.1f}",
            iqr=f"{stats.iqr_focus_score:.1f}",
            minv=f"{stats.min_focus_score:.0f}",
            maxv=f"{stats.max_focus_score:.0f}",
            total_events=stats.total_events,
            chart_timeseries=chart_ts,
            chart_distribution=chart_dist,
            ledger_rows=ledger_rows,
            correlation_section=correlation_section,
            p_value=p_val_str,
            normality_verdict=norm_verdict,
            normality_interp=norm_interp,
            slope=f"{slope:+.2f}",
            trend_sentence=trend_sentence,
            key_finding=key_finding,
            recommendations_html=recs_html,
        )

        filename = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        path = self.dir / filename
        path.write_text(html, encoding="utf-8")
        return path

    # ============ CHART: TIME SERIES ============
    def _chart_timeseries(self, df: pd.DataFrame,
                           stats: SessionStatistics) -> str:
        fig, ax = plt.subplots(figsize=(9, 4.2))
        if df.empty:
            ax.text(0.5, 0.5, "no data available",
                    ha="center", va="center", color=MUTED, style="italic")
            ax.set_axis_off()
            return self._fig_to_b64(fig)

        x = list(range(len(df)))
        scores = df["avg_focus_score"].values

        ax.axhspan(0, 50, alpha=0.08, color=BAD_RD, zorder=0)
        ax.axhline(50, color=BAD_RD, linewidth=0.8,
                   linestyle="--", alpha=0.5, zorder=1)
        ax.text(len(x) - 0.2, 47, "warning threshold",
                ha="right", va="top", fontsize=9,
                color=BAD_RD, style="italic")

        ax.plot(x, scores, color=INK, linewidth=1.0,
                marker="o", markersize=4,
                markerfacecolor=PAPER, markeredgecolor=INK,
                markeredgewidth=1.0, zorder=3, label="per-minute score")

        if stats.rolling_avg_5min:
            ax.plot(x, stats.rolling_avg_5min, color=ACCENT,
                    linewidth=2.4, zorder=4,
                    label="5-min moving average")

        ax.set_title("Focus Score Over Time")
        ax.set_xlabel("Minute")
        ax.set_ylabel("Score (0–100)")
        ax.set_ylim(-2, 105)
        ax.set_xlim(-0.5, len(x) - 0.5)
        ax.grid(True, axis="y", alpha=0.6)
        ax.legend(frameon=False, fontsize=10, loc="lower left")

        plt.tight_layout()
        return self._fig_to_b64(fig)

    # ============ CHART: DISTRIBUTION ============
    def _chart_distribution(self, stats: SessionStatistics) -> str:
        data = [(EVENT_LABELS_EN.get(k, k), v, k)
                for k, v in stats.event_breakdown.items() if v > 0]
        data.sort(key=lambda t: t[1])
        if not data:
            fig, ax = plt.subplots(figsize=(9, 3))
            ax.text(0.5, 0.5, "no events recorded",
                    ha="center", va="center", color=MUTED, style="italic")
            ax.set_axis_off()
            return self._fig_to_b64(fig)

        labels = [d[0] for d in data]
        values = [d[1] for d in data]
        keys   = [d[2] for d in data]

        color_map = {
            EventType.FOCUSED:        FOCUS_GR,
            EventType.PRODUCTIVE_APP: FOCUS_GR,
            EventType.LOOKING_AWAY:   WARN_OR,
            EventType.EYES_CLOSED:    WARN_OR,
            EventType.FACE_ABSENT:    WARN_OR,
            EventType.PHONE_DETECTED: BAD_RD,
            EventType.SOCIAL_MEDIA:   BAD_RD,
            EventType.UNKNOWN_APP:    MUTED,
        }
        colors = [color_map.get(k, MUTED) for k in keys]

        fig_h = max(2.5, 0.45 * len(data) + 1.0)
        fig, ax = plt.subplots(figsize=(9, fig_h))
        bars = ax.barh(labels, values, color=colors, edgecolor="none", height=0.68)
        total = sum(values)
        for bar, v in zip(bars, values):
            pct = v / total * 100 if total else 0
            ax.text(bar.get_width() + max(values) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{v}  ·  {pct:.1f}%",
                    va="center", fontsize=10, color=INK)
        ax.set_title("Event Distribution")
        ax.set_xlabel("Event count")
        ax.set_xlim(0, max(values) * 1.20)
        ax.grid(False)
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(bottom=False, labelbottom=False, left=False)
        plt.tight_layout()
        return self._fig_to_b64(fig)

    # ============ CHART: CORRELATION ============
    def _chart_correlation(self, corr_dict: dict) -> str:
        df_corr = pd.DataFrame(corr_dict)
        df_corr.index = [EVENT_LABELS_EN.get(i, i) for i in df_corr.index]
        df_corr.columns = [EVENT_LABELS_EN.get(c, c) for c in df_corr.columns]

        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        cmap = plt.cm.RdBu_r
        im = ax.imshow(df_corr.values, cmap=cmap, vmin=-1, vmax=1, aspect="auto")

        ax.set_xticks(range(len(df_corr.columns)))
        ax.set_yticks(range(len(df_corr.index)))
        ax.set_xticklabels(df_corr.columns, rotation=30, ha="right")
        ax.set_yticklabels(df_corr.index)
        ax.tick_params(length=0)

        for i in range(df_corr.shape[0]):
            for j in range(df_corr.shape[1]):
                val = df_corr.values[i, j]
                color = "#FFF" if abs(val) > 0.5 else INK
                ax.text(j, i, f"{val:+.2f}", ha="center", va="center",
                        fontsize=10, color=color)

        cbar = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
        cbar.set_label("Pearson r", fontsize=10)
        cbar.outline.set_visible(False)
        ax.set_title("Distraction Correlation Matrix")
        ax.spines[:].set_visible(False)
        plt.tight_layout()
        return self._fig_to_b64(fig)

    # ============ KEY FINDING ============
    def _build_key_finding(self, stats: SessionStatistics) -> str:
        pct = stats.event_percentages
        phone = pct.get(EventType.PHONE_DETECTED, 0)
        social = pct.get(EventType.SOCIAL_MEDIA, 0)
        focus = pct.get(EventType.FOCUSED, 0)
        eyes = pct.get(EventType.EYES_CLOSED, 0)

        if social > 15:
            return (f"{social:.0f}% of the session was spent on social media — "
                    f"the largest source of distraction.")
        if phone > 12:
            return (f"The phone was visible in {phone:.0f}% of recorded events — "
                    f"the primary distraction factor.")
        if eyes > 10:
            return (f"Eyes were closed during {eyes:.0f}% of the session, "
                    f"indicating fatigue.")
        if focus > 60:
            return (f"{focus:.0f}% of the time was spent in a focused state — "
                    f"a strong performance pattern.")
        if stats.focus_trend_slope < -0.8:
            return ("Focus declined steadily from start to finish — "
                    "a typical fatigue curve.")
        return (f"Average focus: {stats.avg_focus_score:.0f}, "
                f"standard deviation: {stats.std_focus_score:.0f} — "
                f"a typical study session.")

    @staticmethod
    def _fig_to_b64(fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode("ascii")
