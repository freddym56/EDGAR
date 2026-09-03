// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.

// FilingSummary.xml parser; matches Python behavior.

import { XMLParser } from 'fast-xml-parser';  // static import

const fetchText = async (url) => {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error('FilingSummary fetch failed');
  return resp.text();
};

// parser.js (excerpt) — robust detection + lazy import of fast-xml-parser

export async function parseFilingSummary(xmlInput, log_debug) {
  let filingSummary;

  // Helper: trim once
  const isString = typeof xmlInput === 'string';
  const s = isString ? xmlInput.trim() : '';

  // Robust detectors:
  const looksLikeXml = isString && (
    /^<\?xml\b/i.test(s)              // XML declaration
    || /^<\s*[A-Za-z_][\w.:-]*/.test(s)  // opening tag: <FilingSummary ...>
  );

  const looksLikeJson = isString && (
    // Heuristic: starts with { or [" and ends with } or ]
    (/^\{/.test(s) && /\}$/.test(s)) || (/^\[\s*{/.test(s) && /\]\s*$/.test(s))
  );

  const looksLikeUrl = isString && /^https?:\/\//i.test(s);

  if (isString) {
    // --- Case 1: XML string ---
    if (looksLikeXml) {
      // Lazy-load fast-xml-parser only when needed
      const parser = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: '', attributesGroupName: '_attributes', textNodeName: '_text' });
      filingSummary = parser.parse(s);

    // --- Case 2: JSON string ---
    } else if (looksLikeJson) {
      try {
        filingSummary = JSON.parse(s);
      } catch (e) {
        throw new Error(`Invalid JSON string for FilingSummary: ${e.message}`);
      }

    // --- Case 3: URL string (fetch XML, then parse) ---
    } else if (looksLikeUrl) {
      const resp = await fetch(s);
      const xml = await resp.text();
      const { XMLParser } = await import('fast-xml-parser');
      const parser = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: '', attributesGroupName: '_attributes', textNodeName: '_text' });
      filingSummary = parser.parse(xml);

    } else {
      const msg = 'Unsupported string format for FilingSummary input (expected XML, JSON, or URL).';
      log_debug(msg);
      throw new Error(msg);
    }

  // --- Case 4: Already-parsed object (etree-like or JSON) ---
  } else if (xmlInput && typeof xmlInput === 'object') {
    filingSummary = xmlInput;

  } else {
    msg = 'xmlInput must be an XML string, JSON string, URL string, or an object.';
    log_debug(msg);
    throw new Error(msg);
  }

  return filingSummary;
}

