// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.

// @ts-check

// Use .js file suffix for sec-gov and m365.cloud.microsoft/chat acceptability
// provide ts-check compatibility for ixviewer shared use


/**
 * Equivalent to Python secure_field() allowed character set.
 * Preserves only: A–Z a–z 0–9 and , . / ? : # @ - _ = + whitespace ' " ( ) $ % ]
 *
 * @param {unknown} input
 * @returns {string}
 */
export function secureField(input) {
  return String(input).replace(/[^A-Za-z0-9,./?:#@\-_=+\s'"()$%]/g, '');
}


/**
 * Escape HTML characters by &-encoding.
 * NOTE: This mirrors the mapping found in your original sanitize.js (no behavioral changes).
 *
 * @param {unknown} str
 * @returns {string}
 */
export function escapeHtml(str) {
  const s = String(str);
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '`': '&#96;',
  };
  return s.replace(/[&<>"'`]/g, ch => map[ch]);
}