# EDGAR R File Viewer (Unified Rendering System)
A unified, cross‑environment rendering engine for EDGAR R‑files, providing
the same user‑facing output across:

- **Neptune DMZ server mode** (Node/Express, CGI replacement)
- **Arelle/PythonMonkey transform mode** (Node‑free execution)

The viewer renders SEC‑style accordion navigation, consolidated report menus,
Shadow DOM–isolated content, accessibility features, and legacy EDGAR output
parity—using one shared codebase.

---

# 1. Overview

The R File Viewer (RFV) is delivered as two build artifacts:

1. **Neptune Router Bundle**  
   `dist/r-file-viewer.bundle.js`  
   - Imported and mounted inside Neptune’s existing Express application  
   - Provides the `/cgi-bin/viewer` CGI‑replacement for filings  
   - Uses Neptune’s DB access (`runQuery`) when provided

2. **Transform Bundle**  
   `dist/r-file-viewer.transform.iife.js`  
   - Runs inside **Arelle** via **PythonMonkey**  
   - Contains no Node, filesystem, or DB dependencies  
   - Used for GUI render mode and SECWS transform pipelines

This unified architecture preserves parity between DMZ operations, Arelle, and
legacy Perl output while eliminating standalone servers previously required.

---

# 2. Neptune Integration Overview

Beginning in 2026, RFV no longer starts its own Express server inside DMZ.
Instead:

- Neptune imports the router from the server bundle:
  ```js
  import { server as rfvServer } from 'r-file-viewer.bundle.js';
  app.use('/cgi-bin/viewer', rfvServer({ ...options }));
  ```
- RFV contributes only an **Express router**, not a full application.
- No `app.listen()` or global server state exists inside RFV.
- Neptune owns:
  - routing
  - logging
  - lifecycle
  - request/session middleware
  - error handling

This aligns the R File Viewer with DMZ security and containerization practices
while preserving dev‑friendly behavior for local development.

---

# 3. Database Integration Model (Neptune‑aware)

RFV dynamically selects the appropriate DB adapter:

### When Neptune provides `runQuery(sql, values)`
RFV:
- Uses Neptune’s DB connection pool  
- Performs **no** mysql2 setup  
- Has no DB lifecycle to manage  
- Uses the adapter:

```js
{ name: "neptune", query: (sql, vals) => runQuery(sql, vals) }
```

### When Neptune does *not* provide `runQuery`
RFV:

1. Uses `DB_STUB_FILE` if supplied (test scenarios)
2. Otherwise creates a singleton **mysql2/promise** pool (dev only)

This behavior is located inside `src/db.js` and ensures consistent results in both DMZ and dev1 environments.

---

# 4. File & Module Structure

The R File Viewer source tree is organized around two execution environments:
(1) **Neptune/DMZ server mode** and  
(2) **Arelle/PythonMonkey transform mode**.

Below is the up‑to‑date structure reflecting the current Neptune router design,
development workflow, and asset pipeline.

```
src/
├── rfvp-router.js          # Primary Express router factory used by Neptune
│                           # Replaces older inline server.js router logic
│                           # Exports an Express.Router(), never app.listen()
│
├── server-dev.js           # Local/dev1 development entry point:
│                           # - Starts Express for VS Code debugging
│                           # - Loads rfvp-router.js
│                           # - Provides hot‑reload friendly behavior
│
├── transform.js            # Arelle/PythonMonkey entry point (Node‑free)
│                           # Exports FilingSummary.transform() API
│
├── parser.js               # Robust FilingSummary.xml / JSON parser
│
├── transform-menu.js       # Builds the SEC‑style accordion navigation
│                           # Normalizes categories using IXViewer rules
│
├── transform-page.js       # Constructs the page scaffold and injects
│                           # Shadow DOM into #reportDiv
│
├── map-reports.js          # Maps FilingSummary input into a consolidated
│                           # structure: categories, report positions, logs
│
├── category-normalizer.js  # Shared with ixviewer-plus; ensures consistent
│                           # categorization across SEC viewers
│
├── sanitize.js             # HTML/input sanitization for safe field values
│
├── db.js                   # MySQL/stub adapter with Neptune-aware runQuery
│                           # fallback logic
│
└── public/                 # Static assets published to dist/public
    └── include/
        ├── jquery-3.7.1.min.js
        ├── accordionMenu.js     # Official SEC accordion script
        ├── sec-viewer.js        # Viewer loader; used in DMZ/server mode
        └── (CSS, fonts, icons, etc.)
```

