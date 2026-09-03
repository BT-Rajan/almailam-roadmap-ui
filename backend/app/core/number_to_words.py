"""Spells out a currency amount in English words (Decimal(1500.500) ->
"One Thousand Five Hundred Kuwaiti Dinars and Five Hundred Fils Only") --
Kuwaiti Dinar quotations traditionally state the total this way, and this
is exactly the "amount_in_words" placeholder an uploaded Quotation/
Contract document template can bind to (see
document_template_service.MERGE_FIELD_CATALOG). No third-party dependency
(num2words etc.) -- amounts here are always a plain currency total, well
within what a small hand-written converter handles correctly, and it
keeps the currency-name/minor-unit table (KWD's minor unit is "Fils", not
"Cents") fully under our control.
"""

from decimal import ROUND_HALF_UP, Decimal

_ONES = (
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen",
)
_TENS = ("", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety")
_SCALES = (
    (1_000_000_000, "Billion"),
    (1_000_000, "Million"),
    (1_000, "Thousand"),
    (100, "Hundred"),
)

# (major unit name, minor unit name, minor units per major unit) -- KWD's
# 3-decimal Fils is why this table exists at all rather than a flat "/100"
# assumption; every currency the Quotation/Contract form offers (see
# NewQuotationDialog.vue's CURRENCY_OPTIONS) is listed explicitly rather
# than guessed, so an unlisted currency fails loudly instead of silently
# mis-converting.
_CURRENCY_UNITS: dict[str, tuple[str, str, int]] = {
    "KWD": ("Kuwaiti Dinar", "Fils", 1000),
    "USD": ("US Dollar", "Cent", 100),
    "AED": ("UAE Dirham", "Fils", 100),
    "EUR": ("Euro", "Cent", 100),
}

# Minor-unit names that are already invariant between singular and plural
# in conventional English usage (Gulf currencies' "Fils" chief among
# them) -- pluralizing these by appending "s" would read as a typo
# ("Filss"), not a plural.
_INVARIANT_MINOR_UNITS = {"Fils"}


def _int_to_words(value: int) -> str:
    if value == 0:
        return "Zero"
    if value < 20:
        return _ONES[value]
    if value < 100:
        tens, remainder = divmod(value, 10)
        return _TENS[tens] + (f" {_ONES[remainder]}" if remainder else "")
    for scale_value, scale_name in _SCALES:
        if value >= scale_value:
            quotient, remainder = divmod(value, scale_value)
            head = f"{_int_to_words(quotient)} {scale_name}"
            return f"{head} {_int_to_words(remainder)}" if remainder else head
    return _ONES[value]  # pragma: no cover -- unreachable, every branch above covers 0-999,999,999


def amount_to_words(amount: Decimal, currency: str) -> str:
    """"Only" is appended the way Kuwaiti/Gulf commercial documents
    conventionally close this line, signalling the figure isn't open to a
    trailing-digits rounding dispute. Rounds to the currency's smallest
    unit first (banker's-rounding-free, matching how the amount itself is
    already stored/displayed -- see quotation_service.compute_amount)
    rather than truncating, so e.g. 1500.999 KWD reads as "...and 999
    Fils", not 998 from float error."""
    if currency not in _CURRENCY_UNITS:
        raise ValueError(f"amount_to_words does not know currency {currency!r}")
    major_name, minor_name, minor_per_major = _CURRENCY_UNITS[currency]

    scaled = int((amount * minor_per_major).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    major_units, minor_units = divmod(scaled, minor_per_major)

    major_plural = major_name if major_units == 1 else f"{major_name}s"
    words = f"{_int_to_words(major_units)} {major_plural}"
    if minor_units:
        minor_plural = minor_name if minor_units == 1 or minor_name in _INVARIANT_MINOR_UNITS else f"{minor_name}s"
        words += f" and {_int_to_words(minor_units)} {minor_plural}"
    return f"{words} Only"
