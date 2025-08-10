"""
PDF Raporlama Modülü - Arama sonuçlarını PDF'e aktarır
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import Color, black, blue, gray
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFExporter:
    """Mevzuat arama sonuçlarını PDF raporu olarak dışa aktarır"""
    
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not REPORTLAB_AVAILABLE:
            self.logger.warning("ReportLab kütüphanesi bulunamadı - PDF export çalışmayacak")
            return
        
        # PDF ayarları
        self.page_size = A4
        self.margin = 0.75 * inch
        
        # Stil ayarları
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Özel PDF stilleri oluştur"""
        if not REPORTLAB_AVAILABLE:
            return
        
        # Başlık stili
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=Color(0, 0.2, 0.4)
        )
        
        # Alt başlık stili
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=gray
        )
        
        # Madde başlığı stili
        self.article_title_style = ParagraphStyle(
            'ArticleTitle',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=10,
            spaceBefore=15,
            textColor=Color(0.2, 0.2, 0.6),
            keepWithNext=True
        )
        
        # İçerik stili
        self.content_style = ParagraphStyle(
            'ArticleContent',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=10,
            leftIndent=20,
            rightIndent=10,
            alignment=TA_LEFT
        )
        
        # Meta bilgi stili
        self.meta_style = ParagraphStyle(
            'MetaInfo',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=5,
            leftIndent=40,
            textColor=gray,
            italic=True
        )
    
    def export_search_results(self, results: List[Any], query: str, 
                            output_path: str, 
                            include_highlights: bool = True,
                            include_metadata: bool = True) -> Dict[str, Any]:
        """
        Arama sonuçlarını PDF raporu olarak dışa aktar
        
        Args:
            results: Arama sonuçları listesi
            query: Arama sorgusu
            output_path: PDF dosya yolu
            include_highlights: Vurguları dahil et
            include_metadata: Meta bilgileri dahil et
            
        Returns:
            Export sonucu
        """
        if not REPORTLAB_AVAILABLE:
            return {
                'success': False,
                'error': 'ReportLab kütüphanesi kurulu değil'
            }
        
        try:
            self.logger.info(f"PDF raporu oluşturuluyor: {output_path}")
            
            # PDF doküman oluştur
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # İçerik elemanları
            story = []
            
            # Başlık ve meta bilgiler
            story.extend(self._create_header(query, len(results)))
            
            # Özet tablo
            if include_metadata:
                story.extend(self._create_summary_table(results))
            
            # Arama sonuçları
            story.extend(self._create_results_section(results, include_highlights))
            
            # Footer bilgileri
            story.extend(self._create_footer())
            
            # PDF oluştur
            doc.build(story)
            
            self.logger.info(f"PDF raporu başarıyla oluşturuldu: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'results_count': len(results),
                'file_size': os.path.getsize(output_path)
            }
            
        except Exception as e:
            self.logger.error(f"PDF export hatası: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_header(self, query: str, results_count: int) -> List[Any]:
        """PDF başlığı oluştur"""
        elements = []
        
        # Ana başlık
        title = Paragraph("Mevzuat Arama Raporu", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Alt başlık
        subtitle = Paragraph(f"Arama Sorgusu: \"{query}\"", self.subtitle_style)
        elements.append(subtitle)
        elements.append(Spacer(1, 12))
        
        # Rapor bilgileri
        report_info = f"""
        <b>Rapor Tarihi:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}<br/>
        <b>Toplam Sonuç:</b> {results_count} madde<br/>
        <b>Sistem:</b> Mevzuat Belge Analiz & Sorgulama Sistemi v1.0.2
        """
        
        info_para = Paragraph(report_info, self.meta_style)
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_summary_table(self, results: List[Any]) -> List[Any]:
        """Özet tablosu oluştur"""
        elements = []
        
        # Belge türü dağılımı
        doc_types = {}
        score_ranges = {'Yüksek (>0.8)': 0, 'Orta (0.5-0.8)': 0, 'Düşük (<0.5)': 0}
        
        for result in results:
            # Belge türü sayımı
            doc_type = getattr(result, 'document_type', 'Bilinmeyen')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # Skor dağılımı
            score = getattr(result, 'score', 0)
            if score > 0.8:
                score_ranges['Yüksek (>0.8)'] += 1
            elif score > 0.5:
                score_ranges['Orta (0.5-0.8)'] += 1
            else:
                score_ranges['Düşük (<0.5)'] += 1
        
        # Tablo verileri
        table_data = [
            ['Kategori', 'Değer', 'Adet'],
        ]
        
        # Belge türleri
        for doc_type, count in doc_types.items():
            table_data.append(['Belge Türü', doc_type, str(count)])
        
        # Skor dağılımı
        for score_range, count in score_ranges.items():
            table_data.append(['Skor Dağılımı', score_range, str(count)])
        
        # Tabloyu oluştur
        table = Table(table_data, colWidths=[2*inch, 3*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Color(0.8, 0.8, 0.8)),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), Color(0.95, 0.95, 0.95)),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        elements.append(Paragraph("Özet", self.styles['Heading2']))
        elements.append(Spacer(1, 12))
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_results_section(self, results: List[Any], include_highlights: bool) -> List[Any]:
        """Arama sonuçları bölümünü oluştur"""
        elements = []
        
        # Bölüm başlığı
        section_title = Paragraph("Arama Sonuçları", self.styles['Heading2'])
        elements.append(section_title)
        elements.append(Spacer(1, 15))
        
        # Her sonuç için
        for i, result in enumerate(results, 1):
            # Madde başlığı
            title = self._get_result_title(result, i)
            article_title = Paragraph(title, self.article_title_style)
            elements.append(article_title)
            
            # Madde içeriği
            content = self._format_content(result.content)
            content_para = Paragraph(content, self.content_style)
            elements.append(content_para)
            
            # Highlight'lar
            if include_highlights and hasattr(result, 'highlights') and result.highlights:
                highlights_text = "<b>İlgili Bölümler:</b><br/>" + "<br/>".join(
                    f"• {highlight}" for highlight in result.highlights[:3]
                )
                highlights_para = Paragraph(highlights_text, self.meta_style)
                elements.append(highlights_para)
            
            # Meta bilgiler
            meta_info = self._format_meta_info(result)
            meta_para = Paragraph(meta_info, self.meta_style)
            elements.append(meta_para)
            
            elements.append(Spacer(1, 15))
            
            # Sayfa sonu (her 5 sonuçta bir)
            if i % 5 == 0 and i < len(results):
                from reportlab.platypus import PageBreak
                elements.append(PageBreak())
        
        return elements
    
    def _get_result_title(self, result: Any, index: int) -> str:
        """Sonuç başlığını formatla"""
        title_parts = [f"{index}."]
        
        if hasattr(result, 'document_title') and result.document_title:
            title_parts.append(result.document_title)
        
        if hasattr(result, 'law_number') and result.law_number:
            title_parts.append(f"(Kanun No: {result.law_number})")
        
        if hasattr(result, 'article_number') and result.article_number:
            title_parts.append(f"- Madde {result.article_number}")
        
        return " ".join(title_parts)
    
    def _format_content(self, content: str) -> str:
        """İçeriği PDF için formatla"""
        if not content:
            return "İçerik bulunamadı"
        
        # Uzun içerikleri kısalt
        if len(content) > 1000:
            content = content[:1000] + "..."
        
        # HTML özel karakterlerini escape et
        content = content.replace('&', '&amp;')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        
        return content
    
    def _format_meta_info(self, result: Any) -> str:
        """Meta bilgileri formatla"""
        meta_parts = []
        
        if hasattr(result, 'document_type'):
            meta_parts.append(f"<b>Tür:</b> {result.document_type}")
        
        if hasattr(result, 'score'):
            meta_parts.append(f"<b>Skor:</b> {result.score:.3f}")
        
        if hasattr(result, 'match_type'):
            match_type_tr = {
                'keyword': 'Anahtar Kelime',
                'semantic': 'Semantik',
                'mixed': 'Karma'
            }
            match_type = match_type_tr.get(result.match_type, result.match_type)
            meta_parts.append(f"<b>Arama Türü:</b> {match_type}")
        
        if hasattr(result, 'is_repealed') and result.is_repealed:
            meta_parts.append("<b>Durum:</b> Mülga")
        elif hasattr(result, 'is_amended') and result.is_amended:
            meta_parts.append("<b>Durum:</b> Değişiklik var")
        
        return " | ".join(meta_parts)
    
    def _create_footer(self) -> List[Any]:
        """PDF footer oluştur"""
        elements = []
        
        elements.append(Spacer(1, 30))
        
        footer_text = f"""
        <i>Bu rapor Mevzuat Belge Analiz & Sorgulama Sistemi tarafından otomatik olarak oluşturulmuştur.</i><br/>
        <i>Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>
        """
        
        footer_para = Paragraph(footer_text, self.meta_style)
        elements.append(footer_para)
        
        return elements
    
    def export_document_comparison(self, documents: List[Dict], output_path: str) -> Dict[str, Any]:
        """İki belge arasında karşılaştırma raporu oluştur"""
        if not REPORTLAB_AVAILABLE:
            return {
                'success': False,
                'error': 'ReportLab kütüphanesi kurulu değil'
            }
        
        try:
            self.logger.info(f"Belge karşılaştırma raporu oluşturuluyor: {output_path}")
            
            # TODO: Implement document comparison
            # Bu özellik gelecek sürümlerde eklenebilir
            
            return {
                'success': False,
                'error': 'Belge karşılaştırma özelliği henüz uygulanmadı'
            }
            
        except Exception as e:
            self.logger.error(f"Belge karşılaştırma export hatası: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_export_formats(self) -> List[str]:
        """Desteklenen export formatları"""
        formats = ['PDF']
        
        # Gelecekte eklenebilecek formatlar
        # if XLSX_AVAILABLE:
        #     formats.append('Excel')
        # if DOCX_AVAILABLE:
        #     formats.append('Word')
        
        return formats

    def is_available(self) -> bool:
        """PDF export özelliğinin kullanılabilir olup olmadığını kontrol et"""
        return REPORTLAB_AVAILABLE
