// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.

/*
 * server-dev.js
 * EDGAR R File Viewer — Development Express Server
 * Created by staff of the U.S. Securities and Exchange Commission.
 * Public domain under 17 U.S.C. § 105.
 *
 * Description:
 *   Local development and testing server for the R‑File Viewer (RFV).
 *   This module is NOT used in Neptune/DMZ production. Instead, it provides
 *   a standalone Express application for:
 *      • Running RFV directly from source during development
 *      • Testing router behavior without Neptune integration
 *      • Enabling VS Code / Node debugging workflows
 *      • Serving static /include assets required by RFV
 *
 * Responsibilities:
 *   • Create an Express app instance (dev‑only; not used in production)
 *   • Mount the RFV router via buildRfvRouter()
 *   • Serve the minimal assets required for the viewer UI to function
 *   • Expose simple heartbeat endpoints (/ , /about , /help)
 *   • Provide an isolated, hot‑reload‑friendly test harness
 *
 * Execution Environment:
 *   • Node.js environment (development only)
 *   • Invoked manually (e.g., `node server-dev.js`)
 *   • May load RFV from either:
 *       – src/rfv-router.js   (source mode)
 *       – dist/r-file-viewer.bundle.js   (bundle mode)
 *
 * Not Used In:
 *   • Neptune DMZ server mode
 *   • Arelle/PythonMonkey transform mode
 *
 * Configuration:
 *   • SERVER_ROOT  — base path for /include assets
 *   • PORT         — override default listener port (fallback uses 3000)
 *
 * Notes:
 *   • This module intentionally owns the Express app and `app.listen()`.
 *   • In production: RFV exports ONLY a router; Neptune owns the server.
 *   • Keep this file minimal so dev behavior stays predictable and debuggable.
 */

import express from 'express';
// uncomment one of these lines to run from source or bundle
//import { buildRfvRouter } from './rfv-router.js';                 // run from src (requires fast-xml-parser access)
import { buildRfvRouter } from '../dist/r-file-viewer.bundle.js'; // run from bundle

import path from 'node:path';

const app = express();
const serverRoot = process.env.SERVER_ROOT;
const includeDir = `${serverRoot}/include`;

// Basic heartbeat for dev server
app.get('/', (req, res) => {
    res.send('RFileViewer router mounted (Neptune integration)');
});

app.get('/about', (req, res) => {
    res.send('RFileViewer is active under Neptune');
});

app.get('/help', (req, res) => {
    res.send('Use /cgi-bin/viewer?action=view&cik=...&accession_number=...&xbrl_type=v');
});

// Static asset passthrough (only assets RFV *requires*)
app.use('/include', express.static(includeDir));
app.use('/cgi-bin/include', express.static(includeDir));
app.use('/cgi-bin/report.css', express.static(path.join(includeDir, 'report.css')));
app.use('/js/third-party', express.static(includeDir));
app.use('/Archives', express.static(`${serverRoot}/Archives`));
app.use('/images', express.static(includeDir));
app.use('/edgar/search/images', express.static(includeDir));
app.use('/edgar/search/global/css/bootstrap', express.static(includeDir));
app.use('/favicon.ico', express.static(path.join(includeDir, 'favicon.ico')));

// iX viewer passthrough (XML-based inline XBRL)
app.use('/ix', express.static(path.join(serverRoot, 'ix'), {
    setHeaders: (res) => {
        res.setHeader('Content-Type', 'application/xhtml+xml');
    }
}));
app.use('/ixviewer-plus', express.static(`${serverRoot}/ixviewer-plus`));
    
app.use('/cgi-bin', buildRfvRouter({
  express,
  apiPath: '/viewer',
  serverRoot: process.env.SERVER_ROOT,
  includeDir: includeDir,
  log_debug: console.log
}));
app.listen(process.env.PORT || 3000);