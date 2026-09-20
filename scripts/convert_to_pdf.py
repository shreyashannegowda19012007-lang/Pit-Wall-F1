from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

def convert_to_pdf():
    pdf = MarkdownPdf(toc_level=2)
    with open('docs/PITWALL_F1_COMPLETE_TECHNICAL_DOCUMENTATION.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    pdf.add_section(Section(md_content))
    
    pdf.save('docs/PITWALL_F1_COMPLETE_TECHNICAL_DOCUMENTATION.pdf')
    print("PDF generated successfully.")

if __name__ == '__main__':
    convert_to_pdf()
