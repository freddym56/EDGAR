# -*- coding: utf-8 -*-
"""
:mod:`EdgarRenderer.Summary`
Edgar(tm) Renderer was created by staff of the U.S. Securities and Exchange Commission.
Data and content created by government employees within the scope of their employment
are not subject to domestic copyright protection. 17 U.S.C. 105.
"""

# provide choice of python Javascript libraries
JS_LIB = "pythonmonkey" # 27 Mb extra distribution size, robust implementation for node.js 
#JS_LIB = "quickjs" # 3 Mb extra distribution size, customary quickjs (dormant project, no recent activity) 
#JS_LIB = "quickjs-ng" # active quickjs project under maintenance, need PR 8 (https://github.com/genotrance/quickjs-ng/pull/8) to handle long strings for FilingSummary.xml
if JS_LIB == "pythonmonkey":
    from pythonmonkey import eval as js_eval 
elif JS_LIB == "quickjs":
    import quickjs
elif JS_LIB == "quickjs-ng": # unsure, has to be built from PR to quickns-ng
    import quickjs

from lxml import etree
import json, os

JS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "view", "rfileviewer", "dist", "r-file-viewer.transform.iife.js")


# this section implements an lxml.etree to fast-xml-parser object for python

ATTR_PREFIX = ""
ATTRS_GRP_NAME = "_attributes"
TEXT_KEY = "_text"

def _coerce_scalar(s: str):
    """Coerce strings to bool/int/float when appropriate, else return as str."""
    if s is None:
        return ""
    s = s.strip()
    # boolean
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    # integer
    if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        try:
            return int(s)
        except ValueError:
            pass
    # float
    try:
        # allow numbers like 1.23 or -0.5
        if any(ch in s for ch in ".eE"):
            return float(s)
    except ValueError:
        pass
    return s

def _merge_child(d: dict, tag: str, value):
    """Place child value under tag, making a list only if tag repeats."""
    if tag in d:
        # Promote to list if repeated
        if isinstance(d[tag], list):
            d[tag].append(value)
        else:
            d[tag] = [d[tag], value]
    else:
        d[tag] = value

def lxml_element_to_fxp_json(el: etree._Element):
    """
    Convert any lxml element to a dict shaped like fast-xml-parser JSON output:
      - attributes in child object ATTRS_GRP_NAME if not null, prefixed with ATTR_PREFIX
      - text under TEXT_KEY only when attributes or children exist
      - scalars for simple elements (no attrs/children)
      - lists created only for repeated sibling tag names
    """
    # Collect attributes (prefixed)
    out = {}
    for k, v in el.attrib.items():
        if ATTRS_GRP_NAME:
            if ATTRS_GRP_NAME not in out: out[ATTRS_GRP_NAME] = {}
            out[ATTRS_GRP_NAME][f"{ATTR_PREFIX}{k}"] = _coerce_scalar(v)
        else:
            out[f"{ATTR_PREFIX}{k}"] = _coerce_scalar(v)

    # Recurse over children, grouping by tag name
    child_tag_counts = {}
    for child in el:
        child_tag_counts[child.tag] = child_tag_counts.get(child.tag, 0) + 1

    for child in el:
        child_val = lxml_element_to_fxp_json(child)
        # If child is simple (returns scalar), keep as scalar
        # Otherwise it's an object (possibly containing attributes/TEXT_KEY)
        _merge_child(out, child.tag, child_val)

    # Handle element text
    text = (el.text or "").strip()
    has_children = len(el) > 0
    has_attrs = bool(el.attrib)

    if has_children or has_attrs:
        # If there's meaningful text alongside attrs/children, store under TEXT_KEY
        if text:
            out[TEXT_KEY] = _coerce_scalar(text)
        # If no text and no children produced anything, ensure at least {} is returned
        if not out:
            out = {}
        return out
    else:
        # Simple element → scalar
        return _coerce_scalar(text)

def lxml_etree_to_fxp_json(root: etree._Element):
    """Top-level wrapper returning {root.tag: ...}"""
    return {root.tag: lxml_element_to_fxp_json(root)}

# entry point from render/__init__.py to transform etree into html

def transformToHtml(filing_summary_etree, accession_number, title=None, timeout_sec=60, logDebugToConsole=False, secws=False):

    # transform FilingSummary lxml etree to fast-xml-parser JSON object
    fxp_json_obj = lxml_etree_to_fxp_json(filing_summary_etree)

    # Load the transform-only bundle
    with open(JS_PATH, "r", encoding="utf-8") as f:
        js_code = f.read()

    if JS_LIB == "pythonmonkey":
        js_eval(js_code)
        js_transform = js_eval("RFileViewer.transform")

        try:
            html = js_transform(
                fxp_json_obj,
                accession_number,
                title,
                logDebugToConsole,
                secws
            )
            return html
        except Exception as exc:
            print("PythonMonkey JS error:", exc)
            raise

    elif JS_LIB in ("quickjs", "quickjs-ng"):
        # quickjs needs stringified object parameter
        fxp_json_str = json.dumps(fxp_json_obj)

        # add sourceURL for better stack traces
        js_code = "//@ sourceURL=r-file-viewer.transform.iife.js\n" + js_code

        ctx = quickjs.Context()
        try:
            # Evaluate IIFE bundle
            ctx.eval(js_code)
            # Create a wrapper for easier calling
            # Wrap the transform with JSON.parse inside JS
            ctx.eval("""
            function __rfv_transform(fxp_json_str, accession_number, title, logDebugToConsole, secws) {
                const fxp_json_obj = JSON.parse(fxp_json_str);
                return RFileViewer.transform(fxp_json_obj, accession_number, title, logDebugToConsole, secws);
            }
            """)

            # Retrieve JS function reference (Python callable)
            ctx.set_time_limit(int(timeout_sec * 1000))
            transform_fn = ctx.get("__rfv_transform")

            # Call JS function
            html = transform_fn(
                fxp_json_str,
                accession_number,
                title,
                logDebugToConsole,
                secws
            )
            return html
        except quickjs.JSException as exc:
            # Log JS exception with stack trace
            print("JS exception in RFV transform:", exc)
            print("JS traceback:\n", str(exc))
            # Optionally re-raise or wrap as needed
            raise
