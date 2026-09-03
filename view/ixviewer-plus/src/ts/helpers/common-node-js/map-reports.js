// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.

// @ts-check

// Use .js file suffix for sec-gov and m365.cloud.microsoft/chat acceptability
// provide ts-check compatibility for ixviewer shared use

// report/instance mapping; matches Python behavior.
import { escapeHtml } from './sanitize.js';
import { normalizeCategory } from './category-normalizer.js';

/**
 * @typedef {Object} InstancesReportsEntry
 * @property {any[]} reports
 * @property {string=} original
 * @property {string=} doctype
 * @property {boolean=} hasStmt
 * @property {boolean=} isinline
 * @property {boolean=} isRr
 * @property {boolean=} isn3n4n6
 * @property {boolean=} isn2prospectus
 * @property {boolean=} isfeeexhibit
 * @property {boolean=} isOnlyDei
 * @property {boolean=} isDefinitelyFs
 * @property {boolean=} isDefinitelyNotFs
 * @property {string=} _priorMenuCat
 */

/** @typedef {Record<string, InstancesReportsEntry>} InstancesReports */

/**
 * Map FilingSummary.xml into instances + reports with flags & normalized categories.
 *
 * @param {any} filingSummary
 * @param {(msg:string)=>void=} log_debug
 * @returns {{
 *   instancesReports: InstancesReports,
 *   original: string,
 *   doctype: string,
 *   log: Array<{type:string,text:string}>,
 *   inputFiles: Array<string>,
 *   majorversion?: string,
 *   nreports?: number,
 *   nbooks?: number
 * }}
 */
export function mapReports(filingSummary, log_debug = () => {}) {
  // ---- normalize & return (use your existing logic) ----
  const fsRoot = filingSummary?.FilingSummary ?? filingSummary?.filingSummary ?? {};
  const fsVers = fsRoot?.Version;
  const reportNodes = normalizeArray(fsRoot?.MyReports?.Report);
  const inputFiles = normalizeArray(fsRoot?.InputFiles?.File);
  const fsLogs = fsRoot?.Logs ?? {};
  log_debug(`FilingSummary version ${fsVers}`);

  /** @type {InstancesReports} */
  const instancesReports = {};
  /** @type {Array<{type:string,text:string}>} */
  const fsLog = [];
  const mappedFilingSummary = {
    instancesReports,
    "original": "",
    "doctype": "",
    "log": fsLog
  };

  // Collect reports per instance
  const reports = [];
  const reportsHaveInstanceAttr = reportNodes.some(report => !!report?._attributes?.instance);
  const firstInst = (reportsHaveInstanceAttr) ? null : // first file for old FilingSummary.xml
    inputFiles.find(f => /\.xml$/i.test(f) && !/(pre|cal|def|lab|ref)\.xml$/i.test(f));
  let position = 1;
  for (const report of reportNodes) {
    const instance = report?._attributes?.instance ?? firstInst ?? "N/A";
    if (instance) {
      instancesReports[instance] ??= { reports: [] };
      instancesReports[instance].reports.push(report);
      reports.push([report]);
      report.instance = instance;
      if (!report?.Position) report.Position = position; // old FilingSummaries
      position += 1;
    }
  }

  // Map File attributes back onto reports; compute flags
  /** @type {Record<string, any>} */
  const fileMap = {};
  for (const f of inputFiles) {
    const original = f?._attributes?.original;
    if (original && instancesReports[original]) {
      fileMap[original] = f;
      const ir = instancesReports[original];
      ir.original = original;
      if (f?._attributes?.doctype) ir.doctype = f._attributes.doctype;
      setFlags(ir, f);
    }
  }
  if (!Object.keys(fileMap).length && firstInst) {
    fileMap[firstInst] = firstInst;
  }

  // Copy attributes from File onto associated Report + inline flag
  for (const key of Object.keys(instancesReports)) {
    const ir = instancesReports[key];
    ir.hasStmt = false;
    ir.isinline = false;
    for (const r of ir.reports) {
      const inst = r?.instance;
      const f = fileMap[inst];
      if (f) {
        Object.assign(r, f);
        const ext = String(inst ?? '').toLowerCase();
        ir.isinline = ext.endsWith('.htm') || ext.endsWith('.xhtml');
      }
      if (String(r?.LongName ?? '').includes(" - Statement - ")) ir.hasStmt = true;
      // map category name
    }
  }

  // Map categories
  for (const key of Object.keys(instancesReports)) {
    const ir = instancesReports[key];
    let priorMenuCat = null;
    for (const r of ir.reports) {
      r.normalizedCategory = priorMenuCat = normalizeCategory(r?.MenuCategory, r?.LongName, r?.Role, ir?.hasStmt, ir, priorMenuCat);
    }
  }

  // Meta
  const verText = String(fsRoot?.Version ?? '.');
  mappedFilingSummary.majorversion = verText.split('.')[0];
  mappedFilingSummary.nreports = reports.length;
  mappedFilingSummary.nbooks = reports.filter(r => r?.ReportType === 'Book').length;
  mappedFilingSummary.inputFiles = inputFiles;

  // Log - flatten logs into single array of log entries
  if (typeof process === 'undefined' || !process.env.BLOCK_LOGS) { // process uninitialized for tranform PythonMonkey executions
    Object.entries(fsLogs).forEach(([logName, logItems]) => {
      for (let t = 0; t <= 2; t++) {
        for (const i of (Array.isArray(logItems) ? logItems : [logItems])) { // Errors, Warnings and then others
          if (i) {
            const typ = escapeHtml(String(i?._attributes?.type ?? i?.type ?? ''));
            const txt = escapeHtml(String(i?._text ?? i?.text ?? ''));
            if ((t == 0 && typ == "Error") ||
                (t == 1 && typ == "Warning") ||
                (t == 2 && typ != "Error" && typ != "Warning")) {
              fsLog.push({type: typ, text: txt});
            }
          }
        }
      }
    })
  }
  return mappedFilingSummary;
}

