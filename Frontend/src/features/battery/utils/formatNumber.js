/**
 * Formats a number for display, or an em dash when the backend sent null,
 * NaN or anything that is not a finite number. A bad value must never crash a screen.
 *
 * @param {unknown} value - Value from an API response.
 * @param {number} [digits=1] - Decimal places.
 * @returns {string}
 */
export function formatNumber(value, digits = 1) {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(digits)
    : "—";
}

/**
 * Formats a 0-1 probability as a whole percent, or an em dash when it is not a finite number.
 *
 * @param {unknown} probability - Value from an API response.
 * @returns {string}
 */
export function formatPercent(probability) {
  return typeof probability === "number" && Number.isFinite(probability)
    ? String(Math.round(probability * 100))
    : "—";
}