### Notes on the Layout

- **rfvp-router.js**
  - This is the official entry point for Neptune.
  - Creates and returns an Express `Router()` without starting any server.
  - Handles CGI-style routes, asset paths, DB integration, and HTML assembly.

- **server-dev.js**
  - Convenience script for local/VS Code debugging.  Used on dev1 for testing.
  - Starts Express on a local port (e.g., 8083) and mounts `rfvp-router`.
  - Mirrors Neptune behavior but retains live reload and full console logging.

- **transform.js**
  - Used by Arelle (PythonMonkey) only.
  - Contains no DB or filesystem coupling.

- **transform-page.js / transform-menu.js**
  - Shared between DMZ and Arelle.
  - These modules implement page scaffolding, accessibility model, the menu,
    and Shadow DOM rendering logic.

- **db.js**
  - Adapts to Neptune’s `runQuery()`.
  - Falls back to stub or mysql2 pool only in dev mode.

- **public/include**
  - Pinned assets loaded identically in both Arelle transform mode and DMZ
    (with SECWS differences handled at runtime).

---

# 5. Build Outputs

### Server / Neptune
```
dist/r-file-viewer.bundle.js   (ESM Router)
```
This file is invoked on the Neptune configuration when the index.js imports express/rfv/r-file-viewer.bundle.js.

On Neptune it is recommended that the EDGAR git repo is checked out and view/rfileviewer/dist/r-file-viewer.bundle.js
is sym-linked to express/rfv/r-file-viewer.bundle.js.  In this way rebuilds of express/rfv/r-file-viewer.bundle.js
which are checked into git become available to Neptune's express server when pulled.


### Arelle Transform Mode
```
dist/r-file-viewer.transform.iife.js   (IIFE, Node-free)
```
This file is relatively-referenced from the EDGAR plugin render/RFileViewer.py which is called
from render/__init__.py to transform FilingSummary.xml into FilingSummary.html when invoked
by command line with parameter --summaryXSLT specifying RFileViewer or RFileViewerSECWS or absent,
and when invoked by GUI operation with the same formula Parameters.  (It is not used when 
--summaryXSLT specifies a .xslt suffixed real file).

### Commands

Please run these commands in the rfileviewer directory (parent of src and dist directories)
to regenerate the files r-file-viewer.bundle.js and r-file-viewer.transform.iife.js

```bash
npm ci
npm run build:server     # Builds router bundle + asset copy
npm run build:transform  # Builds Arelle IIFE bundle
npm test
```

### Deployments

#### EDGAR plugin

The EDGAR plugin will use r-file-viewer.transform.iife.js via Pythonmonkey being called from
render/__init__ via render/RFileViewer.py.

#### Neptune

Install on Neptune as noted above under "Server / Neptune".

Use one of the below rfv-*.sh scripts to start, ping, restart or stop the Express server if needed.  
(The bare cmd line to start express is "node index.js".)

#### Dev1

Install on dev1 under the r-file-viewer directory by WinScp to upload src and dist files as needed.

Dev1 always starts Express by node src/server-dev.js, where one of these options can be uncommented:
 * import buildRfvRouter from sibling source file to run from source
 * import buildRfvRouter from ../dist/r-file-viewer.bundle.js to run from bundle

Use one of the below rfv-*.sh scripts to start, ping, restart or stop the Express server if needed.
(The bare cmd line to start express is "node src/server-dev.js".)

#### Neptune and Dev1 shell scripts

 * rfv-start.js - starts Express from scratch
 * rfv-restart.js - if running terminates Express and then starts it
 * rfv-stop.js - terminates Express
 * rfv-ping.js - verifies whether the Express process started by -start or -restart is still running.

### package.json
```json
{
  "scripts": {
    "build:server": "node build.js && node copy-assets.js",
    "build:transform": "node build.js",
    "start": "node dist/viewer.bundle.cjs --mode=server",
    "test": "jest --env=node"
  }
}
```

