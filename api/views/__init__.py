"""Views: what each screen reads, built from stored records with the shared rules (C2, C5, C12, C18, C19).

The same functions run in two places:
    - the fixture scripts, from `contract/seed/demo.<package>.json`, to write `contract/fixtures/*.json`;
    - the friend's API, from Firestore documents of the same shape, to write `views/...` after every change.
So a screen that works on the fixtures works on the live views. Pure: records in, view out; no I/O here
except `store.load`.
"""
