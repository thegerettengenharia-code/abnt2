"""Corrige a formatação de um documento .docx NO LUGAR, preservando a template.

Fluxo:
1. Ajusta as propriedades de estilo (Normal, títulos) e as páginas/secções.
2. Classifica cada parágrafo (título, corpo, citação longa, legenda, fonte,
   referência, resumo) e aplica a formatação ABNT correspondente.
3. Formata tabelas (sem bordas laterais nem verticais internas).
4. Aplica a numeração de páginas (oculta no pré-textual, arábica a partir da
   Introdução, contando desde a folha de rosto).
5. Formata notas de rodapé (fonte 10, espaçamento simples, separador 5 cm).

Nada de conteúdo é reescrito: apenas a formatação é alterada. As alterações
são registradas para o relatório.
"""
import copy
import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import classify, config

_BLACK = RGBColor(*config.BLACK)
_HEADING_CHANGES: list[str] = []


def _uppercase_text(text):
    letters = sum(1 for ch in text if ch.isalpha())
    if letters == 0:
        return text
    upper = sum(1 for ch in text if ch.isalpha() and ch.isupper())
    if upper / letters >= 0.9:
        return text
    return text.upper()


def _uppercase_paragraph(paragraph):
    runs = [r for r in paragraph.runs if (r.text or "").strip()]
    if not runs:
        return
    full = "".join(r.text for r in runs)
    new = _uppercase_text(full)
    if new != full:
        runs[0].text = new
        for run in runs[1:]:
            run.text = ""


_THEME_FONT_ATTRS = ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme")


def _kill_theme_rfonts(rpr):
    """Remove atributos de tema que sobrepõem a fonte explícita (OOXML).

    Quando w:asciiTheme / w:hAnsiTheme / w:eastAsiaTheme / w:cstheme estão
    presentes no mesmo rPr, o Word/LibreOffice usa a fonte do tema e ignora
    w:ascii/hAnsi. Para ABNT (Arial/TNR, cor preta), precisamos removê-los.
    """
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is not None:
        for attr in _THEME_FONT_ATTRS:
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]
    color = rpr.find(qn("w:color"))
    if color is not None and color.get(qn("w:themeColor")) is not None:
        del color.attrib[qn("w:themeColor")]


def _set_run_font(run, font_name: str, size: int | None = None, bold: bool | None = None):
    run.font.name = font_name
    rpr = run._element.get_or_add_rPr()
    _kill_theme_rfonts(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), font_name)
    run.font.color.rgb = _BLACK
    if size is not None:
        run.font.size = Pt(size)
        _set_szcs(rpr, size)
    if bold is not None:
        run.font.bold = bold


def _set_szcs(rpr, size):
    szcs = rpr.find(qn("w:szCs"))
    if szcs is None:
        szcs = OxmlElement("w:szCs")
        rpr.append(szcs)
    szcs.set(qn("w:val"), str(int(size * 2)))


def _set_style_font(style, font_name: str, size: int | None = None):
    style.font.name = font_name
    rpr = style.element.get_or_add_rPr()
    _kill_theme_rfonts(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), font_name)
    style.font.color.rgb = _BLACK
    if size is not None:
        style.font.size = Pt(size)
        _set_szcs(rpr, size)


def _style_name_key(name):
    return classify.normalize(name or "")


def _clear_indent(pf):
    pf.left_indent = None
    pf.right_indent = None
    pf.first_line_indent = None