---

# 6. Asset Copy Process

`copy-assets.js`:

- Copies `src/public` → `dist/public`
- Normalizes the official SEC accordion script filename
- Ensures pinned jQuery exists
- Warns when required front-end assets are missing

---

# 7. Using RFV in Arelle (Transform Mode)

```python
from pythonmonkey import eval as js_eval

with open("dist/viewer.transform.iife.js", "r", encoding="utf-8") as f:
    js_code = f.read()

js_eval(js_code)

transform = js_eval("FilingSummary.transform")

fs_etree = {
    "FilingSummary": { "MyReports": {"Report": []}, "InputFiles": {"File": []} }
}

html = transform(fs_etree, "000032019326000006")
print(html)
```

This produces SEC-style HTML identical to the DMZ output.

---

# 8. Using RFV in Neptune (Server Mode)

### Environment Variables

- **SERVER_ROOT** — base directory for `/include`  
- **SERVER_API** — path to CGI-compatible endpoints  
- **DB_STUB_FILE** — path to stub DB JSON  
- **DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASS**  
- **BLOCK_LOGS** — suppresses log entries in FilingSummary  
- **DEV_ENV_MODE** — dev flags for debugging  
- **DEBUG_LOG_FILE** — file or `"console.log"`

### Mounting the Router

```js
import { server as rfvServer } from './dist/r-file-viewer.bundle.js';
app.use('/cgi-bin/viewer', rfvServer({ SERVER_ROOT: "/edgar" }));
```

### `.xml` R-file Transform Flow

When RFV encounters a `.xml` report:

1. Neptune (or server.js) applies XSLT using `node-libxslt`.
2. RFV embeds the resulting strings into:

```js
window.TRANSFORMED_HTML_REPORTS = { "3": "<html...>" };
```

3. `loadReport(n)` loads directly from this map—no filesystem reads in the browser.

---

# 9. Page Rendering Architecture

### Shared Scaffold (transform-page.js)

Rendered first to avoid FOUC:

- Header, breadcrumbs, company info
- Accordion left menu
- Report display region (`<div id="reportDiv">`)
- Footer
- Skip-link and ARIA-compliant navigation regions

### Shadow DOM for Report Rendering

All report HTML loads into:

```javascript
const shadow = reportDiv.attachShadow({ mode: "open" });
```

Benefits:

- Encapsulated CSS
- Predictable external stylesheet ordering
- Isolated table/image layout
- Safe handling of legacy EDGAR tags
- Popup AR definitions remain fully ARIA-compliant

---

# 10. Report Rendering Pipeline

1. **loadReport(n)**
2. Fetch `.htm` or use `TRANSFORMED_HTML_REPORTS`
3. **extractLinksAndBody()**
   - Inline `<style>` blocks
   - External CSS
   - Body extraction
4. **renderIntoShadow()**
   - Clear ShadowRoot
   - Inject safety CSS
   - Insert HTML body
   - Fetch and inject external CSS
5. **announce via aria-live**
6. Fade-in transition using `.rfv-pending`

---

# 11. Accordion Menu Behavior

- Built from FilingSummary.xml
- Categorization uses IXViewer-compatible rules
- Categories and report items are accessible `<button>` widgets
- **Initial Selection**:  
  The first report position is automatically marked using:

  ```javascript
  element.classList.add("is-selected");
  ```

  This ensures consistent highlight behavior across DMZ, Arelle, and local dev.

- `aria-current="page"` applied when loading a report
- Report selection scrolls back to the Company Info anchor

---

# 12. Accessibility (Section 508 / WCAG 2.1)

- Correct landmark structure (`<main>`, `<nav>`, `<header>`, `<footer>`)
- Skip-to-main-content link appears only on keyboard tab
- Accordion categories announce expanded/collapsed state
- Report area announces updates via live region
- Shadow DOM popups include ESC-close and focus restoration
- Color contrast and no color-only semantics
- Keyboard navigation mirrors official SEC behavior

## 12.1 Focus, Hover, and Selection States (WCAG 2.2‑aligned)

