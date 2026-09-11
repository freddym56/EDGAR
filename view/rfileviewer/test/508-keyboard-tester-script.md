# R File Viewer – Section 508 Keyboard Tester Script

This script validates keyboard‑only operation and observable accessibility behaviors
(expected by Section 508, WCAG 2.1 A/AA, and internal OIT/QCTC testing practices).

All steps must be completed **using only the keyboard**.

---

## 1. Initial Page Load

1. Load the filing URL in a browser.
2. Press **Tab** once.

**Expected Results**
- The **"Skip to main content"** link becomes visible.
- Focus is clearly indicated on the skip link.

3. Press **Enter**.

**Expected Results**
- Focus moves to the **Company Info** region at the top of main content.
- Screen reader should announce “main” or “main content” depending on mode.

---

## 2. Navigating to the Accordion Menu

4. Press **Tab**.

**Expected Results**
- Focus moves from Company Info into the **left-hand report menu**.
- The first menu category heading receives focus.

5. Press **Enter** or **Space** to toggle the category.

**Expected Results**
- Category expands or collapses.
- `aria-expanded` updates correctly.
- Screen reader announces “expanded” or “collapsed.”

---

## 3. Report List Navigation

6. Press **Tab** to move into the list of reports in the expanded category.

**Expected Results**
- Each report entry is a **button**.
- Each entry is reachable and receives visible focus.

7. Press **Enter** on any report.

**Expected Results**
- Report area sets `aria-busy="true"` briefly.
- Report loads in the **Report content** region.
- Screen reader announces update from the live region.
- The selected report is marked with `aria-current="page"`.

---

## 4. Moving Between Menu and Report Area

8. Press **Shift+Tab** until you return to the menu.

**Expected Results**
- Focus returns to the selected report or the category heading.
- No focus traps occur.

9. Press **Tab** again to move back into the report pane.

**Expected Results**
- Focus enters the labeled “Report content” region.
- Content is readable in logical order with down‑arrow or reading commands.

---

## 5. Opening Definition Pop‑ups (ShowAR)

10. Within the report content, use **Tab** or arrow navigation to reach a definition link.

11. Press **Enter**.

**Expected Results**
- A pop‑up appears adjacent to the link.
- Focus moves **into the pop-up**.
- Screen reader announces it as a region (e.g., “Definition”).

12. Press **Esc**.

**Expected Results**
- Pop‑up closes.
- Focus returns to the triggering link.
- No stray focus remains behind the Shadow DOM boundary.

---

## 6. Keyboard Behavior Validation Checklist

- **Tab / Shift+Tab** move predictably through:
  1. Skip link  
  2. Breadcrumbs  
  3. Company Info  
  4. Left menu  
  5. Report content  
- **Enter / Space** correctly:
  - expands/collapses categories  
  - selects reports  
  - opens definition pop‑ups  
- **Esc** closes definition pop‑ups and returns focus.
- No focus indicators disappear.
- No focus traps exist in:
  - report menu  
  - accordion panels  
  - pop‑ups  
  - Shadow DOM report viewer
- Menu to/from Content
  - Alt+C, Alt+Right to content
  - Alt+M, Alt+Left to menu

---

## 7. Pass/Fail Criteria

The feature **passes** if:
- All interactive elements are keyboard‑reachable.
- Focus order matches logical reading order.
- Pop‑ups open, announce, and close with correct ARIA behavior.
- Live region announces report updates.
- No contrast/FORC issues block visibility of focus indicators.

The feature **fails** if:
- The skip link cannot be activated.
- Menu cannot be expanded/collapsed via keyboard.
- Reports cannot be selected via keyboard.
- Focus becomes trapped or jumps unexpectedly.
- Pop‑ups do not announce, or Esc does not close them.

---

## 8. Tester Notes Section (to be completed by QCTC/508 testers)

- Browser:
- Assistive Tech (JAWS/NVDA + version):
- Filing URL tested:
- Observed issues:
- Screenshots or transcript references: