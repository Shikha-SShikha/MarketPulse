"""Test PDF generation functionality."""

import sys
sys.path.insert(0, '/home/shikha/Main/Coding/Prototype 3/backend')

from app.database import SessionLocal
from app.services import get_current_brief, get_themes_by_ids, get_signals_by_ids
from app.pdf_generator import generate_brief_pdf

# Get database session
db = SessionLocal()

try:
    # Get current brief
    brief = get_current_brief(db)

    if not brief:
        print("ERROR: No brief found")
        sys.exit(1)

    print(f"✓ Brief ID: {brief.id}")
    print(f"✓ Week: {brief.week_start} to {brief.week_end}")
    print(f"✓ Themes: {len(brief.theme_ids)}")

    # Get themes
    themes = get_themes_by_ids(db, brief.theme_ids)
    print(f"✓ Themes loaded: {len(themes)}")

    # Get signals
    all_signal_ids = []
    for theme in themes:
        all_signal_ids.extend(theme.signal_ids or [])
    print(f"✓ Total signal IDs: {len(all_signal_ids)}")

    signals_map = get_signals_by_ids(db, all_signal_ids)
    print(f"✓ Signals loaded: {len(signals_map)}")

    # Generate PDF
    print("\nGenerating PDF...")
    pdf_buffer = generate_brief_pdf(db, brief, themes, signals_map)

    # Write to file
    output_file = "/tmp/test_brief_output.pdf"
    with open(output_file, "wb") as f:
        f.write(pdf_buffer.getvalue())

    import os
    file_size = os.path.getsize(output_file)
    print(f"✓ PDF generated successfully!")
    print(f"✓ File: {output_file}")
    print(f"✓ Size: {file_size:,} bytes")

    # Verify it's a PDF
    with open(output_file, "rb") as f:
        header = f.read(4)
        if header == b'%PDF':
            print(f"✓ Valid PDF header confirmed")
        else:
            print(f"✗ Invalid PDF header: {header}")

finally:
    db.close()
