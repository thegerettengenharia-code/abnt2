# -*- coding: utf-8 -*-
"""Caso realista: docx 'mal formatado' (estilos do Word padrão com tema,
títulos sem estilo Heading, só centralizados/negritados à mão, com números
já gravados no texto, título 'Title' na capa) para reproduzir o defeito."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from abnt import adjust, classify


def build_realistic():
    doc = Document()  # tema padrão Word (Calibri/tema), Heading com cor de tema

    # Capa com estilo Title (28 pt, tema) + Subtitle
    p = doc.add_paragraph(style="Title")
    p.add_run("O IMPACTO DA TECNOLOGIA NA EDUCAÇÃO")
    try:
        p2 = doc.add_paragraph(style="Subtitle")
    except KeyError:
        p2 = doc.add_paragraph()
    p2.add_run("Trabalho de Conclusão de Curso")
    try:
        p3 = doc.add_paragraph()
    except Exception:
        p3 = None
    if p3 is not None:
        p3.add_run("Fulano de Tal")
    doc.add_page_break()

    # Folha de rosto sem estilo
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("O IMPACTO DA TECNOLOGIA NA EDUCAÇÃO").font.size = Pt(11)
    doc.add_page_break()

    # Resumo: título digitado à mão, centralizado, SEM bold, MAIÚSCULO
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("RESUMO").font.name = "Calibri"
    r = doc.add_paragraph(
        "Este trabalho analisa a presença da tecnologia no ensino superior "
        "brasileiro e seus reflexos na aprendizagem. " * 20
    )
    r.paragraph_format.left_indent = Cm(0.5)

    # Título numerado à mão, sem estilo Heading:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("1 INTRODUÇÃO").font.color.rgb = None or p.add_run("").font.color.rgb
    doc.add_paragraph(
        "A introdução contextualiza o tema central da pesquisa. " * 40
    )

    quote = "Conforme autores consagrados, o método científico é essencial. " * 25
    doc.add_paragraph(quote)

    p = doc.add_paragraph()
    p.add_run("2 DESENVOLVIMENTO").font.bold = True
    doc.add_paragraph("O desenvolvimento detalha a metodologia empregada. " * 40)

    p = doc.add_paragraph()
    p.add_run("3 CONSIDERAÇÕES FINAIS")
    doc.add_paragraph("Conclui-se que a tecnologia transforma o ensino. " * 30)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("REFERÊNCIAS").font.name = "Calibri"
    doc.add_paragraph("SOBRENOME, Nome. Título. Local: Editora, 2020.")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "realistico.docx")
    doc.save(out)
    return out


def main():
    path = build_realistic()
    data, report = adjust.adjust_docx(path, "Times New Roman", "realistico.docx")
    out = os.path.join(os.path.dirname(path), "realistico_ABNT.docx")
    with open(out, "wb") as fh:
        fh.write(data)
    print("relatorio:", report["numeracao"], "| faltando:", report["faltando"])
    print("pendencias:", report["pendencias"][:1])

    doc = Document(out)
    ok = True
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if not t:
            continue
        kind = ["corpo"]
        if classify.is_heading(p):
            kind = ["titulo"]
        size = p.runs[0].font.size.pt if p.runs and p.runs[0].font.size else "herda"
        font = p.runs[0].font.name if p.runs else "?"
        print(i, kind[0], repr(t[:46]), "font:", font, "size:", size)

    # O que realmente importa: Introdução foi reconhecida para paginação?
    intro_ok = any(
        classify.is_heading(p) and classify.chapter_key(p.text.strip()) == "Introdução"
        for p in doc.paragraphs
    )
    print("Introdução detectada:", intro_ok)
    print("PgNum pré-textual oculto (sectPr na capa):",
          doc.paragraphs[0]._p.find(
              "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
          ) is not None)
    if not intro_ok:
        ok = False
        print("FALHA: títulos digitados à mão não foram reconhecidos.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
