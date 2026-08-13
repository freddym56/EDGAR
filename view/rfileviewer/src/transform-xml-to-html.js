// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.


// Server-only XML → HTML transform (Node + libxslt).
// Chrome removed XSLTProcessor in browser; RFV never runs XSLT client-side.
// InstanceReport.xslt is externally owned; RFV does not modify it.
// ----------------------------------------------------------------------------
//
// Params are set to match legacy viewer.pl:
//   source = baseDir + '/'
//   asPage = 'true'
//
// Optional parity fixups:
//   - Rewrite <img src> to baseDir/basename
//   - (Client will also run small 'notes' fix; server fix not strictly needed)
//
// Errors:
//   - Throw on transform issues; server.js should log and omit the entry.
// ----------------------------------------------------------------------------


// approach using Linux xsltproc

import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const execFileAsync = promisify(execFile);

/**
 * Transform one XML report to HTML string using InstanceReport.xslt.
 * Preserves legacy semantics: params { source, asPage="true" }.
 */
export async function transformXmlToHtml({ xmlFullPath, baseDir, xsltFullPath }) {
  const { stdout } = await execFileAsync('xsltproc', [
    '--stringparam', 'source', baseDir.endsWith('/') ? baseDir : baseDir + '/',
    '--stringparam', 'asPage', 'true',
    xsltFullPath,
    xmlFullPath
  ]);
  return stdout;
}

/* Approach using libxslt (which needs to be compiled from source for nodejs v22)

import libxslt from 'node-libxslt';
import libxmljs from 'node-libxmljs';
import fs from 'fs/promises';

let stylesheet; // lazy-init once per process

async function getStylesheet() {
  if (!stylesheet) {
    const xsltText = await fs.readFile('/include/InstanceReport.xslt', 'utf8');
    stylesheet = libxslt.parse(xsltText);
  }
  return stylesheet;
}

export async function transformXmlToHtml({ xmlText, baseDir }) {
  const xslt = await getStylesheet();

  const params = {
    source: baseDir.endsWith('/') ? baseDir : (baseDir + '/'),
    asPage: 'true',
  };

  const xmlDoc = libxmljs.parseXml(xmlText);
  const html = xslt.apply(xmlDoc, params);

  // Optional parity fixups (match viewer.pl):
  // 1) Rewrite image src to filing directory basename semantics
  const fixedHtml = html.replace(
    /(<img[^>]*\bsrc=["'])([^"']+)/gi,
    (m, p1, src) => {
      if (!src || src.startsWith('data:') ||
          src.startsWith('https://s3.amazonaws.com/archives.sec.gov/edgar/data/')) {
        return m;
      }
      const basename = src.split('/').pop();
      return `${p1}${params.source}${basename}`;
    }
  );

  // 2) Gecko/WebKit notes conversion: if needed, keep client-side small fix
  //    (We’ll still run the client helper, so server doesn’t need to emulate it here.)

  return fixedHtml;
}

 */
