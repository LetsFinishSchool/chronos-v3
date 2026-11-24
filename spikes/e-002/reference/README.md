# Referenzattrappe (kein Kandidat)

Minimale Python-Umsetzung von `../common/V-1-aufgabenbeschreibung.md` (PostgreSQL, ein Image mit `web` und `worker`). Zweck: die Abnahmesuite (V-2) und die Umgebung (V-4) **validieren**, bevor die Agenten laufen. Keine Qualität, kein Web Push (K3 nicht abgedeckt), kein Teil der Bewertung.

```sh
make build                                          # Image chronos-spike-reference
../common/env/stack.sh up reference 0 chronos-spike-reference
eval "$(../common/env/stack.sh env reference 0)"
python3 ../common/acceptance/run_acceptance.py
```
