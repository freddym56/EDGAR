# -*- coding: utf-8 -*-
"""
HtmlRenderer — Python translation of InstanceReport_Common.xslt.

Takes an lxml InstanceReport element (already assembled from row/col byte lists)
and produces HTML bytes, eliminating the XSLT dependency entirely.
"""

import os
from html import escape as _esc

# Standard XBRL taxonomy prefixes (matches $standardPrefixes param in XSLT)
_STANDARD_PREFIXES = frozenset([
    'cef', 'country', 'currency', 'dei', 'exch', 'ffd', 'fnd', 'ifrs-full',
    'invest', 'naics', 'oef', 'rr', 'rxp', 'sbs', 'shr', 'sic', 'snj',
    'stpr', 'sro', 'srt', 'us-gaap', 'vip', 'xbrldi', 'xbrldt',
])

_MONTHS = ('', 'January', 'February', 'March', 'April', 'May', 'June',
           'July', 'August', 'September', 'October', 'November', 'December')

_CURRENCY_SYMBOLS = {'USD': '$', 'EUR': '€', 'GBP': '₤'}


# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------

def _t(elem, tag, default=''):
    """Text of a direct child element, or default if absent/empty."""
    child = elem.find(tag)
    return (child.text or '') if child is not None else default


def _is_true(elem, tag):
    return _t(elem, tag).casefold() == 'true'


# ---------------------------------------------------------------------------
# Number / date formatting (mirrors XSLT numFilters / dateFilters)
# ---------------------------------------------------------------------------

def _format_number_int(whole, sep=',', size=3):
    if len(whole) <= size:
        return whole
    cut = len(whole) - size
    return _format_number_int(whole[:cut], sep, size) + sep + whole[cut:]


def _format_numeric(value_str, is_ratio):
    """Format a numeric string: commas, negative parens, ratio as %."""
    negative = value_str.startswith('-')
    entire = value_str[1:] if negative else value_str
    if is_ratio:
        try:
            result = '{:.2f}%'.format(float(entire) * 100)
            return '({})'.format(result) if negative else result
        except ValueError:
            pass
    if entire == 'Infinity':
        return '∞'
    if '.' in entire:
        whole, dec = entire.split('.', 1)
        dec_part = '.' + dec
    else:
        whole, dec_part = entire, ''
    formatted = _format_number_int(whole) if whole else '0'
    result = formatted + dec_part
    return '({})'.format(result) if negative else result


def _format_date(text):
    """YYYY-MM-DD → 'Mon. DD, YYYY' US display format."""
    parts = text.split('-')
    if len(parts) != 3:
        return text
    year, ms, ds = parts
    try:
        month, day = int(ms), int(ds)
    except ValueError:
        return text
    if not (1 <= month <= 12):
        return text
    name = _MONTHS[month]
    abbr = name[:3]
    period = '' if name == 'May' else '.'
    day_str = ' 0{},'.format(day) if day < 10 else '{},'.format(day)
    return '{}{} {} {}'.format(abbr, period, day_str, year)


def _nl2br(text):
    """HTML-escape text and replace newlines with <br>."""
    lines = text.replace('\r\n', '\n').split('\n')
    return '<br>\n '.join(_esc(line) for line in lines)