def _apply_paragraph(paragraph, kind, font_name, changes, note=None):
    pf = paragraph.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.page_break_before = False

    if kind == "heading_numbered":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        _clear_indent(pf)
        pf.line_spacing = config.LINE_SPACING
        pf.keep_with_next = True
        if classify.heading_level(paragraph) == 1:
            pf.page_break_before = True  # secção primária em nova página
        size, bold = config.TEXT_SIZE, True
    elif kind == "heading_unnumbered":
        # errata, agradecimentos, resumo, sumário, referências, glossário,
        # apêndice, anexo, índice, listas: centralizado, negrito, MAIÚSCULAS,
        # em nova página.
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _clear_indent(pf)
        pf.line_spacing = config.LINE_SPACING
        pf.keep_with_next = True
        pf.page_break_before = True
        _uppercase_paragraph(paragraph)
        size, bold = config.TEXT_SIZE, True
    elif kind == "quote":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.left_indent = Cm(config.QUOTE_INDENT_CM)
        pf.right_indent = None
        pf.first_line_indent = None
        pf.line_spacing = config.SINGLE_SPACING
        size, bold = config.SMALL_SIZE, False
        changes.quotes += 1
    elif kind in ("caption", "source"):
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _clear_indent(pf)
        pf.line_spacing = config.SINGLE_SPACING
        size, bold = config.SMALL_SIZE, False
        if kind == "caption":
            changes.captions += 1
        else:
            changes.sources += 1
    elif kind == "reference":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        _clear_indent(pf)
        pf.line_spacing = config.SINGLE_SPACING
        pf.space_after = Pt(config.REFERENCE_SPACE_AFTER_PT)  # linha em branco entre cada
        size, bold = config.TEXT_SIZE, False
    elif kind in ("resumo", "abstract"):
        # parágrafo único, sem recuo, espaçamento simples
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.first_line_indent = None
        pf.left_indent = None
        pf.line_spacing = config.SINGLE_SPACING
        size, bold = config.TEXT_SIZE, False
    elif kind == "list":
        pf.line_spacing = config.LINE_SPACING
        pf.first_line_indent = None
        size, bold = config.TEXT_SIZE, False
    elif kind == "pre":
        pf.line_spacing = config.LINE_SPACING
        size, bold = config.TEXT_SIZE, False
    else:  # body
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.first_line_indent = Cm(config.FIRST_LINE_INDENT_CM)
        pf.left_indent = None
        pf.line_spacing = config.LINE_SPACING
        size, bold = config.TEXT_SIZE, False

    for run in paragraph.runs:
        _set_run_font(run, font_name, size, bold)


def _configure_doc_defaults(doc, font_name):
    """Nivela os docDefaults ao modelo ABNT (TNR 12, 1,5, justificado, recuo).

    Isto cobre qualquer parágrafo/run sem formatação direta, espelhando o
    `modelo_abnt_em_branco.docx`.
    """
    try:
        styles_el = doc.styles.element
    except Exception:
        return
    defaults = styles_el.find(qn("w:docDefaults"))
    if defaults is None:
        defaults = OxmlElement("w:docDefaults")
        styles_el.insert(0, defaults)

    rpr_default = defaults.find(qn("w:rPrDefault"))
    if rpr_default is None:
        rpr_default = OxmlElement("w:rPrDefault")
        defaults.insert(0, rpr_default)
    rpr = rpr_default.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        rpr_default.append(rpr)

    _kill_theme_rfonts(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), font_name)

    color = rpr.find(qn("w:color"))
    if color is None:
        color = OxmlElement("w:color")
        rpr.append(color)
    color.set(qn("w:val"), "000000")

    sz = rpr.find(qn("w:sz"))
    if sz is None:
        sz = OxmlElement("w:sz")
        rpr.append(sz)
    sz.set(qn("w:val"), str(config.TEXT_SIZE * 2))
    _set_szcs(rpr, config.TEXT_SIZE)

    ppr_default = defaults.find(qn("w:pPrDefault"))
    if ppr_default is None:
        ppr_default = OxmlElement("w:pPrDefault")
        defaults.append(ppr_default)
    ppr = ppr_default.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr")
        ppr_default.append(ppr)
    spacing = ppr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        ppr.append(spacing)
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "0")
    spacing.set(qn("w:line"), str(int(config.LINE_SPACING * 240)))
    spacing.set(qn("w:lineRule"), "auto")
    ind = ppr.find(qn("w:ind"))
    if ind is None:
        ind = OxmlElement("w:ind")
        ppr.append(ind)
    ind.set(qn("w:firstLine"), str(int(config.FIRST_LINE_INDENT_CM * 567)))
    jc = ppr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        ppr.append(jc)
    jc.set(qn("w:val"), "both")


