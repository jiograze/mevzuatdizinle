#!/usr/bin/env python
import xml.etree.ElementTree as ET

try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    
    line_rate = float(root.attrib.get('line-rate', '0'))
    branch_rate = float(root.attrib.get('branch-rate', '0'))
    
    print(f"📊 Current Test Coverage Status:")
    print(f"   • Line Coverage: {line_rate:.1%}")
    print(f"   • Branch Coverage: {branch_rate:.1%}")
    
    # Package breakdown
    packages = root.findall('packages/package')
    print(f"\n📋 Package Coverage Details:")
    
    for pkg in packages:
        pkg_name = pkg.attrib.get('name', 'Unknown')
        pkg_line_rate = float(pkg.attrib.get('line-rate', '0'))
        print(f"   • {pkg_name}: {pkg_line_rate:.1%}")
        
    # Overall assessment
    if line_rate >= 0.70:
        print(f"\n✅ SUCCESS: {line_rate:.1%} coverage - Target %70+ ACHIEVED!")
    elif line_rate >= 0.40:
        print(f"\n⚠️  PROGRESS: {line_rate:.1%} coverage - Need {0.70-line_rate:.1%} more for target")
    else:
        print(f"\n❌ BELOW TARGET: {line_rate:.1%} coverage - Need {0.70-line_rate:.1%} more for %70 target")
        
except Exception as e:
    print(f"Coverage raporu okunamadı: {e}")
