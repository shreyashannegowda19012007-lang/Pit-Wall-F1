import os
from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

def compile_pdf():
    print("Gathering markdown parts...")
    
    parts = []
    
    # Custom CSS for page breaks to avoid orphan headers and empty pages
    # markdown_pdf handles page breaks well if structured correctly.
    cover_page = """# PITWALL F1: THE DEFINITIVE USER GUIDE
## Engineering Intelligence & Race Strategy Platform

**Document Version:** 3.0 (Comprehensive Specification)
**Target Audience:** Race Strategists, Performance Engineers, Data Scientists

---
<div style="page-break-after: always;"></div>
"""
    parts.append(cover_page)
    
    for i in range(1, 13):
        # Handle part_2b
        if i == 3:
            part_file = f'docs/parts/part_2b.md'
            if os.path.exists(part_file):
                with open(part_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Add page breaks between parts to ensure clean formatting
                    parts.append(content + "\n<div style=\"page-break-after: always;\"></div>\n")
        
        part_file = f'docs/parts/part_{i}.md'
        if os.path.exists(part_file):
            with open(part_file, 'r', encoding='utf-8') as f:
                content = f.read()
                parts.append(content + "\n<div style=\"page-break-after: always;\"></div>\n")

    full_markdown = "".join(parts)
    
    # Save the master markdown file
    md_output_path = 'docs/PITWALL_F1_DEFINITIVE_USER_GUIDE.md'
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(full_markdown)
        
    print(f"Master markdown written to {md_output_path}")
    print(f"Total markdown length: {len(full_markdown)} characters.")
    
    # Generate the PDF
    pdf_output_path = 'docs/PITWALL_F1_DEFINITIVE_USER_GUIDE.pdf'
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(full_markdown))
        pdf.save(pdf_output_path)
        print(f"PDF successfully generated at {pdf_output_path}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == '__main__':
    compile_pdf()