def _simplify_rating_text(text):
    """Strip Moody's/S&P/Fitch rating member prefix/suffix (legacy XSLT)."""
    for prefix, suffix in [
        ('us-gaap:Moodys', 'RatingMember'),
        ('us-gaap:StandardPoors', 'RatingMember'),
        ('us-gaap:Fitch', 'RatingMember'),
    ]:
        if text.startswith(prefix) and text.endswith(suffix):
            return text[len(prefix):-len(suffix)]
    return text


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render(root_elem, as_page=True, disclaimer=None, disclaimer_style=None,
           css='report.css', js='Show.js', top='top.'):
    """
    Render an lxml InstanceReport element to HTML bytes.

    root_elem may be the document root or the InstanceReport element itself.
    Parameters mirror InstanceReport.xslt / InstanceReport_Common.xslt params.
    """
    ir = root_elem if root_elem.tag == 'InstanceReport' else root_elem.find('InstanceReport')
    if ir is None:
        ir = root_elem

    r = _Renderer(css=css, js=js, top=top)
    out = []

    if as_page:
        out.append('<!DOCTYPE HTML>\n<html>\n   <head>\n')
        out.append('      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n')
        out.append('      <title></title>\n')
        out.append('      <link rel="stylesheet" type="text/css" href="{}">\n'.format(_esc(css)))
        out.append('      <script type="text/javascript" src="{}">/* Do Not Remove This Comment */</script>\n'.format(_esc(js)))
        out.append('      <script type="text/javascript">\n')
        out.append('\t\t\t\tfunction toggleNextSibling (e) {\n')
        out.append('\t\t\t\tif (e.nextSibling.style.display==\'none\') {\n')
        out.append('\t\t\t\te.nextSibling.style.display=\'block\';\n')
        out.append('\t\t\t\t} else { e.nextSibling.style.display=\'none\'; } }</script>\n')
        out.append('   </head>\n   <body>\n')

    r.render_report(ir, out, disclaimer=disclaimer, disclaimer_style=disclaimer_style, is_outer=True)

    if as_page:
        out.append('\n   </body>\n</html>')

    return ''.join(out).encode('utf-8')


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class _Renderer:

    def __init__(self, css='report.css', js='Show.js', top='top.'):
        self.css = css
        self.js = js
        self.top = top

    # ------------------------------------------------------------------ #
    # Report root                                                          #
    # ------------------------------------------------------------------ #

    def render_report(self, ir, out, disclaimer=None, disclaimer_style=None, is_outer=True):
        version = _t(ir, 'Version')
        major_version = int(version.split('.')[0]) if version and version[0].isdigit() else 0

        parent = ir.getparent()
        bar_chart_filename = _t(parent, 'BarChartImageFileName') if parent is not None else ''
        is_table = not bool(bar_chart_filename)

        columns = ir.findall('Columns/Column')
        rows = ir.findall('Rows/Row')
        col_by_id = {_t(c, 'Id'): c for c in columns}

        fn = self._compute_footnotes(columns, rows)

        ctx = dict(
            ir=ir,
            major_version=major_version,
            rounding=bool(_t(ir, 'RoundingOption')),
            show_element_names=_is_true(ir, 'ShowElementNames'),
            display_label_column=(
                _t(ir, 'DisplayLabelColumn') == '' or _is_true(ir, 'DisplayLabelColumn')
            ),
            is_transposed=(_is_true(parent, 'IsTransposed') if parent is not None else False),
            columns=columns,
            rows=rows,
            col_by_id=col_by_id,
            **fn,
        )

        if is_outer:
            out.append('<span style="display: none;">v{}</span>'.format(_esc(version)))

        if disclaimer and disclaimer_style:
            out.append('<p style="{}">{}</p>'.format(_esc(disclaimer_style), _esc(disclaimer)))

        if is_table:
            out.append('<table class="report" border="0" cellspacing="2"')
            if is_outer:
                rn = ir.find('ReportName')
                out.append(' id="{}"'.format('g{}'.format(abs(id(rn)) % 10 ** 9)))
            out.append('>\n')

            if not _is_true(ir, 'HasEmbeddedReports') or is_outer:
                self._render_head(ctx, out)

            self._render_body(ctx, out)

            if is_outer:
                self._render_inner_footnotes(ctx, out)

            out.append('</table>\n')

            if not is_outer:
                self._render_outer_footnotes(ctx, out)

            if is_outer:
                self._render_auth_ref_data(ctx, out)
        else:
            filename = os.path.basename(bar_chart_filename.replace('\\', '/'))
            out.append('<img alt="Bar Chart" src="{}"/>\n'.format(_esc(filename)))
            self._render_outer_footnotes(ctx, out)

    # ------------------------------------------------------------------ #
    # Footnote analysis                                                    #
    # ------------------------------------------------------------------ #

    def _compute_footnotes(self, columns, rows):
        col_head_fn = {}
        col_cell_fn = {}
        for col in columns:
            col_head_fn[_t(col, 'Id')] = bool(_t(col, 'FootnoteIndexer'))
        for row in rows:
            for cell in row.findall('Cells/Cell'):
                if _t(cell, 'FootnoteIndexer'):
                    col_cell_fn[_t(cell, 'Id')] = True

        has_row_fn = any(_t(r, 'FootnoteIndexer') for r in rows)
        cols_with_notes = {cid for cid, v in col_cell_fn.items() if v}
        heads_with_notes = {cid for cid, v in col_head_fn.items() if v}
        any_with_notes = cols_with_notes | heads_with_notes
        has_footnotes = bool(any_with_notes) or has_row_fn

        return dict(
            has_footnotes=has_footnotes,
            any_with_notes=any_with_notes,
            cols_with_notes=cols_with_notes,
            heads_with_notes=heads_with_notes,
            has_row_footnotes=has_row_fn,
        )

    # ------------------------------------------------------------------ #
    # Column headers                                                       #
    # ------------------------------------------------------------------ #

    def _render_head(self, ctx, out):
        columns = ctx['columns']
        rows = ctx['rows']
        ir = ctx['ir']
        show_element_names = ctx['show_element_names']
        display_label_column = ctx['display_label_column']
        rounding = ctx['rounding']
        cols_with_notes = ctx['cols_with_notes']
        heads_with_notes = ctx['heads_with_notes']
        any_with_notes = ctx['any_with_notes']
        has_footnotes = ctx['has_footnotes']

        has_label_footnotes = any(_t(r, 'FootnoteIndexer') for r in rows)
        label_colspan = 2 if has_label_footnotes else 1

        # Check for period grouping (any first-label contains ' Ended')
        def first_label(col):
            lbl = col.find('Labels/Label')
            return lbl.get('Label', '') if lbl is not None else ''

        has_ended = any(' Ended' in first_label(c) for c in columns)
        row_span = 2 if has_ended else 1

        out.append('<tr>\n')

        # Label/name header
        if display_label_column:
            out.append('  <th class="tl" colspan="{}"'.format(label_colspan))
            if show_element_names:
                out.append('>Label</th>\n')
            else:
                out.append(' rowspan="{0}"><div style="width: 200px;"><strong>'
                           '{1}'.format(row_span, _esc(_t(ir, 'ReportName'))))
                if rounding:
                    out.append('<br/>{}'.format(_esc(_t(ir, 'RoundingOption'))))
                out.append('</strong></div></th>\n')

        if show_element_names:
            out.append('  <th class="tl"><strong>Element</strong></th>\n')

        if show_element_names:
            for col in columns:
                col_id = _t(col, 'Id')
                extra = 1 if (col_id in any_with_notes and has_footnotes) else 0
                out.append('  <th class="th" colspan="{}">Value</th>\n'.format(1 + extra))
        elif has_ended:
            self._render_period_group_row(columns, any_with_notes, has_footnotes, first_label, out)
        else:
            for col in columns:
                self._render_col_header(col, cols_with_notes, out)

        out.append('</tr>\n')

        # Second header row for individual dates when period grouping active
        if not show_element_names and has_ended:
            out.append('<tr>\n')
            for col in columns:
                if _is_true(col, 'LabelColumn'):
                    continue
                self._render_col_header(col, cols_with_notes, out)
            out.append('</tr>\n')

    def _render_period_group_row(self, columns, any_with_notes, has_footnotes, first_label_fn, out):
        # Collapse contiguous columns with the same first label
        groups = []
        for col in columns:
            lbl = first_label_fn(col)
            col_id = _t(col, 'Id')
            if groups and groups[-1][0] == lbl:
                groups[-1][1].append(col_id)
            else:
                groups.append([lbl, [col_id]])

        for lbl, col_ids in groups:
            extra = sum(1 for cid in col_ids if cid in any_with_notes and has_footnotes)
            colspan = len(col_ids) + extra
            if ' Ended' in lbl:
                out.append('  <th class="th" colspan="{}">{}</th>\n'.format(colspan, _esc(lbl)))
            else:
                out.append('  <th class="th" colspan="{}"></th>\n'.format(colspan))

    def _render_col_header(self, col, cols_with_notes, out):
        col_id = _t(col, 'Id')
        has_cell_fn = col_id in cols_with_notes
        fn_text = _t(col, 'FootnoteIndexer')
        has_head_fn = bool(fn_text)

        out.append('  <th class="th"')
        if has_cell_fn and not has_head_fn:
            out.append(' colspan="2"')
        out.append('>\n')

        labels = col.findall('Labels/Label')
        non_ended = [l for l in labels if ' Ended' not in l.get('Label', '')]
        sep = _t(col, 'LabelSeparator')
        for i, lbl_elem in enumerate(non_ended):
            lbl_text = lbl_elem.get('Label', '')
            suffix = sep if i < len(non_ended) - 1 else ''
            out.append('    <div>{}{}</div>\n'.format(_esc(lbl_text), _esc(suffix)))

        out.append('  </th>\n')

        if has_head_fn:
            out.append('  <th class="th"><sup>{}</sup></th>\n'.format(_esc(fn_text)))

    # ------------------------------------------------------------------ #
    # Table body (rows)                                                   #
    # ------------------------------------------------------------------ #

    def _render_body(self, ctx, out):
        rows = ctx['rows']
        report_name = _t(ctx['ir'], 'ReportName')

        for pos, row in enumerate(rows, start=1):
            if _is_true(row, 'IsReportTitle'):
                continue
            # Skip first segment title that merely repeats the report name
            label = _t(row, 'Label')
            if pos == 1 and _is_true(row, 'IsSegmentTitle') and report_name in label:
                continue

            self._render_row(ctx, row, pos, out)

            if _is_true(row, 'IsSubReportEnd') and pos < len(rows):
                next_row = rows[pos]  # pos is 1-based, rows is 0-based → rows[pos] = next
                if not _is_true(next_row, 'IsSegmentTitle'):
                    self._render_break(ctx, out)

    def _render_row(self, ctx, row, pos, out):
        display_label_column = ctx['display_label_column']
        show_element_names = ctx['show_element_names']
        columns = ctx['columns']
        cols_with_notes = ctx['cols_with_notes']
        heads_with_notes = ctx['heads_with_notes']
        has_footnotes = ctx['has_footnotes']
        has_row_fn = ctx['has_row_footnotes']

        is_segment = _is_true(row, 'IsSegmentTitle')
        is_report_title = _is_true(row, 'IsReportTitle')
        is_calendar = _is_true(row, 'IsCalendarTitle')
        is_total = _is_true(row, 'IsTotalLabel')
        element_prefix = _t(row, 'ElementPrefix')

        if is_segment or is_report_title:
            row_class = 'rh'
        elif is_calendar:
            row_class = 'rc'
        elif pos % 2 == 1:  # XSLT: (position()+1) mod 2 = 0 for pos=1,3,5…
            row_class = 'reu' if is_total else 're'
        else:
            row_class = 'rou' if is_total else 'ro'

        out.append('<tr class="{}">\n'.format(row_class))

        # Is the element a custom (non-standard) prefix?
        prefix_token = element_prefix.split('_')[0] if '_' in element_prefix else element_prefix.rstrip('_')
        is_custom = (
            not is_segment and
            not _is_true(row, 'IsAbstractGroupTitle') and
            prefix_token not in _STANDARD_PREFIXES
        )
        custom_class = ' custom' if is_custom else ''

        if display_label_column:
            out.append('  <td class="pl{}" style="border-bottom: 0px;" valign="top">\n'.format(custom_class))
            self._render_auth_ref_link(row, ctx, out)
            out.append('  </td>\n')
            if has_row_fn:
                fn = _t(row, 'FootnoteIndexer')
                out.append('  <td class="th" style="border-bottom: 0px;"><sup>{}</sup></td>\n'.format(_esc(fn)))

        if show_element_names:
            out.append('  <td class="th" style="border-bottom: 0px;">{}</td>\n'.format(
                _esc(_t(row, 'ElementName'))))

        # Build a cell-id → cell element lookup for this row
        cells = {_t(c, 'Id'): c for c in row.findall('Cells/Cell')}
        for col in columns:
            col_id = _t(col, 'Id')
            self._render_cell(cells.get(col_id), col_id, ctx, out)

        out.append('</tr>\n')

    def _render_break(self, ctx, out):
        columns = ctx['columns']
        cols_with_notes = ctx['cols_with_notes']
        n_fn = sum(1 for c in columns if _t(c, 'Id') in cols_with_notes)
        colspan = len(columns) + n_fn + 1
        out.append('<tr><td colspan="{}" style="height: 1em;"><hr/></td></tr>\n'.format(colspan))

    # ------------------------------------------------------------------ #
    # Auth ref link (row label content)                                   #
    # ------------------------------------------------------------------ #

    def _render_auth_ref_link(self, row, ctx, out):
        is_transposed = ctx['is_transposed']
        top = self.top
        major_version = ctx['major_version']

        is_abstract = _is_true(row, 'IsAbstractGroupTitle')
        is_report_title = _is_true(row, 'IsReportTitle')
        element_name = _t(row, 'ElementName')
        label = _t(row, 'Label').strip()
        level = _t(row, 'Level', '0')

        label_html = '<strong>{}</strong>'.format(_esc(label)) if is_abstract else _esc(label)
        style = ' style="margin-left: {}em;"'.format(level) if level and level != '0' else ''

        if is_transposed or is_report_title or not element_name:
            out.append('    <div class="a"{}>{}</div>\n'.format(style, label_html))
        else:
            ref = 'defref_{}'.format(element_name)
            out.append(
                '    <a class="a" href="javascript:void(0);"'
                ' onclick="{top}Show.showAR( this, \'{ref}\', window );"'
                '>{label}</a>\n'.format(top=top, ref=ref, label=label_html)
            )

    # ------------------------------------------------------------------ #
    # Cell rendering                                                       #
    # ------------------------------------------------------------------ #

    def _render_cell(self, cell, col_id, ctx, out):
        cols_with_notes = ctx['cols_with_notes']
        heads_with_notes = ctx['heads_with_notes']
        has_footnotes = ctx['has_footnotes']
        rounding = ctx['rounding']
        col_by_id = ctx['col_by_id']
        major_version = ctx['major_version']

        in_cols = col_id in cols_with_notes
        in_heads = col_id in heads_with_notes

        # The cell <td> gets colspan=2 when the column spans a header footnote
        # column but has no cell footnotes
        colspan = ' colspan="2"' if (has_footnotes and in_heads and not in_cols) else ''

        if cell is None:
            out.append('  <td{}><span>&nbsp;</span></td>\n'.format(colspan))
            if in_cols:
                out.append('  <td class="fn" style="border-bottom: 0px;"></td>\n')
            return

        embedded_ir = cell.find('EmbeddedReport/InstanceReport')
        if embedded_ir is not None:
            out.append('  <td{}>\n'.format(colspan))
            self.render_report(embedded_ir, out, is_outer=False)
            out.append('  <span>&nbsp;</span></td>\n')
        elif _t(cell, 'IsNumeric') == 'true':
            self._render_numeric_td(cell, col_id, col_by_id, rounding, colspan, out)
        else:
            self._render_text_td(cell, major_version, colspan, out)

        # Extra footnote column
        if in_cols:
            fn = ''
            is_numeric = _t(cell, 'IsNumeric') == 'true'
            non_num = _t(cell, 'NonNumbericText')
            fn_text = _t(cell, 'FootnoteIndexer')
            if (is_numeric or non_num) and fn_text:
                fn = fn_text
            out.append('  <td class="fn" style="border-bottom: 0px;"><sup>{}</sup></td>\n'.format(_esc(fn)))

    def _render_text_td(self, cell, major_version, colspan, out):
        display_date = _is_true(cell, 'DisplayDateInUSFormat')
        text = _t(cell, 'NonNumbericText')

        out.append('  <td class="text"{}>'.format(colspan))
        if not text:
            out.append('&#160;')
        elif display_date:
            out.append(_esc(_format_date(text)))
        else:
            if major_version < 3:
                text = _simplify_rating_text(text)
            # NonNumbericText may contain raw HTML (text-block facts); output verbatim
            out.append(text)
        out.append('<span>&nbsp;</span></td>\n')

    def _render_numeric_td(self, cell, col_id, col_by_id, rounding, colspan, out):
        if _is_true(cell, 'DisplayZeroAsNone') and _t(cell, 'NumericAmount') == '0':
            out.append('  <td class="nump"{}>none<span>&nbsp;</span></td>\n'.format(colspan))
            return

        is_ratio = _is_true(cell, 'IsRatio')
        numeric = _t(cell, 'RoundedNumericAmount') if rounding else _t(cell, 'NumericAmount')

        try:
            amount = float(_t(cell, 'NumericAmount'))
        except ValueError:
            amount = 0.0
        td_class = 'nump' if amount >= 0 else 'num'

        out.append('  <td class="{}"{}>'.format(td_class, colspan))

        if _is_true(cell, 'ShowCurrencySymbol'):
            out.append(_esc(self._lookup_currency(cell, col_id, col_by_id)))

        out.append(_esc(_format_numeric(numeric, is_ratio)))
        out.append('<span>&nbsp;</span></td>\n')

    def _lookup_currency(self, cell, col_id, col_by_id):
        if _is_true(cell, 'IsIndependantCurrency'):
            code = _t(cell, 'CurrencyCode')
            return _CURRENCY_SYMBOLS.get(code, code) + ' '
        col = col_by_id.get(col_id)
        if col is not None:
            code_elem = col.find('CurrencySymbol/Code')
            if code_elem is not None and code_elem.text:
                return code_elem.text + ' '
            sym = _t(col, 'CurrencySymbol')
            if sym:
                return sym + ' '
        return ''

    # ------------------------------------------------------------------ #
    # Footnote sections                                                    #
    # ------------------------------------------------------------------ #

    def _render_inner_footnotes(self, ctx, out):
        footnotes = ctx['ir'].findall('Footnotes/Footnote')
        if not footnotes:
            return
        columns = ctx['columns']
        any_with_notes = ctx['any_with_notes']
        has_row_fn = ctx['has_row_footnotes']
        n_fn = sum(1 for c in columns if _t(c, 'Id') in any_with_notes)
        row_idxs = 2 if has_row_fn else 1
        colspan = len(columns) + n_fn + row_idxs

        out.append('<tr><td colspan="{}"></td></tr>\n'.format(colspan))
        out.append('<tr><td colspan="{}">\n'.format(colspan))
        self._render_outer_footnotes(ctx, out)
        out.append('</td></tr>\n')

    def _render_outer_footnotes(self, ctx, out):
        footnotes = ctx['ir'].findall('Footnotes/Footnote')
        if not footnotes:
            return
        out.append('<table class="outerFootnotes" width="100%">\n')
        for fn in footnotes:
            note_id = _t(fn, 'NoteId')
            note = _t(fn, 'Note')
            out.append('<tr class="outerFootnote">\n')
            out.append('  <td style="vertical-align: top; width: 12pt;" valign="top">[{}]</td>\n'.format(
                _esc(note_id)))
            # Note text may contain HTML (disable-output-escaping in XSLT)
            out.append('  <td style="vertical-align: top;" valign="top">{}</td>\n'.format(note))
            out.append('</tr>\n')
        out.append('</table>\n')

    # ------------------------------------------------------------------ #
    # Auth ref data (hidden definition popup tables)                      #
    # ------------------------------------------------------------------ #

    def _render_auth_ref_data(self, ctx, out):
        ir = ctx['ir']
        top = self.top
        has_embedded = _is_true(ir, 'HasEmbeddedReports')

        row_source = ir.findall('.//Row') if has_embedded else ir.findall('Rows/Row')
        seg_source = (
            ir.findall('.//Segment[IsDefaultForEntity!="true"]/DimensionInfo')
            if has_embedded else
            ir.findall('Rows/Row/MCU/contextRef/Segments/Segment[IsDefaultForEntity!="true"]/DimensionInfo')
        )

        out.append('<div style="display: none;">\n')

        seen_elements = set()
        for row in sorted(row_source, key=lambda r: _t(r, 'ElementName')):
            name = _t(row, 'ElementName')
            if name and name not in seen_elements:
                seen_elements.add(name)
                self._render_auth_ref_table(row, name, top, out)

        seen_dims = set()
        for dim_info in seg_source:
            dim_id = _t(dim_info, 'dimensionId')
            mem_id = _t(dim_info, 'Id')
            key = (dim_id, mem_id)
            if key not in seen_dims:
                seen_dims.add(key)
                ref_name = '{}={}'.format(
                    dim_id.replace(':', '_'), mem_id.replace(':', '_'))
                parent_row = dim_info.getparent()
                while parent_row is not None and parent_row.tag != 'Row':
                    parent_row = parent_row.getparent()
                if parent_row is not None:
                    self._render_auth_ref_table(parent_row, ref_name, top, out)

        out.append('</div>\n')

    def _render_auth_ref_table(self, row, name, top, out):
        definition = _t(row, 'ElementDefenition')
        references = _t(row, 'ElementReferences')
        has_def = bool(definition) and definition != 'No definition available.'
        has_ref = bool(references) and references != 'No authoritative reference available.'

        first = 'ElementDefenition' if has_def else ('ElementReferences' if has_ref else 'Details')

        out.append('<table border="0" cellpadding="0" cellspacing="0" class="authRefData"'
                   ' style="display: none;" id="defref_{}">\n'.format(_esc(name)))
        out.append('<tr><td class="hide">'
                   '<a style="color: white;" href="javascript:void(0);"'
                   ' onclick="{top}Show.hideAR();">X</a>'
                   '</td></tr>\n'.format(top=top))
        out.append('<tr><td><div class="body" style="padding: 2px;">\n')

        if has_def:
            toggle = '- Definition' if first == 'ElementDefenition' else '+ Definition'
            hidden = '' if first == 'ElementDefenition' else ' style="display: none;"'
            out.append('<a href="javascript:void(0);" onclick="{top}Show.toggleNext( this );">'
                       '{t}</a>\n<div{h}><p>{d}</p></div>\n'.format(
                           top=top, t=toggle, h=hidden, d=_esc(definition)))

        if has_ref:
            toggle = '- References' if first == 'ElementReferences' else '+ References'
            hidden = '' if first == 'ElementReferences' else ' style="display: none;"'
            out.append('<a href="javascript:void(0);" onclick="{top}Show.toggleNext( this );">'
                       '{t}</a>\n<div{h}><p>{r}</p></div>\n'.format(
                           top=top, t=toggle, h=hidden, r=_nl2br(references)))

        toggle = '- Details' if first == 'Details' else '+ Details'
        hidden = '' if first == 'Details' else ' style="display: none;"'
        data_type = _t(row, 'ElementDataType') or 'na'
        out.append('<a href="javascript:void(0);" onclick="{top}Show.toggleNext( this );">'
                   '{t}</a>\n<div{h}>\n'.format(top=top, t=toggle, h=hidden))
        out.append('<table border="0" cellpadding="0" cellspacing="0">\n')
        out.append('<tr><td><strong> Name:</strong></td>'
                   '<td style="white-space:nowrap;">{}</td></tr>\n'.format(_esc(name)))
        out.append('<tr><td style="padding-right: 4px;white-space:nowrap;">'
                   '<strong> Namespace Prefix:</strong></td>'
                   '<td>{}</td></tr>\n'.format(_esc(_t(row, 'ElementPrefix'))))
        out.append('<tr><td><strong> Data Type:</strong></td>'
                   '<td>{}</td></tr>\n'.format(_esc(data_type)))
        out.append('<tr><td><strong> Balance Type:</strong></td>'
                   '<td>{}</td></tr>\n'.format(_esc(_t(row, 'BalanceType'))))
        out.append('<tr><td><strong> Period Type:</strong></td>'
                   '<td>{}</td></tr>\n'.format(_esc(_t(row, 'PeriodType'))))
        out.append('</table>\n</div>\n</div></td></tr></table>\n')
