"""Constantes de formatação ABNT aplicadas ao documento enviado."""

FONT_CHOICES = ("Times New Roman", "Arial")
DEFAULT_FONT = "Times New Roman"

TEXT_SIZE = 12          # texto padrão
SMALL_SIZE = 10         # citações longas, notas, paginação, legendas e fontes

LINE_SPACING = 1.5
SINGLE_SPACING = 1.0
LINE_SPACING_OPTIONS = ("1,5", "simples")

FIRST_LINE_INDENT_CM = 1.25
QUOTE_INDENT_CM = 4.0

# Margens (modo espelhado, frente e verso)
# interna = lado da lombada, externa = lado oposto.
# Com mirrorMargins: anverso -> esquerda=interna, direita=externa;
# verso -> esquerda=externa, direita=interna.
MARGIN_TOP_CM = 3.0
MARGIN_INSIDE_CM = 3.0
MARGIN_BOTTOM_CM = 2.0
MARGIN_OUTSIDE_CM = 2.0
PAGE_NUMBER_DISTANCE_CM = 2.0

PAGE_WIDTH_CM = 21.0
PAGE_HEIGHT_CM = 29.7

BLACK = (0, 0, 0)
PLACEHOLDER = "[COMPLETAR]"

# Separação entre referências (uma linha em branco ≈ 12 pt)
REFERENCE_SPACE_AFTER_PT = 12

# Separador de notas de rodapé: traço de 5 cm a partir da margem esquerda
FOOTNOTE_SEPARATOR_CM = 5.0

# Títulos de elementos sem numeração: centralizados, negrito e MAIÚSCULAS
UNNUMBERED_CENTERED_TITLES = (
    "Errata", "Agradecimentos", "Resumo", "Abstract", "Sumário",
    "Referências", "Referências Bibliográficas", "Glossário",
    "Apêndice", "Anexo", "Índice",
    "Lista de Ilustrações", "Lista de Figuras", "Lista de Tabelas",
    "Lista de Abreviaturas e Siglas", "Lista de Abreviaturas",
    "Lista de Símbolos", "Lista de Quadros", "Dedicatória", "Epígrafe",
)

# Secções unnumbered que usam espaçamento simples no corpo
SINGLE_SPACING_TITLES = ("resumo", "abstract")

# Seções que entram no modo de referências
REFERENCE_TITLES = ("Referências", "Referências Bibliográficas")

REQUIRED_ELEMENTS = [
    ("resumo", ("Resumo",)),
    ("abstract", ("Abstract",)),
    ("introducao", ("Introdução",)),
    ("conclusao", ("Conclusão", "Considerações Finais")),
    ("referencias", ("Referências", "Referências Bibliográficas")),
]
