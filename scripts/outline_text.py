"""Visible text for the inline syntax supported by the outline renderer."""
import html
import re


def rendered_inline(text):
    """Remove formatting delimiters, preserving literal operators and symbols."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return html.unescape(text)
