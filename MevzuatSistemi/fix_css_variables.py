#!/usr/bin/env python3
"""
CSS değişkenlerini PyQt5 uyumlu değerlerle değiştir
"""

import os
import re

# Design tokens - design_system.py'den alınan değerler
CSS_VARIABLES = {
    '--color-primary': '#1976D2',
    '--color-primary-variant': '#1565C0',
    '--color-secondary': '#DC004E',
    '--color-secondary-variant': '#C51162',
    '--color-success': '#388E3C',
    '--color-warning': '#F57C00',
    '--color-error': '#D32F2F',
    '--color-info': '#1976D2',
    '--color-surface': '#FFFFFF',
    '--color-background': '#FAFAFA',
    '--color-card-background': '#FFFFFF',
    '--color-text-primary': '#212121',
    '--color-text-secondary': '#757575',
    '--color-text-disabled': '#BDBDBD',
    '--color-text-hint': '#9E9E9E',
    '--color-border-light': '#E0E0E0',
    '--color-border-medium': '#BDBDBD',
    '--color-border-dark': '#757575',
    '--spacing-xs': '4px',
    '--spacing-sm': '8px',
    '--spacing-md': '16px',
    '--spacing-lg': '24px',
    '--spacing-xl': '32px',
    '--spacing-xxl': '48px',
    '--border-radius-sm': '4px',
    '--border-radius-md': '8px',
    '--border-radius-lg': '12px',
    '--border-radius-xl': '16px',
    '--elevation-1': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
    '--elevation-2': '0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)',
    '--elevation-3': '0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)',
    '--elevation-4': '0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22)',
    '--font-family-primary': 'Segoe UI',
    '--font-family-secondary': 'Roboto',
    '--font-family-monospace': 'Consolas',
    '--font-size-caption': '10px',
    '--font-size-small': '12px',
    '--font-size-body': '14px',
    '--font-size-subtitle': '16px',
    '--font-size-title': '20px',
    '--font-size-headline': '24px',
    '--font-weight-light': '300',
    '--font-weight-normal': '400',
    '--font-weight-medium': '500',
    '--font-weight-semibold': '600',
    '--font-weight-bold': '700',
    '--animation-fast': '150ms',
    '--animation-normal': '300ms',
    '--animation-slow': '500ms',
}

def replace_css_variables_in_file(filepath):
    """Bir dosyadaki CSS değişkenlerini değiştir"""
    print(f"İşleniyor: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # var(--variable) pattern'lerini değiştir
        for var_name, value in CSS_VARIABLES.items():
            pattern = f'var\\({re.escape(var_name)}\\)'
            content = re.sub(pattern, value, content)
        
        # String değişkenlerini de kontrol et (Python string'lerinde)
        for var_name, value in CSS_VARIABLES.items():
            pattern = f'"var\\({re.escape(var_name)}\\)"'
            replacement = f'"{value}"'
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Güncellendi: {filepath}")
            return True
        else:
            print(f"⏭️ Değişiklik yok: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Hata: {filepath} - {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    base_path = "app/ui/modern"
    
    files_to_process = [
        "components.py",
        "theme_manager.py",
        "design_system.py"
    ]
    
    total_updated = 0
    
    for filename in files_to_process:
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            if replace_css_variables_in_file(filepath):
                total_updated += 1
        else:
            print(f"❌ Dosya bulunamadı: {filepath}")
    
    print(f"\n🎉 İşlem tamamlandı! {total_updated} dosya güncellendi.")

if __name__ == "__main__":
    main()
