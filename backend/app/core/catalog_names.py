"""Name comparison for the admin-maintained Service and Permit catalogs.

An exact (case-insensitive) match alone let near-duplicates in -- "Permit"
next to "Permits", "Baladia" next to "Baladia Permits" -- and both then
showed up side by side in the project Service Picker. name_key() folds
those spellings together so the catalogs can reject them.
"""

import re

_WORD = re.compile(r"[^\W_]+", re.UNICODE)


def _singular(word: str) -> str:
    # Deliberately simple: enough for the English plurals admins actually
    # type ("Permits", "Services", "Drawings"), without mangling short
    # words or ones ending in "ss" ("Access"). Arabic words pass through.
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def words(name: str) -> list[str]:
    return [_singular(w) for w in _WORD.findall(name.casefold())]


def name_key(name: str, ignore_words: frozenset[str] = frozenset()) -> str:
    """Case-, spacing-, punctuation- and plural-insensitive key.
    `ignore_words` (singular, lower-case) are dropped first -- e.g. the
    permit catalog ignores "permit" so "Baladia" == "Baladia Permits".
    Falls back to the full key if nothing else would remain."""
    all_words = words(name)
    kept = [w for w in all_words if w not in ignore_words]
    return " ".join(kept or all_words)
