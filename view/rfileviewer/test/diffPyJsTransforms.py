#
# Compare python-implemented RFileViewer to javascript-implemented r-file-viewer.transform
#
# compares html results
#
from pythonmonkey import eval as js_eval
import json, os, difflib
from lxml import etree
from RFileViewerInPython import transformToHtml as transformPy

RFileViewer_DIR = os.path.dirname(os.path.dirname(__file__))
RFileViewer_JS_PATH = os.path.join(RFileViewer_DIR, "dist", "r-file-viewer.transform.iife.js")

TESTCASE = "FilingSummary2.xml"
#TESTCASE = "FilingSummary_sample.xml"
TESTCASE_PATH = os.path.join(RFileViewer_DIR, "samples", TESTCASE)

ACCESSION = "0000320193-26-000006"

from lxml import etree

ATTR_PREFIX = "@_"
TEXT_KEY = "#text"

# this section implements an lxml.etree to fast-xml-parser object for python
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
      - attributes prefixed with '@_'
      - text under '#text' only when attributes or children exist
      - scalars for simple elements (no attrs/children)
      - lists created only for repeated sibling tag names
    """
    # Collect attributes (prefixed)
    out = {}
    for k, v in el.attrib.items():
        out[f"{ATTR_PREFIX}{k}"] = _coerce_scalar(v)

    # Recurse over children, grouping by tag name
    child_tag_counts = {}
    for child in el:
        child_tag_counts[child.tag] = child_tag_counts.get(child.tag, 0) + 1

    for child in el:
        child_val = lxml_element_to_fxp_json(child)
        # If child is simple (returns scalar), keep as scalar
        # Otherwise it's an object (possibly containing attributes/#text)
        _merge_child(out, child.tag, child_val)

    # Handle element text
    text = (el.text or "").strip()
    has_children = len(el) > 0
    has_attrs = bool(el.attrib)

    if has_children or has_attrs:
        # If there's meaningful text alongside attrs/children, store under #text
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


def normalize_html(s: str) -> str:
    """
    Lightweight normalization so diffs focus on semantic diffs:
    - normalize whitespace
    - collapse consecutive spaces
    - normalize line endings
    - strip redundant spaces before '>' and after '<'
    """
    if s is None:
        return ""
    # Normalize EOLs
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # Remove trailing spaces
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    # Collapse multiple spaces
    s = re.sub(r"[ \t]+", " ", s)
    # Remove spaces before '>' and after '<'
    s = re.sub(r"\s+>", ">", s)
    s = re.sub(r"<\s+", "<", s)
    return s.strip()

def unified_diff(a: str, b: str, a_name: str, b_name: str) -> str:
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)
    diff = difflib.unified_diff(a_lines, b_lines, fromfile=a_name, tofile=b_name)
    return "".join(diff)


# Load the transform-only bundle
with open(RFileViewer_JS_PATH, "r", encoding="utf-8") as f:
    js_code = f.read()
js_eval(js_code)

#  inject a guard that explodes if anything tries network:
js_eval("""
  globalThis.fetch = (...args) => {
    throw new Error('Network disabled in transform test. Attempted: ' + (args && args[0]));
  };
  // Optional: block other network APIs if present
  globalThis.XMLHttpRequest = function () { throw new Error('Network disabled'); };
""")


transformJS = js_eval("RFileViewer.transform")

# Load the testcase
xml_tree = etree.parse(TESTCASE_PATH)
xml_root = xml_tree.getroot()


# transform lxml etree to fast-xml-parser JSON object
fxp_json_obj = lxml_etree_to_fxp_json(xml_root)
fxp_json_str = json.dumps(fxp_json_obj, indent=2)
with open(os.path.join(os.path.dirname(__file__), "out_fxp_from_FilingSummary.json"), "w") as f:
    f.write(fxp_json_str)

html_from_JS = transformJS(fxp_json_obj, ACCESSION)
html_from_Py = etree.tostring(transformPy(xml_root, ACCESSION), encoding="unicode", pretty_print=True)
diff_js_to_py = unified_diff(html_from_JS, html_from_Py, "html_from_JS", "html_from_Py")

# print(diff_js_to_py)
with open(os.path.join(os.path.dirname(__file__), "out_diff_js_to_py.txt"), "w") as f:
    f.write(diff_js_to_py)
with open(os.path.join(os.path.dirname(__file__), "out_from_js.htm"), "w") as f:
    f.write(html_from_JS)
with open(os.path.join(os.path.dirname(__file__), "out_from_py.htm"), "w") as f:
    f.write(html_from_Py)