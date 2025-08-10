"""
Query Expansion Engine - Turkish Legal Text için Akıllı Sorgu Genişletme
"""

import json
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class ExpandedQuery:
    """Genişletilmiş sorgu veri yapısı"""
    original: str
    expanded_terms: List[str]
    synonyms: List[str]
    semantic_similar: List[str]
    weights: Dict[str, float]
    legal_context: Optional[str] = None

class TurkishLegalQueryExpansion:
    """Türkçe hukuki metinler için sorgu genişletme motoru"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Hukuki terimler sözlüğü
        self.legal_synonyms = self._load_legal_synonyms()
        self.legal_abbreviations = self._load_legal_abbreviations()
        self.context_mapping = self._load_context_mapping()
        
        # Stopwords ve yaygın terimler
        self.turkish_stopwords = self._load_turkish_stopwords()
        self.legal_stopwords = self._load_legal_stopwords()
        
        # Genişletme ağırlıkları
        self.synonym_weight = config_manager.get('query_expansion.synonym_weight', 0.8)
        self.abbreviation_weight = config_manager.get('query_expansion.abbreviation_weight', 0.9)
        self.context_weight = config_manager.get('query_expansion.context_weight', 0.6)
        
    def expand_query(self, original_query: str, context: str = None) -> ExpandedQuery:
        """
        Sorguyu akıllıca genişletir
        
        Args:
            original_query: Orijinal arama sorgusu
            context: Arama bağlamı (opsiyonel)
            
        Returns:
            Genişletilmiş sorgu objesi
        """
        try:
            # Query'yi normalize et
            normalized_query = self._normalize_query(original_query)
            
            # Terimlere ayır
            terms = self._extract_terms(normalized_query)
            
            # Çeşitli genişletme yöntemlerini uygula
            expanded_terms = []
            synonyms = []
            semantic_similar = []
            weights = {}
            
            for term in terms:
                # Eş anlamlı terimler
                term_synonyms = self._find_synonyms(term)
                synonyms.extend(term_synonyms)
                
                # Kısaltmalar
                abbreviations = self._expand_abbreviations(term)
                expanded_terms.extend(abbreviations)
                
                # Yasal bağlam terimleri
                context_terms = self._find_context_terms(term, context)
                expanded_terms.extend(context_terms)
                
                # Ağırlıkları hesapla
                weights[term] = 1.0
                for syn in term_synonyms:
                    weights[syn] = self.synonym_weight
                for abbr in abbreviations:
                    weights[abbr] = self.abbreviation_weight
                for ctx in context_terms:
                    weights[ctx] = self.context_weight
            
            # Tekrarları kaldır
            expanded_terms = list(set(expanded_terms))
            synonyms = list(set(synonyms))
            
            # Yasal bağlamı tespit et
            legal_context = self._detect_legal_context(original_query, terms)
            
            return ExpandedQuery(
                original=original_query,
                expanded_terms=expanded_terms,
                synonyms=synonyms,
                semantic_similar=semantic_similar,
                weights=weights,
                legal_context=legal_context
            )
            
        except Exception as e:
            self.logger.error(f"Query expansion hatası: {e}")
            return ExpandedQuery(
                original=original_query,
                expanded_terms=[],
                synonyms=[],
                semantic_similar=[],
                weights={original_query: 1.0}
            )
    
    def _normalize_query(self, query: str) -> str:
        """Query'yi normalize et"""
        # Türkçe karakterleri koru
        query = query.strip().lower()
        
        # Gereksiz boşlukları temizle
        query = re.sub(r'\s+', ' ', query)
        
        # Özel karakterleri temizle (yasal terimleri koru)
        query = re.sub(r'[^\w\s\-/.]', ' ', query)
        
        return query
    
    def _extract_terms(self, query: str) -> List[str]:
        """Query'den anlamlı terimleri çıkar"""
        # Stopwords'leri filtrele
        terms = []
        words = query.split()
        
        for word in words:
            if (word not in self.turkish_stopwords and 
                word not in self.legal_stopwords and 
                len(word) > 2):
                terms.append(word)
        
        # Çok kelimeli terimleri de dahil et
        compound_terms = self._find_compound_terms(query)
        terms.extend(compound_terms)
        
        return terms
    
    def _find_synonyms(self, term: str) -> List[str]:
        """Terim için eş anlamlıları bul"""
        synonyms = []
        
        # Direkt eşleşme
        if term in self.legal_synonyms:
            synonyms.extend(self.legal_synonyms[term])
        
        # Fuzzy matching için benzer terimler
        for key, values in self.legal_synonyms.items():
            if self._is_similar_term(term, key):
                synonyms.extend(values)
                break
        
        return synonyms
    
    def _expand_abbreviations(self, term: str) -> List[str]:
        """Kısaltmaları genişlet"""
        expanded = []
        
        # Kısaltma → Tam form
        if term.upper() in self.legal_abbreviations:
            expanded.append(self.legal_abbreviations[term.upper()])
        
        # Tam form → Kısaltma
        for abbr, full_form in self.legal_abbreviations.items():
            if term.lower() in full_form.lower():
                expanded.append(abbr.lower())
        
        return expanded
    
    def _find_context_terms(self, term: str, context: str = None) -> List[str]:
        """Bağlam bazlı terimleri bul"""
        context_terms = []
        
        # Yasal alan bazlı terimler
        if term in self.context_mapping:
            legal_area = self.context_mapping[term]
            
            # Aynı yasal alanda bulunan diğer terimleri ekle
            for other_term, other_area in self.context_mapping.items():
                if other_area == legal_area and other_term != term:
                    context_terms.append(other_term)
                    if len(context_terms) >= 3:  # Limit
                        break
        
        return context_terms
    
    def _find_compound_terms(self, query: str) -> List[str]:
        """Çok kelimeli yasal terimleri bul"""
        compound_terms = []
        
        # Yaygın yasal terim kalıpları
        compound_patterns = [
            r'(\w+)\s+(kanunu?)',
            r'(\w+)\s+(yönetmeliği?)',
            r'(\w+)\s+(tüzüğü?)',
            r'(\w+)\s+(genelgesi?)',
            r'(\w+)\s+(tebliği?)',
            r'(\w+)\s+(kararı?)',
        ]
        
        for pattern in compound_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                compound_terms.append(match.group().lower())
        
        return compound_terms
    
    def _detect_legal_context(self, query: str, terms: List[str]) -> Optional[str]:
        """Yasal bağlamı tespit et"""
        context_indicators = {
            'ceza': ['ceza', 'suç', 'mahkumiyet', 'hapis', 'para cezası'],
            'medeni': ['medeni', 'evlilik', 'boşanma', 'miras', 'aile'],
            'ticaret': ['ticaret', 'şirket', 'anonim', 'limited', 'ortaklık'],
            'vergi': ['vergi', 'gelir', 'stopaj', 'kdv', 'özel tüketim'],
            'idare': ['idari', 'belediye', 'valilik', 'kamu', 'devlet'],
            'iş': ['işçi', 'işveren', 'çalışma', 'sendika', 'ücret'],
        }
        
        query_lower = query.lower()
        scores = {}
        
        for context, indicators in context_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in query_lower:
                    score += 1
            
            # Terimlerde de ara
            for term in terms:
                if term in indicators:
                    score += 1
            
            if score > 0:
                scores[context] = score
        
        # En yüksek puanlı bağlamı döndür
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def _is_similar_term(self, term1: str, term2: str, threshold: float = 0.8) -> bool:
        """İki terimin benzerliğini kontrol et"""
        # Basit Levenshtein distance based similarity
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein_distance(term1, term2)
        max_len = max(len(term1), len(term2))
        
        if max_len == 0:
            return True
        
        similarity = 1 - (distance / max_len)
        return similarity >= threshold
    
    def _load_legal_synonyms(self) -> Dict[str, List[str]]:
        """Hukuki eş anlamlılar sözlüğünü yükle"""
        return {
            'kanun': ['yasa', 'mevzuat', 'düzenleme', 'hüküm'],
            'madde': ['bent', 'fıkra', 'paragraf', 'bölüm'],
            'yönetmelik': ['tüzük', 'nizamname', 'talimat'],
            'mahkeme': ['adliye', 'hâkim', 'yargı', 'dava'],
            'ceza': ['müeyyide', 'yaptırım', 'hapis', 'para cezası'],
            'sözleşme': ['mukavele', 'kontrat', 'anlaşma', 'protokol'],
            'taraf': ['kişi', 'şahıs', 'gerçek kişi', 'tüzel kişi'],
            'hak': ['yetki', 'salahiyet', 'imtiyaz', 'ayrıcalık'],
            'yükümlülük': ['sorumluluk', 'vecibe', 'borç', 'mükellefiye'],
            'iptal': ['fesih', 'kaldırma', 'lağvetme', 'ref'],
            'temyiz': ['itiraz', 'başvuru', 'şikâyet', 'dava'],
            'icra': ['infaz', 'uygulama', 'tatbik', 'yürütme'],
            'miras': ['veraset', 'tereke', 'vefat', 'intikal'],
            'evlilik': ['nikâh', 'izdivac', 'birliktelik', 'aile'],
            'boşanma': ['ayrılık', 'fesh-i nikâh', 'talak', 'tefrik'],
            'çocuk': ['küçük', 'reşit olmayan', 'vesayet', 'velaye'],
            'mülkiyet': ['sahiplik', 'tasarruf', 'zilyetlik', 'hak'],
            'kira': ['icara', 'kiralama', 'istisna', 'ecr'],
            'satış': ['bey', 'devir', 'temlik', 'satım'],
            'borç': ['deyn', 'zimmet', 'yükümlülük', 'taahhüt'],
            'alacak': ['hak', 'istihkak', 'talep', 'dava'],
            'faiz': ['kâr', 'ribâ', 'getiri', 'nema'],
            'tazminat': ['zarar', 'ziyan', 'tenfiz', 'telafi'],
            'vergi': ['resim', 'harç', 'gümrük', 'bac'],
            'beyan': ['bildirim', 'ihbar', 'duyuru', 'tebliğ'],
            'denetim': ['kontrol', 'teftiş', 'murakabe', 'inceleme'],
            'cezai': ['adli', 'yargısal', 'muhakeme', 'takibat']
        }
    
    def _load_legal_abbreviations(self) -> Dict[str, str]:
        """Hukuki kısaltmalar sözlüğünü yükle"""
        return {
            'TCK': 'Türk Ceza Kanunu',
            'TMK': 'Türk Medeni Kanunu',
            'TBK': 'Türk Borçlar Kanunu',
            'TTK': 'Türk Ticaret Kanunu',
            'İK': 'İş Kanunu',
            'VUK': 'Vergi Usul Kanunu',
            'GVK': 'Gelir Vergisi Kanunu',
            'AATUHK': 'Amme Alacaklarının Tahsil Usulü Hakkında Kanun',
            'CMK': 'Ceza Muhakemesi Kanunu',
            'HMK': 'Hukuk Muhakemesi Kanunu',
            'İİK': 'İcra ve İflas Kanunu',
            'HUMK': 'Hukuk Usulü Muhakemeleri Kanunu',
            'SSGSSK': 'Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu',
            'KVKK': 'Kişisel Verilerin Korunması Kanunu',
            'MGTK': 'Milli Güvenlik ve Terörle Mücadele',
            'HSYK': 'Hâkimler ve Savcılar Yüksek Kurulu',
            'TBMM': 'Türkiye Büyük Millet Meclisi',
            'AYM': 'Anayasa Mahkemesi',
            'YDKK': 'Yükseköğretim Kalite Kurulu'
        }
    
    def _load_context_mapping(self) -> Dict[str, str]:
        """Terim → hukuk alanı mapping'i"""
        return {
            # Ceza Hukuku
            'suç': 'ceza', 'ceza': 'ceza', 'hapis': 'ceza', 'mahkumiyet': 'ceza',
            'beraat': 'ceza', 'savcı': 'ceza', 'sanık': 'ceza', 'mağdur': 'ceza',
            
            # Medeni Hukuk
            'evlilik': 'medeni', 'boşanma': 'medeni', 'miras': 'medeni', 
            'vesayet': 'medeni', 'aile': 'medeni', 'çocuk': 'medeni',
            
            # Ticaret Hukuku
            'şirket': 'ticaret', 'anonim': 'ticaret', 'limited': 'ticaret',
            'ortaklık': 'ticaret', 'ticaret': 'ticaret', 'tacir': 'ticaret',
            
            # Vergi Hukuku
            'vergi': 'vergi', 'beyan': 'vergi', 'matrah': 'vergi',
            'stopaj': 'vergi', 'kdv': 'vergi', 'ötv': 'vergi',
            
            # İş Hukuku
            'işçi': 'is', 'işveren': 'is', 'çalışma': 'is',
            'sendika': 'is', 'ücret': 'is', 'işsizlik': 'is',
            
            # İdare Hukuku
            'idare': 'idare', 'belediye': 'idare', 'valilik': 'idare',
            'kamu': 'idare', 'memur': 'idare', 'devlet': 'idare'
        }
    
    def _load_turkish_stopwords(self) -> Set[str]:
        """Türkçe stop words"""
        return {
            'bir', 'bu', 'şu', 've', 'veya', 'ile', 'için', 'den', 'dan', 'de', 'da',
            'nin', 'nın', 'nun', 'nün', 'in', 'ın', 'un', 'ün', 'a', 'e', 'i', 'ı',
            'o', 'ö', 'u', 'ü', 'ya', 'ye', 'den', 'ten', 'ne', 'ki', 'mi', 'mı',
            'mu', 'mü', 'dı', 'di', 'du', 'dü', 'tı', 'ti', 'tu', 'tü', 'la', 'le',
            'ta', 'te', 'sa', 'se', 'ca', 'ce', 'na', 'ne'
        }
    
    def _load_legal_stopwords(self) -> Set[str]:
        """Hukuki stopwords (çok yaygın terimler)"""
        return {
            'hakkında', 'ilişkin', 'dair', 'göre', 'uygun', 'karşı', 'aykırı',
            'usul', 'esasa', 'şekil', 'husus', 'mevzu', 'konu', 'alan'
        }

