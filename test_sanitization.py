#!/usr/bin/env python3
"""
Test the error sanitization for Markdown compatibility
"""

def sanitize_error_for_markdown(error: str) -> str:
    """Sanitize error messages containing JSON for safe Markdown display."""
    return (str(error)
            .replace('{', '[')
            .replace('}', ']')
            .replace('"', "'")
            .replace('\\', '/'))

if __name__ == '__main__':
    # Test cases
    test_cases = [
        'Normal error message',
        'SL: {"retCode":110093,"retMsg":"expect Falling, but trigger_price[14922000] >= current[14917000]??LastPrice"}',
        'TP: {"code": -2021, "msg": "Order would immediately trigger"}',
        'Error with \\backslashes\\ and "quotes"',
        'Mixed: {"key": "value"} and normal text',
    ]

    print("Testing error sanitization for Telegram Markdown compatibility:")
    print("=" * 70)

    for i, test_error in enumerate(test_cases, 1):
        sanitized = sanitize_error_for_markdown(test_error)
        has_braces = '{' in sanitized or '}' in sanitized
        has_quotes = '"' in sanitized

        print(f"\nTest {i}:")
        print(f"  Original: {test_error}")
        print(f"  Sanitized: {sanitized}")
        print(f"  Contains braces: {has_braces} | Contains quotes: {has_quotes}")

        if has_braces or has_quotes:
            print("  ❌ STILL UNSAFE FOR MARKDOWN")
        else:
            print("  ✅ SAFE FOR MARKDOWN")




