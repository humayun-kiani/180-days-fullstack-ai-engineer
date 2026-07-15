# ============================================================
# src/utils/string_tools.py
# String utility functions
# ============================================================

import re
import string
import random


def is_palindrome(text):
    """
    Check if text reads the same forwards and backwards.

    Args:
        text (str): Text to check.

    Returns:
        bool: True if palindrome, False otherwise.

    Example:
        >>> is_palindrome("racecar")
        True
        >>> is_palindrome("hello")
        False
    """
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text).lower()
    return cleaned == cleaned[::-1]


def count_words(text):
    """Count words in a text string."""
    return len(text.split())


def count_vowels(text):
    """Count vowels (a, e, i, o, u) in text."""
    return sum(1 for c in text.lower() if c in "aeiou")


def count_consonants(text):
    """Count consonants in text."""
    return sum(1 for c in text.lower()
               if c.isalpha() and c not in "aeiou")


def truncate(text, max_length=50, suffix="..."):
    """
    Truncate text to max_length characters.

    Args:
        text (str): Text to truncate.
        max_length (int): Maximum character length.
        suffix (str): String to append when truncated.

    Returns:
        str: Truncated string with suffix if needed.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def generate_password(length=12, use_symbols=True):
    """
    Generate a random secure password.

    Args:
        length (int): Length of password.
        use_symbols (bool): Include special characters.

    Returns:
        str: Generated password.
    """
    chars = string.ascii_letters + string.digits
    if use_symbols:
        chars += "!@#$%^&*"

    # Ensure at least one of each required type
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
    ]
    if use_symbols:
        password.append(random.choice("!@#$%^&*"))

    # Fill the rest randomly
    password += random.choices(chars, k=length - len(password))

    # Shuffle to avoid predictable pattern
    random.shuffle(password)
    return "".join(password)


def caesar_cipher(text, shift=3, decode=False):
    """
    Encode or decode text using Caesar cipher.

    Args:
        text (str): Text to encode/decode.
        shift (int): Number of positions to shift.
        decode (bool): If True, decode instead of encode.

    Returns:
        str: Encoded or decoded text.
    """
    if decode:
        shift = -shift

    result = []
    for char in text:
        if char.isalpha():
            base = ord("A") if char.isupper() else ord("a")
            shifted = (ord(char) - base + shift) % 26 + base
            result.append(chr(shifted))
        else:
            result.append(char)
    return "".join(result)


def extract_emails(text):
    """
    Extract all email addresses from text using regex.

    Args:
        text (str): Text to search.

    Returns:
        list: List of found email addresses.
    """
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)


def extract_numbers(text):
    """Extract all numbers from text."""
    return [float(n) for n in re.findall(r"-?\d+\.?\d*", text)]


def word_frequency(text):
    """
    Count frequency of each word in text.

    Returns:
        dict: Word counts sorted by frequency (highest first).
    """
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


if __name__ == "__main__":
    # Quick tests when run directly
    print("String Tools Module")
    print("-" * 30)
    print(f"is_palindrome('racecar'): {is_palindrome('racecar')}")
    print(f"count_vowels('Hello World'): {count_vowels('Hello World')}")
    print(f"truncate('Very long text here', 10): {truncate('Very long text here', 10)}")
    print(f"generate_password(16): {generate_password(16)}")
    print(f"caesar_cipher('Hello'): {caesar_cipher('Hello')}")
    print(f"extract_emails('Contact me@test.com'): {extract_emails('Contact me@test.com or you@site.org')}")