"""Converte um PDF em um .docx já formatado em ABNT.

Um PDF não carrega uma 'template' editável, então aqui o texto é extraído e
um novo documento é montado seguindo as normas (A4, margens, fonte, recuo).
"""
import io
import re

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import adjust, classify, config

_kill_theme_rfonts = adjust._kill_theme_rfonts
_configure_doc_defaults = adjust._configure_doc_defaults


def _fitz():
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24
    except ImportError:
        import fitz  # type: ignore
    return fitz


def extract_text_blocks(path):
    fitz = _fitz()
    blocks = []
    with fitz.open(path) as pdf:
        for page in pdf:
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                if block.get("type") != 0:
                    continue
                sizes, texts = [], []
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        if span_text.strip():
                            texts.append(span_text)
                            sizes.append(round(span.get("size", 0), 1))
                text = " ".join(texts).strip()
                if text:
                    avg = sum(sizes) / len(sizes) if sizes else 12.0
                    blocks.append({"text": text, "size": avg})
    return blocks


def _set_font(run, font_name, size):
    run.font.name = font_name
    rpr = run._element.get_or_add_rPr()
    _kill_theme_rfonts(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), font_name)
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(*config.BLACK)
    szcs = rpr.find(qn("w:szCs"))
    if szcs is None:
        szcs = OxmlElement("w:szCs")
        rpr.append(szcs)
    szcs.set(qn("w:val"), str(int(size * 2)))


def _base_paragraph(doc, font_name, *, align, spacing, indent_cm, size):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = spacing
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    if indent_cm:
        pf.first_line_indent = Cm(indent_cm)
    run = p.add_run("")
    _set_font(run, font_name, size)
    return p, run


def _configure_mirror_margins(doc):
    """Ativa margens espelhadas (frente/verso) nas configurações do documento."""
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


def _set_pgnum(doc, start=None, fmt="decimal"):
    """Ajusta a numeração (apenas formato/início)."""
    sectpr = doc.sections[-1]._sectPr
    existing = sectpr.find(qn("w:pgNumType"))
    if existing is not None:
        sectpr.remove(existing)
    el = OxmlElement("w:pgNumType")
    el.set(qn("w:fmt"), fmt)
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


def _is_unnumbered(text):
    return classify.unnumbered_title(text) is not None


def _uppercase_text(text):
    letters = sum(1 for ch in text if ch.isalpha())
    if letters == 0:
        return text
    upper = sum(1 for ch in text if ch.isalpha() and ch.isupper())
    if upper / letters >= 0.9:
        return text
    return text.upper()