/** @template T @param {T|T[]|undefined} v @returns {T[]} */
function normalizeArray(v) {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

/**
 * Copy of the R viewer’s flag mapping (names normalized for convenience)
 * @param {InstancesReportsEntry} ir
 * @param {any} f
 */
function setFlags(ir, f) {
  const map = {
    isRR: 'isRr',
    isVip: 'isn3n4n6',
    isN2Prospectus: 'isn2prospectus',
    isFeeExhibit: 'isfeeexhibit'
  };
  const flags = [
    'isRR','isOEF','isN2Prospectus','isVip','isFeeExhibit','isNcsr','isProxy',
    'isN1a','isSdr','isOnlyShr','isRxp','isUsgaap','isIfrs','isOnlyDei','isDefinitelyFs'
  ];
  for (const k of flags) {
    const nk = map[k] ?? k;
    const ka = f?._attributes?.[k] || f?.[k] || null;
    ir[nk] = ka === 'true' || ka === true;
  }
  ir.isDefinitelyNotFs =
    ir.isOnlyShr || ir.isRxp || ir.isN1a || ir.isn3n4n6 || ir.isn2prospectus ||
    ir.isfeeexhibit || ir.isProxy || ir.isSdr || ir.isOnlyDei ||
    (ir.isNcsr && !ir.isDefinitelyFs);
  ir.mayHaveExcel = ir.isOnlyDei || ir.isDefinitelyFs;
}

export function extractReportsAndMenuCats(fsParsed) {
  /*
  * transform-menu.js (extractReportsAndMenuCats)
  * EDGAR R File Viewer — FilingSummary Normalization
  * Created by staff of the U.S. Securities and Exchange Commission.
  * Public domain under 17 U.S.C. §105.
  *
  * Description:
  *   Extracts and normalizes report metadata from map-reports.js output.
  *   This function provides a shared, canonical data model used by both:
  *     • Mustard (server-mode R-File Viewer menu)
  *     • IX Viewer (HTML/inline fact navigation)
  *
  * Responsibilities:
  *   • Collect reports from instancesReports (map-reports.js)
  *   • Preserve instance ordering and inline doctype metadata
  *   • Flatten all reports across instances
  *   • Sort reports by Position (map-reports determines Position)
  *   • Group reports into menuCats using normalizedCategory
  *   • Compute reportFiles mapping and track highest Position
  *   • Populate fsParsed.rfvMenu with an initially empty array
  *
  * Guarantees:
  *   • Identical menuCats and ordering for Mustard and IX Viewer
  *   • Canonical category grouping based solely on normalizedCategory
  *   • No HTML generation — this is pure data processing
  *
  * Inputs:
  *   fsParsed — result of map-reports.js mapping
  *
  * Outputs:
  *   {
  *     inlineUrlDoctypes,   // Map(instUrl → inline doctype or null)
  *     menuCats,            // Map(category → array of reports)
  *     rfvMenu,             // Empty array; renderer populates
  *     reportFiles,         // Pos → filename mapping
  *     maxPos               // Highest Position found
  *   }
  *
  * Dependencies:
  *   • map-reports.js (assigns instance grouping, flags, category normalization)
  *   • Only pure JavaScript; no DOM, no event handling
  *
  * Notes:
  *   • This function must remain environment‑agnostic (Node/Web/Worker).
  *   • All rendering concerns belong to renderAccordionMenu().
  */

  const allReports = [];
  const inlineUrlDoctypes = new Map(); 
  const rfvMenu = fsParsed.rfvMenu = []; 

  // Collect reports from instancesReports
  for (const inst of Object.keys(fsParsed?.instancesReports ?? {})) {
    const ir = fsParsed.instancesReports[inst];
    const instUrl = ir.original ?? inst;
    inlineUrlDoctypes.set(instUrl, ir.isinline ? ir.doctype : null);

    for (const r of ir?.reports ?? []) {
      allReports.push(r);
    }
  }
  if (inlineUrlDoctypes.size === 0) {
    inlineUrlDoctypes.set(null, null);
  }

  // Sort by Position
  allReports.sort((a, b) => Number(a?.Position ?? 0) - Number(b?.Position ?? 0));

  // Group into Menu Categories (menuCats) by normalizedCategory (default: "Reports")
  const menuCats = new Map();
  for (const r of allReports) {
    const cat = String(r?.normalizedCategory ?? "Reports").trim() || "Reports";
    if (!menuCats.has(cat)) menuCats.set(cat, []);
    menuCats.get(cat).push(r);
  }

  // Collect all unique report files, track max position
  let reportFiles = {};
  let maxPos = 0;
  for (const r of allReports) {
    const pos = Number(r?.Position ?? 0);
    const file = String(r?.HtmlFileName ?? r?.XmlFileName ?? "").trim();
    if (file) {
      reportFiles[pos] = file;
      if (pos > maxPos) maxPos = pos;
    }
  }

  return {
    inlineUrlDoctypes,
    menuCats,
    rfvMenu,
    reportFiles,
    maxPos
  };
}