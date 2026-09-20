import os
from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

def finalize_guide():
    doc = []

    # 18. QUICK REFERENCE
    doc.append("""# 13. QUICK REFERENCE

If you need to perform a specific engineering task quickly, use this lookup guide:

- **I want to know why we lost time:** Go to the *Telemetry Performance Lab*. Compare your driver to the rival and check the Brake Point Delta.
- **I want to compare two drivers:** Go to the *Telemetry Performance Lab*.
- **I want to understand tyre behaviour:** Go to the *Command Center* and look at the *Unified Tyre Intelligence* degradation slope.
- **I want to evaluate a pit stop:** Go to the *Race Simulator & Strategy Engine*. Check the Win Probability for the baseline recommendation.
- **I want to test another strategy:** Go to the *Race Simulator* sidebar. Adjust the "Modify Pit Lap" slider and press RECALCULATE.
- **I want to understand what happened around us:** Go to the *3D Spatial Intelligence* tab. Look at the traffic clustering on the map.
- **I want a quick text summary of the race:** Go to the *JARVIS Engineering Insights* tab and ask a tactical question.

---
<div style="page-break-after: always;"></div>
""")

    # 19. FINAL CHAPTER
    doc.append("""# 14. PITWALL F1 — THE COMPLETE PICTURE

Pitwall F1 is not just a collection of charts; it is a unified intelligence pipeline. It represents a paradigm shift from *reactive* engineering to *proactive* engineering.

By automatically parsing raw FIA telemetry, interpolating distance arrays, calculating differential braking metrics, establishing empirical tyre degradation slopes, feeding those slopes into a vectorized Monte Carlo simulator, and extracting ML-driven overtake probabilities, Pitwall F1 performs the work of a 20-person strategy room in less than 500 milliseconds.

The system empowers a single user to sit at the digital pitwall, observe the physical reality of the race, simulate a thousand alternative futures, and transmit the winning command over the radio.

*End of Document.*
""")

    with open('docs/PITWALL_F1_COMPLETE_USER_GUIDE.md', 'a', encoding='utf-8') as f:
        f.write("".join(doc))

    print("Markdown completed successfully. Generating PDF...")
    
    # Generate PDF
    pdf_path = 'docs/PITWALL_F1_COMPLETE_USER_GUIDE.pdf'
    try:
        pdf = MarkdownPdf(toc_level=2)
        with open('docs/PITWALL_F1_COMPLETE_USER_GUIDE.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
        pdf.add_section(Section(md_content))
        pdf.save(pdf_path)
        print("PDF generated successfully.")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == '__main__':
    finalize_guide()
