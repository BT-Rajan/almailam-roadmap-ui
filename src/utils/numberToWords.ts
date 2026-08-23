// Converts a KWD amount into the "[amount] Kuwaiti Dinars only" style
// phrase used by the lettered quotation/contract templates. Correct for
// the range these documents realistically use (up to low millions);
// not a general-purpose currency-to-words library.

const AR_ONES = [
  '',
  'واحد',
  'اثنان',
  'ثلاثة',
  'أربعة',
  'خمسة',
  'ستة',
  'سبعة',
  'ثمانية',
  'تسعة',
  'عشرة',
  'أحد عشر',
  'اثنا عشر',
  'ثلاثة عشر',
  'أربعة عشر',
  'خمسة عشر',
  'ستة عشر',
  'سبعة عشر',
  'ثمانية عشر',
  'تسعة عشر',
]
const AR_TENS = ['', '', 'عشرون', 'ثلاثون', 'أربعون', 'خمسون', 'ستون', 'سبعون', 'ثمانون', 'تسعون']
const AR_HUNDREDS = [
  '',
  'مائة',
  'مئتان',
  'ثلاثمائة',
  'أربعمائة',
  'خمسمائة',
  'ستمائة',
  'سبعمائة',
  'ثمانمائة',
  'تسعمائة',
]

function arabicUnderThousand(n: number): string {
  if (n === 0) return ''
  const parts: string[] = []
  const hundreds = Math.floor(n / 100)
  const remainder = n % 100
  if (hundreds) parts.push(AR_HUNDREDS[hundreds])
  if (remainder) {
    if (remainder < 20) {
      parts.push(AR_ONES[remainder])
    } else {
      const tens = Math.floor(remainder / 10)
      const ones = remainder % 10
      parts.push(ones ? `${AR_ONES[ones]} و${AR_TENS[tens]}` : AR_TENS[tens])
    }
  }
  return parts.join(' و')
}

/** Whole-number integer (0 to low millions) to Arabic words. */
export function integerToArabicWords(value: number): string {
  const n = Math.floor(Math.abs(value))
  if (n === 0) return 'صفر'

  const millions = Math.floor(n / 1_000_000)
  const thousands = Math.floor((n % 1_000_000) / 1000)
  const rest = n % 1000

  const groups: string[] = []
  if (millions) {
    groups.push(millions === 1 ? 'مليون' : millions === 2 ? 'مليونان' : `${arabicUnderThousand(millions)} مليون`)
  }
  if (thousands) {
    groups.push(thousands === 1 ? 'ألف' : thousands === 2 ? 'ألفان' : `${arabicUnderThousand(thousands)} ألف`)
  }
  if (rest) {
    groups.push(arabicUnderThousand(rest))
  }
  return groups.join(' و')
}

/** e.g. 1250.500 KWD -> "ألف ومئتان وخمسون ديناراً كويتياً و500 فلس فقط لا غير" */
export function amountToArabicWords(amount: number, currencyLabel = 'دينار كويتي'): string {
  const dinars = Math.floor(amount)
  const fils = Math.round((amount - dinars) * 1000)
  const dinarsWords = integerToArabicWords(dinars)
  const dinarSuffix = dinars === 1 ? 'دينار كويتي' : dinars === 2 ? 'ديناران كويتيان' : `${currencyLabel}اً`
  const base = `${dinarsWords} ${dinarSuffix}`
  const filsPart = fils > 0 ? ` و${fils} فلس` : ''
  return `(${base}${filsPart} فقط لا غير)`
}

const EN_ONES = [
  '',
  'One',
  'Two',
  'Three',
  'Four',
  'Five',
  'Six',
  'Seven',
  'Eight',
  'Nine',
  'Ten',
  'Eleven',
  'Twelve',
  'Thirteen',
  'Fourteen',
  'Fifteen',
  'Sixteen',
  'Seventeen',
  'Eighteen',
  'Nineteen',
]
const EN_TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

function englishUnderThousand(n: number): string {
  if (n === 0) return ''
  const parts: string[] = []
  const hundreds = Math.floor(n / 100)
  const remainder = n % 100
  if (hundreds) parts.push(`${EN_ONES[hundreds]} Hundred`)
  if (remainder) {
    if (remainder < 20) {
      parts.push(EN_ONES[remainder])
    } else {
      const tens = Math.floor(remainder / 10)
      const ones = remainder % 10
      parts.push(ones ? `${EN_TENS[tens]}-${EN_ONES[ones]}` : EN_TENS[tens])
    }
  }
  return parts.join(' ')
}

export function integerToEnglishWords(value: number): string {
  const n = Math.floor(Math.abs(value))
  if (n === 0) return 'Zero'

  const millions = Math.floor(n / 1_000_000)
  const thousands = Math.floor((n % 1_000_000) / 1000)
  const rest = n % 1000

  const groups: string[] = []
  if (millions) groups.push(`${englishUnderThousand(millions)} Million`)
  if (thousands) groups.push(`${englishUnderThousand(thousands)} Thousand`)
  if (rest) groups.push(englishUnderThousand(rest))
  return groups.join(' ')
}

/** e.g. 1250.500 KWD -> "Kuwaiti Dinars One Thousand Two Hundred and Fifty and 500 Fils Only" */
export function amountToEnglishWords(amount: number, currencyLabel = 'Kuwaiti Dinars'): string {
  const dinars = Math.floor(amount)
  const fils = Math.round((amount - dinars) * 1000)
  const dinarsWords = integerToEnglishWords(dinars)
  const filsPart = fils > 0 ? ` and ${fils} Fils` : ''
  return `(${currencyLabel} ${dinarsWords}${filsPart} Only)`
}