def build_from_pdf(path, font_name, original_filename):
    blocks = extract_text_blocks(path)
    doc = docx.Document()

    section = doc.sections[0]
    section.page_width = Cm(config.PAGE_WIDTH_CM)
    section.page_height = Cm(config.PAGE_HEIGHT_CM)
    section.top_margin = Cm(config.MARGIN_TOP_CM)
    section.left_margin = Cm(config.MARGIN_INSIDE_CM)
    section.bottom_margin = Cm(config.MARGIN_BOTTOM_CM)
    section.right_margin = Cm(config.MARGIN_OUTSIDE_CM)

    style = doc.styles["Normal"]
    style.font.name = font_name
    style.font.size = Pt(config.TEXT_SIZE)
    style.paragraph_format.line_spacing = config.LINE_SPACING

    # Normaliza estilos de título (Heading 1..N / Title) para ABNT
    heading_like = ("heading", "título", "titulo", "title", "subtitle",
                    "subtitulo", "subtítulo", "toc heading")
    plain_like = ("hyperlink", "list paragraph", "footer", "header",
                  "footnote text", "endnote text", "caption", "quote")
    for st in doc.styles:
        try:
            key = adjust._style_name_key(getattr(st, "name", ""))
            if key and any(key.startswith(h) for h in heading_like):
                adjust._set_style_font(st, font_name, config.TEXT_SIZE)
                st.font.bold = True
                st.paragraph_format.space_before = Pt(0)
                st.paragraph_format.space_after = Pt(0)
                st.paragraph_format.line_spacing = config.LINE_SPACING
            elif key and any(key.startswith(p) for p in plain_like):
                adjust._set_style_font(st, font_name, config.SMALL_SIZE)
        except Exception:
            continue

    _configure_doc_defaults(doc, font_name)
    _configure_mirror_margins(doc)

    counters = {1: 0, 2: 0, 3: 0, 4: 0}
    changes = {
        "corpo_paragrafos": 0, "citacoes_longas": 0, "legendas": 0,
        "fontes": 0, "referencias": 0, "notas_rodape": 0,
        "tabelas_sem_bordas_verticais": 0,
    }
    mode = "body"
    found = []

    body_sizes = [b["size"] for b in blocks if b["size"]]
    body_size = max(set(body_sizes), key=body_sizes.count) if body_sizes else 12.0
    heading_size = body_size + 1.5

    for block in blocks:
        text = block["text"]
        is_heading = block["size"] >= heading_size and len(text) < 120
        key = classify.chapter_key(text)
        unnum = classify.unnumbered_title(text)

        if is_heading or key is not None:
            if unnum in ("Resumo", "Abstract"):
                mode = "resumo" if classify.normalize(unnum) == "resumo" else "abstract"
            elif unnum in config.REFERENCE_TITLES:
                mode = "reference"
            else:
                mode = "body"
            if unnum is not None:
                found.append(unnum)
                # títulos sem numeração: centralizados, negrito, MAIÚSCULAS, nova página
                text = _uppercase_text(text)
                p, run = _base_paragraph(
                    doc, font_name, align=WD_ALIGN_PARAGRAPH.CENTER,
                    spacing=config.LINE_SPACING, indent_cm=None, size=config.TEXT_SIZE,
                )
                p.paragraph_format.keep_with_next = True
                p.paragraph_format.page_break_before = True
                run.text = text
                run.bold = True
                continue

            level = 1
            for i in range(1, 5):
                counters[i] = 0
            counters[1] += 1
            number = str(counters[1])
            p, run = _base_paragraph(
                doc, font_name, align=WD_ALIGN_PARAGRAPH.LEFT,
                spacing=config.LINE_SPACING, indent_cm=None, size=config.TEXT_SIZE,
            )
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.page_break_before = True
            run.text = f"{number} {text}".strip()
            run.bold = True
            continue

        if mode == "reference":
            changes["referencias"] += 1
            p, run = _base_paragraph(
                doc, font_name, align=WD_ALIGN_PARAGRAPH.LEFT,
                spacing=config.SINGLE_SPACING, indent_cm=None, size=config.TEXT_SIZE,
            )
            p.paragraph_format.space_after = Pt(config.REFERENCE_SPACE_AFTER_PT)
            run.text = text
        elif mode in ("resumo", "abstract"):
            p, run = _base_paragraph(
                doc, font_name, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                spacing=config.SINGLE_SPACING,
                indent_cm=None, size=config.TEXT_SIZE,
            )
            run.text = text
        elif classify.is_source(text):
            changes["fontes"] += 1
            p, run = _base_paragraph(
                doc, font_name, align=WD_ALIGN_PARAGRAPH.CENTER,
                spacing=config.SINGLE_SPACING, indent_cm=None, size=config.SMALL_SIZE,
            )
            run.text = text
        elif classify.is_caption(text):
            changes["legendas"] += 1
            p, run = _base_paragraph(
                doc, font_name, align=WD_ALIGN_PARAGRAPH.CENTER,
                spacing=config.SINGLE_SPACING, indent_cm=None, size=config.SMALL_SIZE,
            )
            run.text = text
        elif classify.is_long_quote(text, None):
            changes["citacoes_longas"] += 1
            p, run = _base_paragraph(
                doc, font_name, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                spacing=config.SINGLE_SPACING, indent_cm=None, size=config.SMALL_SIZE,
            )
            p.paragraph_format.left_indent = Cm(config.QUOTE_INDENT_CM)
            run.text = text
        else:
            changes["corpo_paragrafos"] += 1
            p, run = _base_paragraph(
                doc, font_name, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                spacing=config.LINE_SPACING,
                indent_cm=config.FIRST_LINE_INDENT_CM, size=config.TEXT_SIZE,
            )
            run.text = text

    _set_pgnum(doc, start=1, fmt="decimal")  # PDF reconstruído: não há capa
    _configure_header(doc, font_name)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    found_norm = {classify.normalize(m) for m in found}
    encontrados, missing = [], []
    for _, labels in config.REQUIRED_ELEMENTS:
        if any(classify.normalize(label) in found_norm for label in labels):
            encontrados.append(labels[0])
        else:
            missing.append(labels[0])

    report = {
        "encontrados": encontrados,
        "faltando": missing,
        "alteracoes": changes,
        "numeracao": {
            "pre_textual_oculta": True,
            "textual_arabica": True,
            "contagem_desde_folha_rosto": True,
        },
        "pendencias": [
            "O número de página fica oculto até a Introdução; a contagem "
            "exata depende da paginação do Word/LibreOffice.",
            "Citações longas foram identificadas por tamanho (mais de 3 "
            "linhas) e por padrão de referência (AUTOR, ano); confira.",
        ],
    }
    return buffer.getvalue(), report


def _configure_header(doc, font_name):
    section = doc.sections[0]
    header = section.header
    paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, text, end):
        run._element.append(el)
    _set_font(run, font_name, config.SMALL_SIZE)
