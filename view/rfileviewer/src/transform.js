// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.

// src/transform.js
// Transform entry points for R File Viewer when called from EDGAR/render in Arelle:
// - FilingSummary.transform(...)  -> Arelle/PythonMonkey (Node-free)
//
// Parity with Perl viewer:
// * Perl-style accordion markup (anchors: javascript:loadReport(n))
// * Same client assets in both modes (accordion + loader, jQuery pinned)
//
// Notes:
// - Server mode serves the same scaffold and includes pinned assets from /include.
//
// - FxpJson file is in the format produced by fast-xml-parser, for example to test
//   RFileViewer>node_modules\.bin\fxparser fixtures\FilingSummary_sample.xml > fxp_sampel.json
//
// References:
// - transform.page.js renders the SEC-style page scaffold (menu + placeholder).
//
// Package context: "type": "module" (ESM).

// Note (2026-March):
// The transform pipeline now assumes the enhanced ShadowRoot rendering model
// implemented in transform.page.js, including all new safety styles,
// AR popups, and scroll-to-company-info behavior.

// - Does NOT supply transformedHtmlReports (this is done in EDGAR plugin)
// - RFV client fetches .htm via URL and renders in ShadowRoot.


import { mapReports, extractReportsAndMenuCats } from '../../viewer-common-src/map-reports.js';
import { renderAccordionMenu } from './transform-menu.js';
import { renderPage } from './transform-page.js';

// ----- Arelle entry: FilingSummary.transform (Node-free) -----
export function transform(filingSummaryFxpJsonObj, accessionNumber, title, logDebugToConsole=false, secws=false) {

  const log_debug = function(msg) {
      if (logDebugToConsole) console.log(msg);
  }

  const fsParsed = mapReports(filingSummaryFxpJsonObj, log_debug);
  const mode = 'transform';
  
  // Build accordion menu - step 1 - prep reports data
  const categorizedReports = extractReportsAndMenuCats(fsParsed);

  // Build accordion menu - step 2 - build html
  const menuHtml = renderAccordionMenu(categorizedReports, mode, secws, fsParsed.log);

  return renderPage({
    accessionNumber,
    fsParsed,
    aliasPath: '',       // Transform mode: local report files (co-located with output)
    mode,
    title: title,
    menuHtml,
    log_debug,
    secws,              // use SEC Workstation DisplayDocument.do queries
    errors: []
  });
}
