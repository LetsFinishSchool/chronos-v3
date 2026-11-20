#!/usr/bin/env python3
"""Erzeugt ein VAPID-Schlüsselpaar (P-256) als URL-sichere Base64-Zeichenketten. Braucht das Paket 'cryptography'."""
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization as s
k = ec.generate_private_key(ec.SECP256R1())
b = lambda x: base64.urlsafe_b64encode(x).rstrip(b"=").decode()
pub = k.public_key().public_bytes(s.Encoding.X962, s.PublicFormat.UncompressedPoint)
priv = k.private_numbers().private_value.to_bytes(32, "big")
print(f"VAPID_PUBLIC_KEY={b(pub)}")
print(f"VAPID_PRIVATE_KEY={b(priv)}")
