"""PDF Raporlama yardımcı modülü (basit sürüm)

Özellikler (v0.1):
- Arama sonuç listesini tablo halinde PDF'e döker
- Üst bilgi: başlık, tarih, toplam sonuç sayısı
- Gelecek: sayfalama, tema, logo, gelişmiş şablon (Jinja2 + HTML -> PDF)
"""
from datetime import datetime
from typing import List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.core.search_engine import SearchResult

class PDFReportExporter:
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab kurulmamış; requirements.txt ile yükleyin")
        self.styles = getSampleStyleSheet()

    def export_search_results(self, results: List[SearchResult], filename: str, query: str):
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []

        title = Paragraph(f"<b>Arama Raporu</b>", self.styles['Title'])
        subtitle = Paragraph(f"Sorgu: <b>{query}</b> | Toplam Sonuç: {len(results)} | Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal'])
        elements.append(title)
        elements.append(subtitle)
        elements.append(Spacer(1, 12))

        data = [["#", "Belge", "Tür", "Madde", "Başlık", "Skor"]]
        for idx, r in enumerate(results[:200], start=1):  # temel limit
            data.append([
                idx,
                (r.document_title or '')[:40],
                r.document_type,
                r.article_number or '',
                (r.title or '')[:40],
                f"{r.score:.3f}"
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightyellow]),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        elements.append(table)

        doc.build(elements)
        return filename