def _configure_styles(doc, font_name):
    heading_like = ("heading", "título", "titulo", "title", "subtitle",
                    "subtitulo", "subtítulo", "toc heading", "toc 1")
    plain_like = ("hyperlink", "list paragraph", "footer", "header",
                  "footnote text", "endnote text", "caption",
                  "footnote reference", "endnote reference", "quote")

    for style in doc.styles:
        try:
            key = _style_name_key(getattr(style, "name", ""))
            if key == "normal":
                _set_style_font(style, font_name, config.TEXT_SIZE)
                pf = style.paragraph_format
                pf.line_spacing = config.LINE_SPACING
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)
                pf.first_line_indent = Cm(config.FIRST_LINE_INDENT_CM)
                pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            elif any(key.startswith(h) for h in heading_like):
                _set_style_font(style, font_name, config.TEXT_SIZE)
                style.font.bold = True
                pf = style.paragraph_format
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)
                pf.line_spacing = config.LINE_SPACING
            elif any(key.startswith(p) for p in plain_like):
                # estilos auxiliares mantêm o tamanho previsto pela regra
                target = config.TEXT_SIZE
                if key.startswith(("footnote", "endnote", "caption", "header", "footer")):
                    target = config.SMALL_SIZE
                _set_style_font(style, font_name, target)
                if key.startswith("hyperlink"):
                    style.font.underline = False
        except Exception:
            continue


def _configure_mirror_margins(doc):
    """Ativa margens espelhadas (frente/verso) nas configurações do documento.

    Com mirrorMargins, os campos esquerda/direita das margens passam a ser
    interna (lombada) / externa. Portanto:
      anverso: esquerda=3, direita=2 · verso: esquerda=2, direita=3.
    """
    try:
        settings = doc.settings.element
    except Exception:
        return
    if settings.find(qn("w:mirrorMargins")) is None:
        mirror = OxmlElement("w:mirrorMargins")
        try:
            settings.insert_element_before(mirror, "w:compat", "w:docVars", "w:rsids")
        except Exception:
            settings.append(mirror)


def _configure_sections(doc):
    for section in doc.sections:
        section.page_width = Cm(config.PAGE_WIDTH_CM)
        section.page_height = Cm(config.PAGE_HEIGHT_CM)
        section.top_margin = Cm(config.MARGIN_TOP_CM)
        section.left_margin = Cm(config.MARGIN_INSIDE_CM)
        section.bottom_margin = Cm(config.MARGIN_BOTTOM_CM)
        section.right_margin = Cm(config.MARGIN_OUTSIDE_CM)
        section.header_distance = Cm(config.PAGE_NUMBER_DISTANCE_CM)
        section.footer_distance = Cm(config.PAGE_NUMBER_DISTANCE_CM)


def _has_border(tbl_borders, name):
    el = tbl_borders.find(qn(f"w:{name}"))
    if el is None:
        return False
    val = (el.get(qn("w:val")) or "").lower()
    return val not in ("none", "nil", "off")


def format_tables(doc):
    """Remove bordas laterais e verticais internas (NBR 14724).

    Mantém apenas bordas horizontais: topo, fundo e internas horizontais.
    """
    count = 0
    for table in doc.tables:
        tbl = table._tbl
        for tbl_pr in tbl.findall(qn("w:tblPr")):
            borders = tbl_pr.find(qn("w:tblBorders"))
            if borders is None:
                continue
            touched = False
            for name in ("left", "right", "insideV"):
                if not _has_border(borders, name):
                    continue
                old = borders.find(qn(f"w:{name}"))
                borders.remove(old)
                none_el = OxmlElement(f"w:{name}")
                none_el.set(qn("w:val"), "none")
                none_el.set(qn("w:sz"), "0")
                none_el.set(qn("w:space"), "0")
                none_el.set(qn("w:color"), "auto")
                borders.append(none_el)
                touched = True
            if touched:
                count += 1
    return count


def _format_footnote_part(element, font_name):
    changed = False
    for p in element.iter(qn("w:p")):
        ppr = p.find(qn("w:pPr"))
        if ppr is None:
            ppr = OxmlElement("w:pPr")
            p.insert(0, ppr)
        spacing = ppr.find(qn("w:spacing"))
        if spacing is None:
            spacing = OxmlElement("w:spacing")
            ppr.append(spacing)
        spacing.set(qn("w:line"), str(int(config.SINGLE_SPACING * 240)))
        spacing.set(qn("w:lineRule"), "auto")
        for r in p.iter(qn("w:r")):
            rpr = r.find(qn("w:rPr"))
            if rpr is None:
                rpr = OxmlElement("w:rPr")
                r.insert(0, rpr)
            rfonts = rpr.find(qn("w:rFonts"))
            if rfonts is None:
                rfonts = OxmlElement("w:rFonts")
                rpr.insert(0, rfonts)
            for attr in ("w:ascii", "w:hAnsi", "w:cs"):
                rfonts.set(qn(attr), font_name)
            sz = rpr.find(qn("w:sz"))
            if sz is None:
                sz = OxmlElement("w:sz")
                rpr.append(sz)
            sz.set(qn("w:val"), str(config.SMALL_SIZE * 2))
            szcs = rpr.find(qn("w:szCs"))
            if szcs is None:
                szcs = OxmlElement("w:szCs")
                rpr.append(szcs)
            szcs.set(qn("w:val"), str(config.SMALL_SIZE * 2))
        changed = True
    return changed