The accordion menu and report list use three distinct and intentionally separate visual states.  
These states follow WCAG 2.4.7 (Focus Visible), WCAG 2.4.11 (Focus Appearance Minimum),  
and ARIA Authoring Practices for accordions and menus.

### 1. **Focus (keyboard users only)**  
- Implemented using `:focus-visible`.  
- Displays a 3px blue outline (`#005A9C`) with a 2px offset.  
- Only appears during **keyboard** navigation, not mouse clicks.  
- When a report is activated, focus intentionally moves to the main content region  
  to support screen‑reader workflows and prevent redundant navigation.

### 2. **Selection (current report)**  
- Marked using `aria-current="page"` and `.is-selected`.  
- Shows a persistent left border highlight.  
- Uses a background fill suitable for light or dark menu items.  
- Uses increased font weight for a non‑color cue.  
- Does *not* display a focus ring unless the user explicitly tabs back to it.

### 3. **Hover (pointer users)**  
- Uses background‑color and text‑decoration changes.  
- Dark‑background items (IX Viewer, All Reports, Rendering Log) use  
  a separate high‑contrast hover color to maintain WCAG 1.4.11 compliance.

### 4. **Accordion Toggles**  
- Expanding or collapsing a section via keyboard keeps focus on the toggle button,  
  which is the ARIA‑recommended pattern.  
- Expanding via mouse does not show a focus ring because `:focus-visible` suppresses  
  keyboard‑only indicators for pointer interactions.

### 5. **Intended Behavioral Summary**  
- **Tab** → shows focus ring on menu items.  
- **Enter / Space** on a category toggle → focus remains on the toggle.  
- **Enter** on a report → selection updates, focus moves to main content.  
- **Mouse click** → does not create a focus ring (correct per `:focus-visible`).  
- Selection visuals persist independently of focus state.
---

# 13. FOUC Prevention & Ready-State Logic

- Page becomes visible immediately after scaffold creation
- When no reports exist, `__rfvSetReady()` still runs
- Fade transitions avoid header/footer jumps
- No global `scrollTo(0,0)`—local scroll to Company Info preserves context

---

# 14. Execution Modes Summary

### Arelle Transform Mode
- Input: FilingSummary dict/etree
- Output: Self-contained SEC-style HTML
- No DB or filesystem access
- No XSLT (transform performed before viewer renders)

### Neptune Server Mode
- Input: FilingSummary.xml + Filing directory
- XSLT for `.xml` reports performed server-side
- DB metadata retrieval via Neptune `runQuery`
- Shadow DOM content rendered client-side

Both modes use the same menu, scaffold, Shadow DOM, and accessibility logic.

---

# 15. Parity Checklist

- Menu structure matches IXViewer
- All Reports is appended after last position
- No browser XSLT
- Server mode uses transformed HTML map
- Transform mode loads `.htm` only
- Categories normalized via shared logic
- Logs appended when available

---

# 16. Security & CSP Model

- No client-side XSLT (reduces attack surface)
- Only reads files listed in FilingSummary
- Image-path rewrite avoids external URLs
- Shadow DOM ensures CSS locality
- Escaped HTML and safe string handling via sanitize.js

---

# 17. Keyboard Navigation Quick Guide

*(Identical behavior in Arelle and Neptune)*

- **Tab** → reveals skip link  
- **Enter** on skip link → moves to Company Info  
- **Tab** → enters accordion menu  
- **Enter/Space** → expand/collapse categories  
- **Enter** → load report  
- **Shift+Tab** → return to menu  
- **Alt+M / Alt+Left** → jump to menu (optional)  
- **Alt+C / Alt+Right** → jump to content  
- **Esc** → close popups

---

# 18. FAQ

**Q: Does RFV start its own server?**  
No. It provides only a router. Neptune owns the actual Express instance.

**Q: Can RFV run without a DB?**  
Yes. In Arelle mode or when `DB_STUB_FILE` is set.

**Q: Where is XSLT executed?**  
Only server-side (Node/libxslt) before sending HTML to the client.

**Q: Does RFV load external CSS from filings?**  
Yes, but only for report content, and only inside a Shadow DOM.

---

# 19. License

All EDGAR R File Viewer code authored by the U.S. Securities and Exchange Commission
is public domain under **17 U.S.C. § 105**.