// transform.templates.js (shared by server + Arelle)
import { escapeHtml, escapeAttr } from './transform.escape.js';
import { categorize } from './categorize.js';

/**
 * Render the accordion menu from FilingSummary data.
 * Required for client scripts; uses expected IDs/classes.
 */
export function renderAccordionMenu(fsParsed) {
  const items = [];
  for (const inst of Object.keys(fsParsed.instancesReports || {})) {
    const ir = fsParsed.instancesReports[inst];
    for (const r of ir.reports || []) {
      const cat = categorize(fsParsed, r); // category text
      items.push({ inst, r, cat });
    }
  }

  // TODO: replace IDs/classes with the exact ones your scripts require
  return `
<nav id="TODO_accordion_root" class="TODO_accordion_class">
  ${items.map(({ r, cat }) => `
    <div class="TODO_accordion_item" data-category="${escapeAttr(cat)}">
      <a class="TODO_accordion_link" href="#${escapeAttr(r?.instance || r?.shortName || 'Report')}
      </a>
    </div>
  `).join('')}
</nav>`;
}

/**
 * Render All Reports container. Client script expects a specific container ID/classes.
 */
export function renderAllReports(fsParsed) {
  const articles = [];
  for (const inst of Object.keys(fsParsed.instancesReports || {})) {
    const ir = fsParsed.instancesReports[inst];
    for (const r of ir.reports || []) {
      articles.push(`
<article id="${escapeAttr(r?.instance || '')}" class="TODO_allReports_article">
  <h3 class="TODO_allReports_title">${escapeHtml(r?.LongName || 'Report')}</h3>
  <div class="TODO_allReports_body">[placeholder for rendered content]</div>
</article>`);
    }
  }

  // TODO: exact ID/class hook (e.g., id="allReports")
  return `<section id="TODO_allReports_root" class="TODO_allReports_container">
${articles.join('\n')}
</section>`;
}

/**
 * Shared page renderer used by both transform() and server().
 * In transform mode, we omit server header/footer & DB-fueled sections.
 */
export function renderPage({
  mode, cik, accessionNumber, filingSummaryParsed, errors = []
}) {
  let html = `
<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="utf-8"/>
  <title>${escapeHtml('EDGAR Filing Data')}</title>
</head><body>
<header class="TODO_header_minimal">
  <h1>EDGAR Filing Data</h1>
  ${accessionNumber ? `<span class="acc">${escapeHtml(accessionNumber)}</span>` : ''}
</header>
`;

  if (errors.length) {
    html += `<div class="errors">${errors.map(e => `<p>${escapeHtml(String(e))}</p>`).join('')}</div>`;
  }

  // Accordion menu (required)
  if (filingSummaryParsed?.instancesReports) {
    html += renderAccordionMenu(filingSummaryParsed);
  }

  // All Reports (required)
  if (filingSummaryParsed?.instancesReports) {
    html += renderAllReports(filingSummaryParsed);
  }

  // No server footer/header in transform mode
  html += `</body></html>`;
  return html;
}
