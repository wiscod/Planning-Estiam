from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "Marche a suivre pour le Role 3", border=False, ln=True, align="C")
        self.ln(10)

pdf = PDF()
pdf.add_page()
pdf.set_font("helvetica", size=11)

with open("annexe/marche_a_suivre_role3.md", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
        line = line.encode('latin-1', 'replace').decode('latin-1')
        try:
            # use a specific width and simple text
            pdf.write(8, line)
            pdf.ln(8)
        except Exception:
            pdf.write(8, "[Ligne non affichable]")
            pdf.ln(8)

pdf.output("annexe/marche_a_suivre_role3.pdf")