class LegalQueryOptimizer:
    """Hukuki sorgu optimizasyon motoru"""
    
    def __init__(self, query_expansion: TurkishLegalQueryExpansion):
        self.expansion_engine = query_expansion
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def optimize_for_search(self, query: str, search_type: str = 'mixed') -> Dict[str, any]:
        """
        Arama türüne göre optimize edilmiş sorgu oluştur
        
        Args:
            query: Orijinal sorgu
            search_type: 'keyword', 'semantic', 'mixed'
            
        Returns:
            Optimize edilmiş arama parametreleri
        """
        expanded_query = self.expansion_engine.expand_query(query)
        
        if search_type == 'keyword':
            return self._optimize_for_keyword_search(expanded_query)
        elif search_type == 'semantic':
            return self._optimize_for_semantic_search(expanded_query)
        else:  # mixed
            return self._optimize_for_mixed_search(expanded_query)
    
    def _optimize_for_keyword_search(self, expanded_query: ExpandedQuery) -> Dict[str, any]:
        """Keyword arama için optimizasyon"""
        # FTS için boolean sorgusu oluştur
        terms = [expanded_query.original] + expanded_query.synonyms + expanded_query.expanded_terms
        
        # Ağırlıklara göre sırala
        weighted_terms = sorted(terms, key=lambda t: expanded_query.weights.get(t, 0.5), reverse=True)
        
        # FTS boolean sorgusu
        main_terms = weighted_terms[:3]  # En önemli 3 terim
        optional_terms = weighted_terms[3:8]  # İsteğe bağlı 5 terim
        
        fts_query = ' AND '.join(f'"{term}"*' for term in main_terms)
        if optional_terms:
            fts_query += ' OR ' + ' OR '.join(f'"{term}"*' for term in optional_terms)
        
        return {
            'fts_query': fts_query,
            'boost_terms': main_terms,
            'weights': expanded_query.weights,
            'legal_context': expanded_query.legal_context
        }
    
    def _optimize_for_semantic_search(self, expanded_query: ExpandedQuery) -> Dict[str, any]:
        """Semantic arama için optimizasyon"""
        # Semantic arama için genişletilmiş metni oluştur
        all_terms = ([expanded_query.original] + 
                    expanded_query.synonyms + 
                    expanded_query.expanded_terms)
        
        # Context-aware query oluştur
        semantic_query = expanded_query.original
        if expanded_query.legal_context:
            semantic_query += f" {expanded_query.legal_context} hukuku"
        
        # En ağırlıklı terimleri ekle
        top_terms = sorted(all_terms, 
                          key=lambda t: expanded_query.weights.get(t, 0.5), 
                          reverse=True)[:5]
        
        semantic_query += ' ' + ' '.join(top_terms)
        
        return {
            'semantic_query': semantic_query,
            'context_boost': expanded_query.legal_context,
            'similarity_threshold': 0.7,
            'weights': expanded_query.weights
        }
    
    def _optimize_for_mixed_search(self, expanded_query: ExpandedQuery) -> Dict[str, any]:
        """Mixed arama için optimizasyon"""
        keyword_opts = self._optimize_for_keyword_search(expanded_query)
        semantic_opts = self._optimize_for_semantic_search(expanded_query)
        
        return {
            'keyword': keyword_opts,
            'semantic': semantic_opts,
            'fusion_weights': {
                'keyword': 0.6,
                'semantic': 0.4
            },
            'legal_context': expanded_query.legal_context,
            'expanded_query': expanded_query
        }
