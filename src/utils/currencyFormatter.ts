export function formatCurrency(amount: number, currency = 'KWD'): string {
  return new Intl.NumberFormat('en-KW', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}
