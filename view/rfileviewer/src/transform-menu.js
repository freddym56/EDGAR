// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.

// Enhancements (2026-March):
// - Menu initialization supports scroll-to-company-info anchor.
// - Selection behavior now updates aria-current and visible focus.
// - Accordion toggles operate with correct ARIA expanded state.
// - Internal highlight() integrated with external navigation and Shadow DOM updates.

// transform.menu.js
import { escapeHtml } from '../../viewer-common-src/sanitize.js';

/**
 * Render the accessible accordion navigation for reports.
 * - Category headings become <button class="accordion-toggle" aria-expanded/aria-controls>
 * - Each report selection is a <button class="rf_viewer"> that calls loadReport(n)
 * - "All Reports" + "Rendering Log" are buttons (consistent styling & highlight)
 * - Inline XBRL viewer remains a navigational <a> (so it can navigate to /ix)
 * - outputs rfvParsed menu structure for scrapers
 *     [ { documentType: 10-K, url: url },
 *       { category: str, reports: [
 *            { label: report-label, pos: position, url: url }, ...
 *          ] },
 *       ... more rFileReports and inlineReports as appropariate
 *       { allReports: [url, url...] },
 *       { renderingLogs: log-object } // only when renderingLogs are present
 *     ]
 */
export function renderAccordionMenu({
  inlineUrlDoctypes, 
  menuCats, 
  rfvMenu, 
  reportFiles, 
  maxPos 
  }, mode,
  secws = false,
  log = null) {
  
  /*
  * Description:
  *   Produces the SEC‑style accordion navigation menu used by
  *   Neptune/Mustard (server mode) and transform-page.js (client mode).
  *   Consumes the normalized shared fsReportsData produced by
  *   extractReportsAndMenuCats().
  *
  * Responsibilities:
  *   • Generate accessible <nav>/<ul>/<button> accordion markup
  *   • Insert inline XBRL Viewer entry (when instance has inline doctype)
  *   • Emit category accordion sections and report menu items
  *   • Emit synthetic “All Reports” entry (max(Position)+1)
  *   • Emit Rendering Log entry when log exists
  *   • Populate rfvMenu with scraper‑friendly structured metadata
  *   • Ensure ordering exactly matches fsReportsData.menuCats
  *
  * Inputs:
  *   fsReportsData — output of extractReportsAndMenuCats()
  *   mode          — 'server' | 'transform' (UI environment hint)
  *
  * Outputs:
  *   • Returns complete HTML <nav>…</nav> string
  *   • Populates fsReportsData.rfvMenu with structured menu metadata
  *
  * Dependencies:
  *   • escapeHtml() for safe label rendering
  *   • loadReport(), highlight(), ix_viewer_url() provided by client bootstrap
  *
  * Notes:
  *   • Does NOT compute categories, positions, or grouping.
  *     Those must be computed by extractReportsAndMenuCats().
  *   • Must remain DOM-portable and Shadow-DOM-safe.
  *   • No event wiring; client environment attaches handlers.
  */


  const reportsGif = (secws) ? '/AR/Images/reports.gif' : '/images/reports.gif';

	  let html = `
    <nav id="report-menu" aria-label="Reports menu">
      <ul id="menu" role="list">
  `;

  let catIndex = 0;
  let ixIndex = 0;

  for (const [instUrl, inlineDoctype] of inlineUrlDoctypes.entries()) {
    let firstOfInst = true;

    for (const [cat, items] of menuCats.entries()) {
      if (items.some(r => r.instance === instUrl && r?.ShortName != "All Reports")) {
        const catText = escapeHtml(cat);
        catIndex += 1;

        // Inline XBRL viewer link
        if (inlineDoctype != null && firstOfInst) {
          const displayedDocType = inlineDoctype || 'Unknown';  // may be blank if DocType missing
          firstOfInst = false;
          ixIndex += 1;

          html += `
            <li id="menu_ix${ixIndex}" class="accordion ix">
              <button class="ix_viewer" type="button"
                aria-label="Open ${escapeHtml(displayedDocType)} in IX Viewer"
                onclick="window.RFV && window.RFV.highlight(this);  window.location=ix_viewer_url('${instUrl}');">
                <span class="doc-type" aria-hidden="true">
                  ${escapeHtml(displayedDocType)}
                </span>
              </button>
            </li>
          `;

          rfvMenu.push({ documentType: displayedDocType, url: instUrl });
        }

        // Category toggle
        const panelId = `submenu-cat${catIndex}`;

        html += `
          <li class="accordion">
            <button id="menu_cat${catIndex}"
              class="accordion-toggle"
              type="button"
              aria-expanded="false"
              aria-controls="${panelId}">
              ${catText}
            </button>
            <ul id="${panelId}" data-accordion-panel role="list" hidden>
        `;

        const rfvCatReports = [];
        rfvMenu.push({ category: catText, reports: rfvCatReports });

        // Category items
        for (const r of items) {
          if (r.instance === instUrl && r?.ShortName != "All Reports") {
            const pos = Number(r?.Position ?? 0);
            const file = String(r?.HtmlFileName ?? r?.XmlFileName ?? "").trim();
            const label = escapeHtml(r?.ShortName ?? r?.LongName ?? "");

            html += `
              <li class="accordion" id="r${pos}">
                <button id="menu_r${pos}"
                        class="rf_viewer"
                        type="button"
                        onclick="window.RFV && window.RFV.highlight(this); loadReport(${pos});"
                        aria-controls="reportDiv">
                  ${label}
                </button>
              </li>
            `;

            rfvCatReports.push({ label, pos, url: file });
          }
        }

        html += `
            </ul>
          </li>
        `;
      }
    }

    catIndex++;
  }

  // Synthetic "All Reports"
  const allReportsPos = maxPos + 1;

  if (Object.keys(reportFiles).length > 0) {
    html += `
      <li class="accordion">
        <button class="all_reports" type="button"
          onclick="window.RFV && window.RFV.highlight(this); loadReport(${allReportsPos});">
          <img src="${reportsGif}" border="0" height="12" width="9" alt="Reports" /> All Reports
        </button>
      </li>
    `;

    reportFiles[allReportsPos] = "ALL_REPORTS_SYNTHETIC";

    rfvMenu.push({ allReports: reportFiles });
  }

  // Rendering logs
  if (log?.length) {
    html += `
      <li class="accordion">
        <button class="rendering_logs" type="button"
          onclick="window.RFV && window.RFV.highlight(this); window.showRenderingLog();"
          aria-controls="reportDiv">
          <img src="${reportsGif}" border="0" height="12" width="9" alt="Reports" /> Rendering Log
        </button>
      </li>
    `;
    rfvMenu.push({ renderingLogs: log });
  }

  html += `
      </ul>
    </nav>
  `;

  return html;
}