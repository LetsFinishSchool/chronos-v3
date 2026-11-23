"""Kanäle (mock, email, webpush). Nur Worker und Verdrahtung dürfen dieses Modul kennen, nie die Fachbereiche (S-9)."""
from chronos.channels import email, mock, webpush

CHANNELS = {m.name: m for m in (mock, email, webpush)}
