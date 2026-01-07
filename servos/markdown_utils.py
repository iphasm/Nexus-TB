"""
Markdown utilities for safe Telegram message formatting
"""

import re
from typing import Dict, Any

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown parsing.

    Telegram Markdown has issues with certain characters, especially:
    - Asterisks (*) - used for bold
    - Underscores (_) - used for italic
    - Backticks (`) - used for code
    - Square brackets ([ ]) - used for links
    - Parentheses ( ) - used in links
    - Pipes (|) - used in tables
    """
    if not text:
        return ""

    # Convert to string if not already
    text = str(text)

    # Characters that need to be escaped in Markdown
    escape_chars = ['*', '_', '`', '[', ']', '(', ')', '|']

    # Escape each special character
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")

    return text

def sanitize_signal_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize signal metadata to prevent Markdown parsing errors.

    This is critical for the 'reason' field in trading signals.
    """
    if not metadata:
        return {}

    sanitized = {}
    for key, value in metadata.items():
        # Skip 'strategy' key as it's handled separately
        if key.lower() == 'strategy':
            sanitized[key] = value
            continue

        if isinstance(value, float):
            # Smart formatting for floats:
            # - Large numbers (>1): 2 decimals
            # - Small numbers (<1): 4-5 decimals depending on zeros
            abs_val = abs(value)
            if abs_val == 0:
                str_value = "0.00"
            elif abs_val >= 1:
                str_value = f"{value:.2f}"
            elif abs_val >= 0.0001:
                str_value = f"{value:.4f}"
            else:
                str_value = f"{value:.6f}"
            
            # Remove trailing zeros for cleanliness
            if '.' in str_value:
               str_value = str_value.rstrip('0').rstrip('.')
            
            sanitized[key] = str_value
            continue
            
        # Convert value to string and escape
        str_value = str(value)

        # Handle special TREND values with emojis (these are safe)
        if key.upper() == 'TREND':
            if str_value.upper() == 'UP':
                sanitized[key] = "UP 🐂"
            elif str_value.upper() == 'DOWN':
                sanitized[key] = "DOWN 🐻"
            else:
                sanitized[key] = escape_markdown(str_value)
        else:
            # Escape all other values
            sanitized[key] = escape_markdown(str_value)
            
    return sanitized

def safe_format_number(value: float, decimals: int = 2) -> str:
    """
    Safely format numbers for Markdown, avoiding comma separators that can cause issues.
    """
    if value is None:
        return "N/A"

    try:
        # Always use dot as decimal separator and no thousands separator to avoid Markdown issues
        formatted = f"{value:.{decimals}f}"
        # Remove any commas that might have been added by locale formatting
        return formatted.replace(',', '')
    except (ValueError, TypeError):
        return escape_markdown(str(value))

def create_safe_reason(strategy: str, confidence: float, metadata: Dict[str, Any]) -> str:
    """
    Create a safe reason string for trading signals, properly escaped for Markdown.
    """
    # Sanitize metadata first
    safe_metadata = sanitize_signal_metadata(metadata)

    # Build meta parameters
    meta_params = []
    for k, v in safe_metadata.items():
        if k.lower() == 'strategy':
            continue

        if isinstance(v, float):
            # Use safe number formatting
            meta_params.append(f"{escape_markdown(k.upper())}: {safe_format_number(v, 1)}")
        else:
            meta_params.append(f"{escape_markdown(k.upper())}: {v}")

    params_str = " | ".join(meta_params)
    reason = f"[{escape_markdown(strategy)} | Conf: {confidence:.0%} | {params_str}]"

    return reason

def safe_format_template(template: str, **kwargs) -> str:
    """
    Safely format a template string with Markdown escaping.
    """
    # Escape all string values in kwargs
    safe_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            safe_kwargs[key] = escape_markdown(value)
        elif isinstance(value, float):
            safe_kwargs[key] = safe_format_number(value)
        else:
            safe_kwargs[key] = escape_markdown(str(value))

    try:
        return template.format(**safe_kwargs)
    except (KeyError, ValueError) as e:
        # If formatting fails, return a safe fallback
        return f"Error formatting message: {escape_markdown(str(e))}"
