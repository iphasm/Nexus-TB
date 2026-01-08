#!/usr/bin/env python3
"""
Diagnóstico para error de parsing Markdown en Telegram
Error: "can't parse entities: Can't find end of the entity starting at byte offset 478"
"""

import re

def check_markdown_entities(text):
    """Check for unclosed Markdown entities"""
    issues = []

    # Check for unclosed bold/italic
    bold_count = text.count('**')
    italic_count = text.count('*') - bold_count * 2  # Bold uses 2 asterisks

    if bold_count % 2 != 0:
        issues.append(f'Unclosed bold: {bold_count} ** found')
    if italic_count % 2 != 0:
        issues.append(f'Unclosed italic: {italic_count} * found (excluding bold)')

    # Check for unclosed code blocks
    backtick_count = text.count('`')
    if backtick_count % 2 != 0:
        issues.append(f'Unclosed inline code: {backtick_count} ` found')

    # Check for problematic characters around offset 478
    if len(text) > 478:
        char_478 = text[477]  # 0-indexed
        context_start = max(0, 470)
        context_end = min(len(text), 490)
        context = text[context_start:context_end]
        issues.append(f'Character at offset 478: "{char_478}" (ord: {ord(char_478)})')
        issues.append(f'Context around 478: "{context}"')

    # Check for JSON-like content that might break Markdown
    json_pattern = r'\{[^}]*\}|\[[^\]]*\]'
    json_matches = re.findall(json_pattern, text)
    if json_matches:
        issues.append(f'Found JSON-like content: {len(json_matches)} matches')
        for i, match in enumerate(json_matches[:3]):  # Show first 3
            issues.append(f'  JSON {i+1}: {match[:100]}...')

    # Check for special characters that might cause issues
    special_chars = ['{', '}', '[', ']', '(', ')', '*', '`', '_']
    for char in special_chars:
        if char in text:
            first_pos = text.find(char)
            issues.append(f'Special char "{char}" found at position {first_pos}')

    return issues

def test_problematic_messages():
    """Test known problematic message patterns"""

    # Test 1: Error message with JSON
    test1 = '''❌ Effector Error: {"error": "ORDER_WOULD_IMMEDIATELY_TRIGGER", "code": -2021, "msg": "Order would immediately trigger. Check stopPrice."}'''
    print('=== TEST 1: Error message with JSON ===')
    print(f'Message length: {len(test1)}')
    issues1 = check_markdown_entities(test1)
    for issue in issues1:
        print(f'  {issue}')
    print()

    # Test 2: Message with nested quotes and special chars
    test2 = '''🛡️ **Protección:** Binance: SL=True, TP=True, Trailing=False | Errors: ['SL: {"retCode":110093,"retMsg":"expect Falling, but trigger_price[14922000] >= current[14917000]??LastPrice"}']'''
    print('=== TEST 2: Protection message with nested JSON ===')
    print(f'Message length: {len(test2)}')
    issues2 = check_markdown_entities(test2)
    for issue in issues2:
        print(f'  {issue}')
    print()

    # Test 3: Long message that might reach offset 478
    test3 = '''🔄 **Reporte de Sincronización:**

✅ BTCUSDT (LONG) ✅
   SL: 43,250.00 (2.00%) | TP: 45,000.00
   TS Act: 43,500.00 (Entry)

✅ ETHUSDT (LONG) ✅
   SL: 2,650.00 (1.50%) | TP: 2,800.00
   TS Act: 2,700.00 (Entry)

⚠️ ADAUSDT (LONG) ⚠️
   SL: 0.4250 (2.50%) | TP: 0.4500
   TS Act: 0.4350 (Entry)
   Err: SL verification failed - order not found in open orders

Total synchronized: 3 positions'''
    print('=== TEST 3: Long sync report ===')
    print(f'Message length: {len(test3)}')
    issues3 = check_markdown_entities(test3)
    for issue in issues3:
        print(f'  {issue}')
    print()

if __name__ == '__main__':
    test_problematic_messages()




