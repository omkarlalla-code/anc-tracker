#!/usr/bin/env python3
"""
Phone/name encryption and decryption using pysodium (libsodium secretbox).

Key management:
  - Generate once:   python3 core/crypto.py generate-key
  - Store result in: .env as TRACKER_ENCRYPTION_KEY=<hex>
  - check_reminders.sh sources .env so the key is available at cron runtime

Blob format stored in SQLite:
  hex( nonce[24 bytes] + ciphertext ) as TEXT

Usage:
  python3 core/crypto.py generate-key
  python3 core/crypto.py encrypt "+91XXXXXXXXXX"
  python3 core/crypto.py decrypt "<hex blob>"
"""

import sys
import os
import binascii
import pysodium


def _get_key() -> bytes:
    hex_key = os.environ.get('TRACKER_ENCRYPTION_KEY')
    if not hex_key:
        raise RuntimeError("TRACKER_ENCRYPTION_KEY is not set. Source .env before running.")
    key = binascii.unhexlify(hex_key.strip())
    if len(key) != pysodium.crypto_secretbox_KEYBYTES:
        raise RuntimeError(
            f"Key must be {pysodium.crypto_secretbox_KEYBYTES} bytes "
            f"({pysodium.crypto_secretbox_KEYBYTES * 2} hex chars)"
        )
    return key


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns hex-encoded nonce+ciphertext."""
    key = _get_key()
    nonce = pysodium.randombytes(pysodium.crypto_secretbox_NONCEBYTES)
    ciphertext = pysodium.crypto_secretbox(plaintext.encode('utf-8'), nonce, key)
    return binascii.hexlify(nonce + ciphertext).decode('ascii')


def decrypt(hex_blob: str) -> str:
    """Decrypt a hex-encoded nonce+ciphertext blob. Returns plaintext string."""
    key = _get_key()
    raw = binascii.unhexlify(hex_blob.strip())
    nonce = raw[:pysodium.crypto_secretbox_NONCEBYTES]
    ciphertext = raw[pysodium.crypto_secretbox_NONCEBYTES:]
    plaintext = pysodium.crypto_secretbox_open(ciphertext, nonce, key)
    return plaintext.decode('utf-8')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'generate-key':
        key = pysodium.randombytes(pysodium.crypto_secretbox_KEYBYTES)
        print(binascii.hexlify(key).decode('ascii'))

    elif cmd == 'encrypt':
        value = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read().strip()
        print(encrypt(value))

    elif cmd == 'decrypt':
        value = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read().strip()
        print(decrypt(value))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
