"""Meldet alle Operationen an (Import genügt: die Dekoratoren tragen sie in die Registry ein).

Eine neue Operation braucht nur ein Modul mit `@operation` und einen Import hier — sonst nichts (kein Endpunkt, keine
Werkzeugliste, keine Typen von Hand).
"""
from chronos.ai import ask  # noqa: F401
from chronos.domain import appointments, history_ops, series, teams  # noqa: F401
from chronos.notifications import ops  # noqa: F401