def _set_footnote_separator(element):
    """Garante que o separador de notas tenha o traço e recua 5 cm à esquerda."""
    changed = False
    for fn in element.findall(qn("w:footnote")):
        ftype = fn.get(qn("w:type"))
        if ftype not in ("separator", "continuationSeparator"):
            continue
        for p in fn.findall(qn("w:p")):
            ppr = p.find(qn("w:pPr"))
            if ppr is None:
                ppr = OxmlElement("w:pPr")
                p.insert(0, ppr)
            ind = ppr.find(qn("w:ind"))
            if ind is None:
                ind = OxmlElement("w:ind")
                ppr.append(ind)
            ind.set(qn("w:left"), "0")
            ind.remove(qn("w:hanging")) if ind.get(qn("w:hanging")) else None

            # Recria o run com o traço de 5 cm
            for r in list(p.findall(qn("w:r"))):
                p.remove(r)
            run = OxmlElement("w:r")
            sep = OxmlElement("w:separator")
            run.append(sep)
            p.append(run)
            changed = True
    return changed


def format_footnotes(doc, font_name):
    footnoted = False
    separator_done = False
    for part in doc.part.package.parts:
        name = str(getattr(part, "partname", ""))
        element = getattr(part, "element", None)
        if element is None:
            continue
        if name.endswith("/footnotes.xml") or name.endswith("/endnotes.xml"):
            if _format_footnote_part(element, font_name):
                footnoted = True
        if name.endswith("/footnotes.xml"):
            if _set_footnote_separator(element):
                separator_done = True
    if separator_done:
        return 2 if footnoted else 1
    return 1 if footnoted else 0


def _set_pgnum(sectpr, fmt, start):
    existing = sectpr.find(qn("w:pgNumType"))
    if existing is not None:
        sectpr.remove(existing)
    if start is None and fmt is None:
        return  # continuar a contagem
    el = OxmlElement("w:pgNumType")
    el.set(qn("w:fmt"), fmt if fmt else "decimal")
    if start is not None:
        el.set(qn("w:start"), str(start))
    try:
        sectpr.insert_element_before(
            el,
            "w:cols", "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
            "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid",
            "w:printerSettings", "w:sectPrChange",
        )
    except Exception:
        sectpr.append(el)


def _clear_pgnum(sectpr):
    existing = sectpr.find(qn("w:pgNumType"))
    if existing is not None:
        sectpr.remove(existing)


def _strip_header(header):
    for p in header.paragraphs:
        for r in list(p.runs):
            r._element.getparent().remove(r._element)


