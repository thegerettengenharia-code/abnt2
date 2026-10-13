"""Utilidades para classificar parágrafos de um documento do Word."""
import re
import unicodedata


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


_HEADING_STYLES = re.compile(
    r"^(heading|titulo|seção|secao)\s*\d+$"
)

# Estilos de EXIBIÇÃO (capa/folha de rosto): nunca viram título numerado.
_DISPLAY_STYLES = {"title", "titulo", "título", "subtitle", "subtítulo", "subtitulo"}

_CHAPTER_WORDS = {
    "introducao": "Introdução",
    "conclusao": "Conclusão",
    "referencias": "Referências",
    "referencias bibliograficas": "Referências Bibliográficas",
    "resumo": "Resumo",
    "abstract": "Abstract",
    "sumario": "Sumário",
    "agradecimentos": "Agradecimentos",
    "metodologia": "Metodologia",
    "desenvolvimento": "Desenvolvimento",
    "referencial teorico": "Referencial Teórico",
    "fundamentacao teorica": "Fundamentação Teórica",
    "justificativa": "Justificativa",
    "resultados": "Resultados",
    "discussao": "Discussão",
    "consideracoes finais": "Considerações Finais",
    "glossario": "Glossário",
    "apendice": "Apêndice",
    "anexo": "Anexo",
    "indice": "Índice",
    "lista de ilustracoes": "Lista de Ilustrações",
    "lista de figuras": "Lista de Figuras",
    "lista de tabelas": "Lista de Tabelas",
    "lista de quadros": "Lista de Quadros",
    "lista de abreviaturas": "Lista de Abreviaturas",
    "lista de abreviaturas e siglas": "Lista de Abreviaturas e Siglas",
    "lista de siglas": "Lista de Abreviaturas e Siglas",
    "lista de simbolos": "Lista de Símbolos",
    "dedicatoria": "Dedicatória",
    "epigrafe": "Epígrafe",
    "errata": "Errata",
}

# Secções que NÃO recebem número (elementos pré/pós-textuais)
_UNNUMBERED = {
    "resumo", "abstract", "sumario", "referencias", "agradecimentos",
    "referencias bibliograficas", "glossario", "apendice", "anexo",
    "indice", "lista de ilustracoes", "lista de figuras", "lista de tabelas",
    "lista de quadros", "lista de abreviaturas", "lista de siglas",
    "lista de abreviaturas e siglas", "lista de simbolos", "epigrafe",
    "dedicatoria", "errata",
}

_LEADING_NUMBER = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s+")
_LEADING_NUMBER_GAP = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s*")


_CAPTION_PREFIX = (
    "figura", "fig.", "tabela", "tab.", "quadro", "grafico", "imagem",
    "mapa", "foto", "fluxograma", "organograma", "ilustracao", "ilustração",
    "grafico", "gráfico",
)

_SOURCE_PREFIX = ("fonte:", "fonte :", "source:", "source :")

_CITATION = re.compile(
    r"\([^)]*\b(?:1[5-9]|20)\d{2}[a-z]?\b[^)]*\)"          # (AUTOR, 2020, p. 45)
    r"|[A-ZÀ-Ú][a-zà-ú]+\s*\(\s*(?:1[5-9]|20)\d{2}[a-z]?\s*\)"  # Autor (2020)
    r"|\b(?:apud|citado por)\b",
)


_MANUAL_NUMBER = re.compile(r"^\s*\d+(?:\.\d+)*\s+\S")


def is_display_style(paragraph) -> bool:
    """True se o parágrafo usa um estilo de exibição (Title/Subtitle)."""
    style = (paragraph.style.name or "") if paragraph.style is not None else ""
    return normalize(style) in _DISPLAY_STYLES


def is_heading(paragraph) -> bool:
    style = (paragraph.style.name or "") if paragraph.style is not None else ""
    if normalize(style) in _DISPLAY_STYLES:
        return False
    if _HEADING_STYLES.match(normalize(style)):
        return True
    text = (paragraph.text or "").strip()
    if not text or len(text) > 90:
        return False
    # Título de seção reconhecido (RESUMO, REFERÊNCIAS, 1 INTRODUÇÃO, ...)
    if chapter_key(text) is not None:
        return True
    # Numeração manual no próprio texto: "1 INTRODUÇÃO", "2.1 Objetivos"
    if _MANUAL_NUMBER.match(text) and len(text) <= 90:
        return True
    runs = [r for r in paragraph.runs if (r.text or "").strip()]
    if runs and all(r.bold for r in runs):
        return True
    return False


def heading_level(paragraph) -> int:
    m = re.search(r"(\d)", paragraph.style.name or "")
    if m:
        return max(1, min(int(m.group(1)), 4))
    text = (paragraph.text or "").strip()
    manual = re.match(r"^\s*(\d+(?:\.\d+)*)", text)
    if manual:
        depth = manual.group(1).count(".") + 1
        return max(1, min(depth, 4))
    return 1


def chapter_key(text: str) -> str | None:
    stripped = _LEADING_NUMBER.sub("", text or "")
    return _CHAPTER_WORDS.get(normalize(stripped))


def is_unnumbered(text: str) -> bool:
    stripped = _LEADING_NUMBER.sub("", text or "")
    return normalize(stripped) in _UNNUMBERED


def is_caption(text: str) -> bool:
    n = normalize(text)
    return any(n.startswith(normalize(p)) for p in _CAPTION_PREFIX)


def is_source(text: str) -> bool:
    n = normalize(text)
    return any(n.startswith(normalize(p)) for p in _SOURCE_PREFIX)


def unnumbered_title(text: str) -> str | None:
    """Devolve a CHAVE canonica se o titulo for de elemento sem numeracao."""
    stripped = _LEADING_NUMBER_GAP.sub("", text or "").strip()
    n = normalize(stripped)
    if n in _UNNUMBERED:
        return _CHAPTER_WORDS.get(n)
    return None


def is_unnumbered_centered(text: str) -> bool:
    return unnumbered_title(text) is not None


def strip_list_marks(text: str) -> str:
    return re.sub(r"^[\-\*\u2022\.]+\s*", "", text).strip()


def is_long_quote(text: str, left_indent_cm: float | None) -> bool:
    t = " ".join((text or "").split())
    if len(t) < 240:
        return False
    if left_indent_cm is not None and left_indent_cm >= 3.0:
        return True
    if _CITATION.search(t):
        return True
    if t.startswith('"') or t.startswith("\u201c") or t.startswith("\u2018"):
        return True
    return False
