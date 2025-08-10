"""
Faceted Search Engine - Çok boyutlu arama sistemi
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class FacetOption:
    """Facet seçeneği"""
    value: str
    label: str
    count: int
    selected: bool = False

@dataclass 
class Facet:
    """Facet kategorisi"""
    name: str
    label: str
    options: List[FacetOption]
    facet_type: str  # 'single', 'multiple', 'range'
    is_collapsed: bool = False

@dataclass
class FacetedResults:
    """Faceted search sonuçları"""
    documents: List[Any]
    facets: List[Facet]
    total_count: int
    filtered_count: int
    applied_filters: Dict[str, List[str]]

class LegalDocumentFacetEngine:
    """Hukuki belgeler için faceted search motoru"""
    
    def __init__(self, database_manager, config_manager):
        self.db = database_manager
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Facet definitions
        self.facet_definitions = self._load_facet_definitions()
        
    def search_with_facets(self, base_results: List[Any], 
                          selected_facets: Dict[str, List[str]] = None) -> FacetedResults:
        """
        Base search results üzerinde faceted filtering uygula
        
        Args:
            base_results: Temel arama sonuçları
            selected_facets: Seçili facet filtreleri
            
        Returns:
            Faceted search sonuçları
        """
        try:
            if selected_facets is None:
                selected_facets = {}
            
            # Apply facet filters
            filtered_results = self._apply_facet_filters(base_results, selected_facets)
            
            # Calculate facet counts
            facets = self._calculate_facet_counts(base_results, selected_facets)
            
            return FacetedResults(
                documents=filtered_results,
                facets=facets,
                total_count=len(base_results),
                filtered_count=len(filtered_results),
                applied_filters=selected_facets
            )
            
        except Exception as e:
            self.logger.error(f"Faceted search hatası: {e}")
            return FacetedResults(
                documents=base_results,
                facets=[],
                total_count=len(base_results),
                filtered_count=len(base_results),
                applied_filters={}
            )
    
    def _apply_facet_filters(self, results: List[Any], 
                           selected_facets: Dict[str, List[str]]) -> List[Any]:
        """Seçili facetlere göre sonuçları filtrele"""
        
        if not selected_facets:
            return results
        
        filtered_results = []
        
        for result in results:
            include_result = True
            
            # Her facet için kontrol
            for facet_name, selected_values in selected_facets.items():
                if not selected_values:
                    continue
                
                facet_definition = self.facet_definitions.get(facet_name)
                if not facet_definition:
                    continue
                
                # Result'tan facet değerini al
                result_value = self._extract_facet_value(result, facet_definition)
                
                # Filtreleme mantığı
                if facet_definition['type'] == 'single' or facet_definition['type'] == 'multiple':
                    if result_value not in selected_values:
                        include_result = False
                        break
                elif facet_definition['type'] == 'range':
                    if not self._value_in_range(result_value, selected_values):
                        include_result = False
                        break
            
            if include_result:
                filtered_results.append(result)
        
        return filtered_results
    
    def _calculate_facet_counts(self, results: List[Any], 
                               selected_facets: Dict[str, List[str]]) -> List[Facet]:
        """Facet seçeneklerinin sayılarını hesapla"""
        
        facets = []
        
        for facet_name, facet_def in self.facet_definitions.items():
            # Facet değerlerini topla
            value_counts = {}
            
            for result in results:
                facet_value = self._extract_facet_value(result, facet_def)
                
                if facet_value:
                    if facet_def['type'] == 'range':
                        # Range facetler için aralık belirle
                        range_key = self._get_range_key(facet_value, facet_def)
                        value_counts[range_key] = value_counts.get(range_key, 0) + 1
                    else:
                        value_counts[facet_value] = value_counts.get(facet_value, 0) + 1
            
            # Facet options oluştur
            facet_options = []
            selected_values = selected_facets.get(facet_name, [])
            
            # Sort by count (descending) or by predefined order
            if facet_def.get('sort_order'):
                sorted_values = [(v, c) for v, c in value_counts.items() 
                               if v in facet_def['sort_order']]
                sorted_values.sort(key=lambda x: facet_def['sort_order'].index(x[0]))
            else:
                sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
            
            for value, count in sorted_values:
                if count > 0:  # Only show facets with results
                    option = FacetOption(
                        value=value,
                        label=facet_def['labels'].get(value, value),
                        count=count,
                        selected=value in selected_values
                    )
                    facet_options.append(option)
            
            if facet_options:  # Only add facets that have options
                facet = Facet(
                    name=facet_name,
                    label=facet_def['label'],
                    options=facet_options,
                    facet_type=facet_def['type']
                )
                facets.append(facet)
        
        return facets
    
    def _extract_facet_value(self, result: Any, facet_definition: Dict) -> Any:
        """Result'tan facet değerini çıkar"""
        
        field_path = facet_definition['field']
        
        # Result bir dict ise
        if hasattr(result, '__dict__'):
            result_dict = result.__dict__
        elif isinstance(result, dict):
            result_dict = result
        else:
            return None
        
        # Nested field access (örn: "document.type")
        value = result_dict
        for field in field_path.split('.'):
            if isinstance(value, dict) and field in value:
                value = value[field]
            elif hasattr(value, field):
                value = getattr(value, field)
            else:
                return None
        
        # Value transformation
        transform = facet_definition.get('transform')
        if transform:
            value = self._apply_transform(value, transform)
        
        return value
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Value transformation uygula"""
        
        if transform == 'year':
            if isinstance(value, datetime):
                return str(value.year)
            elif isinstance(value, str):
                try:
                    return value[:4]  # YYYY formatı
                except:
                    return None
        
        elif transform == 'month_year':
            if isinstance(value, datetime):
                return f"{value.year}-{value.month:02d}"
        
        elif transform == 'upper':
            return str(value).upper() if value else None
        
        elif transform == 'lower':
            return str(value).lower() if value else None
        
        elif transform == 'normalize_document_type':
            return self._normalize_document_type(value)
        
        return value
    
    def _normalize_document_type(self, doc_type: str) -> str:
        """Belge türünü normalize et"""
        if not doc_type:
            return 'DİĞER'
        
        doc_type = doc_type.upper().strip()
        
        # Common normalizations
        if 'KANUN' in doc_type:
            return 'KANUN'
        elif 'YÖNETMELIK' in doc_type:
            return 'YÖNETMELİK'
        elif 'TÜZÜK' in doc_type:
            return 'TÜZÜK'
        elif 'GENELGE' in doc_type:
            return 'GENELGE'
        elif 'TEBLİĞ' in doc_type:
            return 'TEBLİĞ'
        elif 'KARAR' in doc_type:
            return 'KARAR'
        elif 'DİREKTİF' in doc_type:
            return 'DİREKTİF'
        else:
            return 'DİĞER'
    
    def _get_range_key(self, value: Any, facet_definition: Dict) -> str:
        """Range facet için aralık anahtarı belirle"""
        
        ranges = facet_definition.get('ranges', [])
        
        # Numeric ranges
        if isinstance(value, (int, float)):
            for range_def in ranges:
                if range_def['min'] <= value <= range_def['max']:
                    return range_def['key']
        
        # Date ranges
        elif isinstance(value, datetime):
            for range_def in ranges:
                start_date = datetime.strptime(range_def['start'], '%Y-%m-%d')
                end_date = datetime.strptime(range_def['end'], '%Y-%m-%d')
                if start_date <= value <= end_date:
                    return range_def['key']
        
        return 'DİĞER'
    
    def _value_in_range(self, value: Any, selected_ranges: List[str]) -> bool:
        """Değerin seçili aralıklarda olup olmadığını kontrol et"""
        
        for facet_def in self.facet_definitions.values():
            if facet_def['type'] != 'range':
                continue
            
            for range_def in facet_def.get('ranges', []):
                if range_def['key'] in selected_ranges:
                    range_key = self._get_range_key(value, facet_def)
                    if range_key == range_def['key']:
                        return True
        
        return False
    
    def _load_facet_definitions(self) -> Dict[str, Dict]:
        """Facet tanımlarını yükle"""
        
        return {
            'document_type': {
                'label': 'Belge Türü',
                'field': 'document_type',
                'type': 'multiple',
                'transform': 'normalize_document_type',
                'sort_order': ['KANUN', 'YÖNETMELİK', 'TÜZÜK', 'GENELGE', 'TEBLİĞ', 'KARAR', 'DİĞER'],
                'labels': {
                    'KANUN': 'Kanun',
                    'YÖNETMELİK': 'Yönetmelik',
                    'TÜZÜK': 'Tüzük',
                    'GENELGE': 'Genelge',
                    'TEBLİĞ': 'Tebliğ',
                    'KARAR': 'Karar',
                    'DİREKTİF': 'Direktif',
                    'DİĞER': 'Diğer'
                }
            },
            
            'legal_domain': {
                'label': 'Hukuk Alanı',
                'field': 'legal_domain',
                'type': 'multiple',
                'labels': {
                    'ceza': 'Ceza Hukuku',
                    'medeni': 'Medeni Hukuk',
                    'ticaret': 'Ticaret Hukuku',
                    'vergi': 'Vergi Hukuku',
                    'is': 'İş Hukuku',
                    'idare': 'İdare Hukuku',
                    'anayasa': 'Anayasa Hukuku',
                    'uluslararasi': 'Uluslararası Hukuk'
                }
            },
            
            'publication_year': {
                'label': 'Yayın Yılı',
                'field': 'publication_date',
                'type': 'range',
                'transform': 'year',
                'ranges': [
                    {'key': '2020-2024', 'label': '2020-2024', 'start': '2020-01-01', 'end': '2024-12-31'},
                    {'key': '2015-2019', 'label': '2015-2019', 'start': '2015-01-01', 'end': '2019-12-31'},
                    {'key': '2010-2014', 'label': '2010-2014', 'start': '2010-01-01', 'end': '2014-12-31'},
                    {'key': '2005-2009', 'label': '2005-2009', 'start': '2005-01-01', 'end': '2009-12-31'},
                    {'key': '2000-2004', 'label': '2000-2004', 'start': '2000-01-01', 'end': '2004-12-31'},
                    {'key': 'before-2000', 'label': '2000 Öncesi', 'start': '1900-01-01', 'end': '1999-12-31'}
                ]
            },
            
            'institution': {
                'label': 'Kurumsal Kaynak',
                'field': 'institution',
                'type': 'multiple',
                'labels': {
                    'tbmm': 'TBMM',
                    'cumhurbaskanligi': 'Cumhurbaşkanlığı',
                    'bakanlar_kurulu': 'Bakanlar Kurulu',
                    'danistay': 'Danıştay',
                    'yargitay': 'Yargıtay',
                    'anayasa_mahkemesi': 'Anayasa Mahkemesi',
                    'sayistay': 'Sayıştay',
                    'hsyk': 'HSK',
                    'bakanlık': 'Bakanlıklar',
                    'diger': 'Diğer'
                }
            },
            
            'status': {
                'label': 'Belge Durumu',
                'field': 'status',
                'type': 'multiple',
                'labels': {
                    'active': 'Yürürlükte',
                    'repealed': 'Mülga',
                    'amended': 'Değişiklik Geçirmiş',
                    'suspended': 'Askıya Alınmış',
                    'draft': 'Taslak'
                }
            },
            
            'content_length': {
                'label': 'İçerik Uzunluğu',
                'field': 'content_length',
                'type': 'range',
                'ranges': [
                    {'key': 'short', 'label': 'Kısa (< 1000 karakter)', 'min': 0, 'max': 999},
                    {'key': 'medium', 'label': 'Orta (1000-5000 karakter)', 'min': 1000, 'max': 4999},
                    {'key': 'long', 'label': 'Uzun (5000+ karakter)', 'min': 5000, 'max': float('inf')}
                ]
            }
        }
    
    def get_facet_suggestions(self, facet_name: str, partial_value: str, 
                            limit: int = 10) -> List[FacetOption]:
        """Facet değeri için önerileri al"""
        try:
            facet_def = self.facet_definitions.get(facet_name)
            if not facet_def:
                return []
            
            # Database'den değerleri al
            cursor = self.db.connection.cursor()
            
            field_path = facet_def['field']
            
            # Simple field access için SQL sorgusu
            if '.' not in field_path:
                cursor.execute(f"""
                    SELECT DISTINCT {field_path}, COUNT(*) as count
                    FROM articles a
                    JOIN documents d ON a.document_id = d.id
                    WHERE LOWER({field_path}) LIKE LOWER(?)
                    GROUP BY {field_path}
                    ORDER BY count DESC
                    LIMIT ?
                """, (f"%{partial_value}%", limit))
                
                results = cursor.fetchall()
                cursor.close()
                
                suggestions = []
                for value, count in results:
                    if value:
                        transformed_value = self._apply_transform(
                            value, facet_def.get('transform')
                        )
                        
                        suggestion = FacetOption(
                            value=str(transformed_value),
                            label=facet_def['labels'].get(str(transformed_value), str(transformed_value)),
                            count=count
                        )
                        suggestions.append(suggestion)
                
                return suggestions
            
            return []
            
        except Exception as e:
            self.logger.error(f"Facet öneri hatası: {e}")
            return []
    
    def export_facet_state(self, faceted_results: FacetedResults) -> Dict[str, Any]:
        """Facet durumunu export et (URL parametreleri için)"""
        
        export_data = {
            'applied_filters': faceted_results.applied_filters,
            'total_count': faceted_results.total_count,
            'filtered_count': faceted_results.filtered_count,
            'facet_counts': {}
        }
        
        for facet in faceted_results.facets:
            export_data['facet_counts'][facet.name] = {
                option.value: option.count 
                for option in facet.options
            }
        
        return export_data
    
    def import_facet_state(self, export_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Export edilen facet durumunu import et"""
        
        return export_data.get('applied_filters', {})