def _add_page_field(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    for el in (fld_begin, instr, fld_sep, txt, fld_end):
        run._element.append(el)
    return run


def _set_page_header(header, font_name):
    header.is_linked_to_previous = False
    if not header.paragraphs:
        paragraph = header.add_paragraph()
    else:
        paragraph = header.paragraphs[0]
    for existing in list(paragraph.runs):
        existing._element.getparent().remove(existing._element)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.paragraph_format.first_line_indent = None
    paragraph.paragraph_format.line_spacing = config.SINGLE_SPACING
    run = _add_page_field(paragraph)
    _set_run_font(run, font_name, config.SMALL_SIZE)


def _set_blank_header(header):
    header.is_linked_to_previous = False
    _strip_header(header)
    if header.paragraphs:
        header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT


def _configure_headers(doc, font_name):
    """Oculta o número no pré-textual; exibe arábico a partir da Introdução.

    Conta as folhas a partir da folha de rosto (a capa não conta): por
    heurística, o primeiro parágrafo do documento inicia uma secção com
    ``start=0`` para a capa.
    """
    intro_index = None
    for i, paragraph in enumerate(doc.paragraphs):
        if classify.is_heading(paragraph) and classify.chapter_key(
            paragraph.text.strip()
        ) == "Introdução":
            intro_index = i
            break

    sections = doc.sections
    for section in sections:
        section.header.is_linked_to_previous = False
        _set_blank_header(section.header)

    if intro_index is not None and intro_index > 0:
        prev = doc.paragraphs[intro_index - 1]._p
        final_sectpr = sections[-1]._sectPr

        pre_sectpr = copy.deepcopy(final_sectpr)
        _set_pgnum(pre_sectpr, None, None)  # sem reinício: continua do documento
        prev.get_or_add_pPr().append(pre_sectpr)
        _set_pgnum(final_sectpr, "decimal", None)  # continua do pré-textual

        # capa: não conta. Heurística -> 1º parágrafo abre secção com start=0
        if len(doc.paragraphs) > 0:
            first = doc.paragraphs[0]._p
            capa_sectpr = copy.deepcopy(final_sectpr)
            _set_pgnum(capa_sectpr, "decimal", 0)
            first.get_or_add_pPr().append(capa_sectpr)
        # Exibe o número a partir da Introdução (secção final/listada por último).
        _set_page_header(sections[-1].header, font_name)
        return True

    # Sem "Introdução": exibe em arábico desde o início
    for section in sections:
        _set_page_header(section.header, font_name)
    final_sectpr = sections[-1]._sectPr
    _set_pgnum(final_sectpr, "decimal", 1)
    return False


# ---------------------------------------------------------------------------
# Títulos


def _heading_number(paragraph, counters, level, text, key):
    if classify.unnumbered_title(text) is not None:
        for i in range(1, 5):
            counters[i] = 0
        return
    level = max(1, min(level, 4))
    for deeper in range(level + 1, 5):
        counters[deeper] = 0
    counters[level] += 1
    number = ".".join(str(counters[i]) for i in range(1, level + 1))
    # Remove numeração existente (com ponto/hífen residual) antes de inserir.
    # Para efeito no primeiro run NÃO vazio — Word costuma criar runs vazios.
    runs = [r for r in paragraph.runs if (r.text or "").strip()]
    if runs:
        cleaned = re.sub(r"^\s*\d+(?:\.\d+)*[.)-]?\s*", "", runs[0].text)
        runs[0].text = f"{number} {cleaned}"
    else:
        paragraph.add_run(f"{number} ")
    _HEADING_CHANGES.append(f"{number} {text}")


# ---------------------------------------------------------------------------
# Ajuste principal


    line_spacing = 1.5 if line_spacing == "1,5" else 1.0
    _configure_styles(doc, font_name, line_spacing)
    _configure_doc_defaults(doc, font_name, line_spacing)
    _configure_mirror_margins(doc)
    _configure_sections(doc)

    counters = {1: 0, 2: 0, 3: 0, 4: 0}
    _HEADING_CHANGES.clear()
   

    counters = {1: 0, 2: 0, 3: 0, 4: 0}
    _HEADING_CHANGES.clear()

    mode = "body"
    seen_intro = False

    has_intro = any(
        classify.is_heading(p) and classify.chapter_key(p.text.strip()) == "Introdução"
        for p in doc.paragraphs
    )

    for paragraph in doc.paragraphs:
        text = (paragraph.text or "").strip()
        if not text:
            _format_empty(paragraph, font_name)
            continue

        if classify.is_source(text):
            kind = "source"
        elif classify.is_caption(text):
            kind = "caption"
        elif classify.is_display_style(paragraph):
            # capa/folha de rosto: preservar o visual, só padronizar a fonte
            kind = "pre"
        elif classify.is_heading(paragraph):
            key = classify.chapter_key(text)
            unnum = classify.unnumbered_title(text)

            if unnum is not None:
                if unnum in ("Resumo", "Abstract"):
                    mode = "resumo" if classify.normalize(unnum) == "resumo" else "abstract"
                elif unnum in config.REFERENCE_TITLES:
                    mode = "reference"
                else:
                    mode = "body"
                level = classify.heading_level(paragraph)
                _heading_number(paragraph, counters, level, text, key)
                kind = "heading_unnumbered"
            else:
                if key == "Referências":
                    mode = "reference"
                elif key in ("Resumo", "Abstract"):
                    mode = classify.normalize(key)
                else:
                    mode = "body"
                if key == "Introdução":
                    seen_intro = True
                level = classify.heading_level(paragraph)
                _heading_number(paragraph, counters, level, text, key)
                kind = "heading_numbered"
        elif mode == "reference":
            kind = "reference"
            changes.references += 1
        elif mode in ("resumo", "abstract"):
            kind = mode
        elif classify.is_long_quote(text, _left_indent_cm(paragraph)):
            kind = "quote"
        elif (paragraph.style.name or "").lower().startswith("list"):
            kind = "list"
        elif paragraph.alignment in (WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT):
            kind = "pre"
        elif has_intro and not seen_intro:
            kind = "pre"
        else:
            kind = "body"
            changes.body += 1

        _apply_paragraph(paragraph, kind, font_name, changes)

    changes.tables = format_tables(doc)
    changes.footnotes = format_footnotes(doc, font_name)
    changes.intro_found = has_intro

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Regrava para os cabeçalhos/numeração, que exigem secções reabertas
    reloaded = Document(buffer)
    changes.textual_sections = _configure_headers(reloaded, font_name)
    final = io.BytesIO()
    reloaded.save(final)
    final.seek(0)

    report = _build_report(changes, doc)
    return final.getvalue(), report


def _format_empty(paragraph, font_name):
    for run in paragraph.runs:
        _set_run_font(run, font_name, None)


def _left_indent_cm(paragraph):
    value = paragraph.paragraph_format.left_indent
    if value is None:
        return None
    try:
        return value.cm
    except Exception:
        return None


class _Changes:
    def __init__(self):
        self.body = 0
        self.quotes = 0
        self.captions = 0
        self.sources = 0
        self.references = 0
        self.footnotes = 0
        self.tables = 0
        self.textual_sections = False
        self.intro_found = False


def _build_report(changes, doc):
    text = "\n".join((p.text or "") for p in doc.paragraphs)
    normalized = classify.normalize(text)

    found, missing = [], []
    for key, labels in config.REQUIRED_ELEMENTS:
        if any(classify.normalize(label) in normalized for label in labels):
            found.append(labels[0])
        else:
            missing.append(labels[0])

    return {
        "encontrados": found,
        "faltando": missing,
        "alteracoes": {
            "corpo_paragrafos": changes.body,
            "citacoes_longas": changes.quotes,
            "legendas": changes.captions,
            "fontes": changes.sources,
            "referencias": changes.references,
            "notas_rodape": changes.footnotes,
            "tabelas_sem_bordas_verticais": changes.tables,
        },
        "numeracao": {
            "pre_textual_oculta": changes.textual_sections,
            "textual_arabica": True,
            "contagem_desde_folha_rosto": changes.textual_sections,
        },
        "pendencias": _pendencies(changes, missing),
    }


def _pendencies(changes, missing):
    items = []
    if not changes.intro_found:
        items.append(
            "Não encontrei um título 'Introdução'. O número de página foi "
            "exibido em arábico desde o início e não ficou oculto no "
            "pré-textual. Confirme manualmente."
        )
    else:
        items.append(
            "O número de página fica oculto até a Introdução e passa a ser "
            "exibido, em algarismos arábicos, a partir dela. A contagem exata "
            "depende da paginação do Word/LibreOffice: ao abrir o arquivo, "
            "o programa aplica o valor correto."
        )
    if missing:
        items.append(
            "Não localizei no documento: " + ", ".join(missing)
            + ". Verifique se os elementos existem com esses títulos."
        )
    items.append(
        "Citações longas foram identificadas por tamanho (mais de 3 linhas) e "
        "pelo padrão de referência (AUTOR, ano). Revise se todas ficaram com "
        "recuo de 4 cm, fonte tamanho 10, sem aspas."
    )
    items.append(
        "Tabelas foram deixadas sem bordas laterais e sem verticais internas; "
        "confira o resultado, sobretudo se a tabela tinha uma estrutura "
        "diferente."
    )
    items.append(
        "Fórmulas, imagens e quadros complexos mantêm o layout original; "
        "confira o recuo e a fonte das legendas."
    )
    return items


# -----------------------------------------------------------------------------
# PDF (abnt/pdf_docx.py partilha apenas o cabeçalho/margens via build_from_pdf)
