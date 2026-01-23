"""PDF generation utilities for weekly briefs."""

from datetime import datetime
from io import BytesIO
from typing import List

from weasyprint import HTML, CSS
from sqlalchemy.orm import Session

from app.models import WeeklyBrief, Theme, Signal


def generate_brief_html(brief: WeeklyBrief, themes: List[Theme], signals_map: dict) -> str:
    """
    Generate HTML content for a weekly brief PDF.

    Args:
        brief: WeeklyBrief ORM object
        themes: List of Theme ORM objects (in display order)
        signals_map: Dict mapping signal_id to Signal object

    Returns:
        HTML string with embedded CSS
    """

    # Format dates
    week_start = datetime.fromisoformat(str(brief.week_start)).strftime('%B %d, %Y')
    week_end = datetime.fromisoformat(str(brief.week_end)).strftime('%B %d, %Y')
    generated_at = brief.generated_at.strftime('%B %d, %Y at %I:%M %p UTC')

    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>STM Intelligence Brief - Week of {week_start}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm 1.5cm 2.5cm 1.5cm;

                @bottom-center {{
                    content: counter(page) " of " counter(pages);
                    font-size: 9pt;
                    color: #6b7280;
                }}
            }}

            * {{
                box-sizing: border-box;
            }}

            body {{
                font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 10pt;
                line-height: 1.6;
                color: #1f2937;
                margin: 0;
                padding: 0;
                position: relative;
            }}

            /* Watermark */
            body::before {{
                content: "AI-GENERATED CONTENT";
                position: fixed;
                top: 45%;
                left: 50%;
                margin-left: -300pt;
                font-size: 60pt;
                font-weight: bold;
                color: rgba(229, 231, 235, 0.25);
                z-index: -1;
                white-space: nowrap;
                pointer-events: none;
                text-align: center;
            }}

            /* Header */
            .header {{
                border-bottom: 3px solid #161616;
                padding-bottom: 1cm;
                margin-bottom: 0.8cm;
            }}

            .header h1 {{
                font-size: 24pt;
                font-weight: 600;
                color: #161616;
                margin: 0 0 0.3cm 0;
                line-height: 1.2;
            }}

            .header .subtitle {{
                font-size: 11pt;
                color: #525252;
                margin-bottom: 0.3cm;
            }}

            .metadata {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.5cm;
                font-size: 9pt;
                color: #525252;
            }}

            .metadata-item {{
                display: flex;
                align-items: center;
                gap: 0.15cm;
            }}

            .metadata-label {{
                font-weight: 500;
            }}

            /* Stats bar */
            .stats-bar {{
                background-color: #f4f4f4;
                border-left: 3px solid #0f62fe;
                padding: 0.4cm;
                margin-bottom: 0.8cm;
                display: flex;
                gap: 0.8cm;
                flex-wrap: wrap;
            }}

            .stat {{
                font-size: 9pt;
            }}

            .stat-label {{
                color: #525252;
            }}

            .stat-value {{
                font-weight: 600;
                color: #161616;
                margin-left: 0.1cm;
            }}

            .coverage-tags {{
                display: flex;
                gap: 0.2cm;
                flex-wrap: wrap;
            }}

            .coverage-tag {{
                background-color: #e0e0e0;
                color: #161616;
                padding: 0.1cm 0.25cm;
                border-radius: 2px;
                font-size: 8pt;
                font-weight: 500;
            }}

            /* Theme card */
            .theme {{
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 0.6cm;
                margin-bottom: 0.6cm;
                page-break-inside: avoid;
            }}

            .theme-header {{
                display: flex;
                align-items: flex-start;
                gap: 0.3cm;
                margin-bottom: 0.4cm;
            }}

            .theme-rank {{
                background-color: #161616;
                color: #ffffff;
                width: 0.8cm;
                height: 0.8cm;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 10pt;
                flex-shrink: 0;
            }}

            .theme-title {{
                flex: 1;
            }}

            .theme-title h2 {{
                font-size: 13pt;
                font-weight: 600;
                color: #161616;
                margin: 0 0 0.2cm 0;
                line-height: 1.3;
            }}

            .theme-badges {{
                display: flex;
                gap: 0.2cm;
                flex-wrap: wrap;
                margin-top: 0.2cm;
            }}

            .badge {{
                padding: 0.1cm 0.25cm;
                border-radius: 2px;
                font-size: 8pt;
                font-weight: 500;
            }}

            .badge-ops {{ background-color: #d0e2ff; color: #002d9c; }}
            .badge-tech {{ background-color: #e8daff; color: #491d8b; }}
            .badge-integrity {{ background-color: #ffd6a5; color: #8a3800; }}
            .badge-procurement {{ background-color: #9ef0f0; color: #004144; }}

            .badge-confidence-high {{ background-color: #defbe6; color: #0e6027; border: 1px solid #a7f0ba; }}
            .badge-confidence-medium {{ background-color: #fcf4d6; color: #8e6a00; border: 1px solid #fddc69; }}
            .badge-confidence-low {{ background-color: #ffd7d9; color: #750e13; border: 1px solid #ffa4a9; }}

            /* Section */
            .section {{
                margin-bottom: 0.4cm;
            }}

            .section-title {{
                font-size: 8pt;
                font-weight: 600;
                color: #525252;
                text-transform: uppercase;
                letter-spacing: 0.03cm;
                margin-bottom: 0.2cm;
            }}

            .section-content ul {{
                margin: 0;
                padding-left: 0;
                list-style: none;
            }}

            .section-content li {{
                position: relative;
                padding-left: 0.4cm;
                margin-bottom: 0.15cm;
                color: #161616;
            }}

            .section-content li::before {{
                content: "•";
                position: absolute;
                left: 0;
                color: #0f62fe;
                font-weight: bold;
            }}

            .key-players {{
                font-size: 9pt;
                color: #525252;
                margin-top: 0.3cm;
            }}

            .key-players-label {{
                font-weight: 500;
            }}

            /* Signals */
            .signals {{
                background-color: #f4f4f4;
                border-radius: 3px;
                padding: 0.4cm;
                margin-top: 0.4cm;
            }}

            .signals-header {{
                font-size: 9pt;
                font-weight: 600;
                color: #525252;
                margin-bottom: 0.3cm;
                padding-bottom: 0.15cm;
                border-bottom: 1px solid #e0e0e0;
            }}

            .signal {{
                margin-bottom: 0.3cm;
                padding-bottom: 0.3cm;
                border-bottom: 1px solid #e0e0e0;
            }}

            .signal:last-child {{
                margin-bottom: 0;
                padding-bottom: 0;
                border-bottom: none;
            }}

            .signal-entity {{
                font-weight: 600;
                color: #161616;
                font-size: 9pt;
            }}

            .signal-meta {{
                font-size: 8pt;
                color: #525252;
                margin-top: 0.1cm;
            }}

            .signal-snippet {{
                font-size: 8pt;
                color: #525252;
                margin-top: 0.15cm;
                font-style: italic;
            }}

            .signal-link {{
                font-size: 7pt;
                color: #0f62fe;
                word-break: break-all;
                margin-top: 0.1cm;
            }}

            /* Footer */
            .document-footer {{
                margin-top: 0.8cm;
                padding-top: 0.4cm;
                border-top: 1px solid #e0e0e0;
                text-align: center;
                font-size: 8pt;
                color: #8d8d8d;
            }}

            /* Avoid breaks */
            h1, h2, h3, .theme-header {{
                page-break-after: avoid;
            }}

            .section {{
                page-break-inside: avoid;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="header">
            <h1>STM Intelligence Brief</h1>
            <div class="subtitle">Market and Competitive Intelligence for Sales Teams</div>
            <div class="metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Week:</span>
                    <span>{week_start} — {week_end}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Generated:</span>
                    <span>{generated_at}</span>
                </div>
            </div>
        </div>

        <!-- Summary Stats -->
        <div class="stats-bar">
            <div class="stat">
                <span class="stat-label">Themes:</span>
                <span class="stat-value">{len(themes)}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Signals:</span>
                <span class="stat-value">{brief.total_signals}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Coverage:</span>
                <div class="coverage-tags">
    """

    for area in brief.coverage_areas or []:
        html += f'                    <span class="coverage-tag">{area}</span>\n'

    html += """
                </div>
            </div>
        </div>

        <!-- Themes -->
    """

    for rank, theme in enumerate(themes, start=1):
        # Get confidence badge class
        confidence_class = f"badge-confidence-{theme.aggregate_confidence.lower()}"

        html += f"""
        <div class="theme">
            <div class="theme-header">
                <div class="theme-rank">{rank}</div>
                <div class="theme-title">
                    <h2>{theme.title}</h2>
                    <div class="theme-badges">
        """

        # Impact area badges
        badge_classes = {
            'Ops': 'badge-ops',
            'Tech': 'badge-tech',
            'Integrity': 'badge-integrity',
            'Procurement': 'badge-procurement',
        }

        for area in theme.impact_areas or []:
            badge_class = badge_classes.get(area, '')
            html += f'                        <span class="badge {badge_class}">{area}</span>\n'

        html += f"""
                        <span class="badge {confidence_class}">{theme.aggregate_confidence} Confidence</span>
                    </div>
                </div>
            </div>

            <!-- Why It Matters -->
            <div class="section">
                <div class="section-title">Why It Matters</div>
                <div class="section-content">
                    <ul>
        """

        # Split so_what into sentences for bullet points
        # Smart splitting that handles abbreviations (Dr., Ph.D., etc.)
        import re

        def split_into_sentences(text: str) -> list:
            """Split text into sentences, handling common abbreviations."""
            # Split on periods followed by space and capital letter
            # BUT NOT if the period follows common abbreviations
            pattern = r'(?<!\bDr)(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bProf)(?<!\bSr)(?<!\bJr)(?<!\bInc)(?<!\bLtd)(?<!\bCorp)(?<!\bvs)(?<!\betc)(?<!\be\.g)(?<!\bi\.e)\.(?=\s+[A-Z])'

            # Split the text
            sentences = re.split(pattern, text)

            # Clean up and filter empty sentences
            sentences = [s.strip() for s in sentences if s.strip()]

            # Add periods back if missing
            result = []
            for s in sentences:
                if s and not s.endswith(('.', '!', '?')):
                    result.append(s + '.')
                else:
                    result.append(s)

            return result

        so_what_sentences = split_into_sentences(theme.so_what)
        for sentence in so_what_sentences:
            html += f'                        <li>{sentence}</li>\n'

        html += """
                    </ul>
                </div>
            </div>

            <!-- Next Steps -->
        """

        if theme.now_what:
            html += """
            <div class="section">
                <div class="section-title">Next Steps</div>
                <div class="section-content">
                    <ul>
            """
            for action in theme.now_what:
                html += f'                        <li>{action}</li>\n'

            html += """
                    </ul>
                </div>
            </div>
            """

        # Key Players
        if theme.key_players:
            key_players_str = ', '.join(theme.key_players)
            html += f"""
            <div class="key-players">
                <span class="key-players-label">Key Players:</span> {key_players_str}
            </div>
            """

        # Supporting Signals
        theme_signals = [signals_map[sid] for sid in (theme.signal_ids or []) if sid in signals_map]

        if theme_signals:
            html += f"""
            <div class="signals">
                <div class="signals-header">{len(theme_signals)} Supporting Signal{'s' if len(theme_signals) != 1 else ''}</div>
            """

            for signal in theme_signals:
                html += f"""
                <div class="signal">
                    <div class="signal-entity">{signal.entity}</div>
                    <div class="signal-meta">{signal.event_type} • {signal.topic} • {signal.confidence} Confidence</div>
                    <div class="signal-snippet">"{signal.evidence_snippet[:200]}{'...' if len(signal.evidence_snippet) > 200 else ''}"</div>
                    <div class="signal-link">{signal.source_url}</div>
                </div>
                """

            html += """
            </div>
            """

        html += """
        </div>
        """

    html += """
        <!-- Footer -->
        <div class="document-footer">
            <p>This intelligence brief was generated by MarketPulse AI and should be reviewed by a human curator.</p>
            <p>All content is AI-generated and may require verification.</p>
        </div>
    </body>
    </html>
    """

    return html


def generate_brief_pdf(db: Session, brief: WeeklyBrief, themes: List[Theme], signals_map: dict) -> BytesIO:
    """
    Generate a PDF file for a weekly brief.

    Args:
        db: Database session
        brief: WeeklyBrief ORM object
        themes: List of Theme ORM objects (in display order)
        signals_map: Dict mapping signal_id to Signal object

    Returns:
        BytesIO buffer containing PDF data
    """
    # Generate HTML
    html_content = generate_brief_html(brief, themes, signals_map)

    # Convert to PDF
    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    return pdf_buffer
