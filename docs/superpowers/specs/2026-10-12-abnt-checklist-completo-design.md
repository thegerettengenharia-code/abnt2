# Spec: Implementação Completa Checklist ABNT (NBR 14724, 6023, 10520, 6022, 6027, 6028)

**Data:** 2026-10-12
**Status:** Aprovado para implementação
**Classificação:** Architectural

---

## 1. Resumo

Estender o Formatador ABNT para cobrir **fielmente** todas as 6 categorias do checklist fornecido, aplicando formatação **apenas aos elementos detectados** no documento (sem adicionar/remover conteúdo), com relatório expandido de validação e auto-correção onde viável.

**Bug crítico a corrigir:** `abnt/adjust.py` está sem a definição `def adjust_docx(...)` — caminho `.docx` inoperante.

---

## 2. Requisitos por Categoria

### 2.1 Estrutura do Documento (NBR 14724)

| Item | Ação | Detecção | Formatação |
|---|---|---|---|
| Folha de rosto (+ ficha catalográfica verso) | Validar presença; não formatar conteúdo | Texto "FOLHA DE ROSTO" ou "Ficha catalográfica" | Preservar estilos `Title`/`Subtitle`; paginação não conta |
| Errata | Validar se houver | Palavra "ERRATA" (centralizada, maiúsculas) | Título sem numeração, centralizado, negrito, maiúsculas |
| Folha de aprovação | Validar se houver | Palavras "FOLHA DE APROVAÇÃO" / "BANCA" | Não formatar (assinaturas) |
| Dedicatória / Agradecimentos / Epígrafe | Validar se houver | Palavras-chave centralizadas | Título sem numeração, centralizado, negrito, maiúsculas; corpo: espaço simples, sem recuo |
| Resumo (NBR 6028) / Abstract | Validar presença obrigatória | "RESUMO" / "ABSTRACT" (centralizados) | Parágrafo único, espaço simples, **sem recuo**, fonte 12 |
| Listas (ilustrações, tabelas, abreviaturas, símbolos) | Validar se houver | "LISTA DE..." centralizado | Título sem numeração; itens: espaço simples |
| Sumário (NBR 6027) | Validar presença | "SUMÁRIO" centralizado | Título sem numeração; entradas com recuo hierárquico |
| Introdução | **Marca início da numeração** (p. 1) | "INTRODUÇÃO" numerado (1) | Heading 1: negrito, esquerda, árabe sem ponto; quebra de página antes |
| Desenvolvimento | Corpo principal | Headings numerados sequenciais | Mesma regra de heading |
| Considerações finais | Validar presença | "CONSIDERAÇÕES FINAIS" / "CONCLUSÃO" | Heading numerado |
| Referências | Validar presença; bloco especial | "REFERÊNCIAS" / "REFERÊNCIAS BIBLIOGRÁFICAS" | Título sem numeração, centralizado, negrito, maiúsculas; entradas com **entrelinha pendente 1,25 cm**, espaço simples, linha em branco entre entradas, **ano em negrito** |
| Apêndices / Anexos | Validar se houver | "APÊNDICE", "ANEXO" (letras maiúsculas: A, B...) | Heading sem numeração (letra), centralizado, negrito, maiúsculas; continuação da numeração de páginas |

**Regra de ordenação:** Validar sequência NBR 14724 e reportar `ordem_incorreta` em `pendencias`. **Não reordenar automaticamente**.

---

### 2.2 Formatação Geral

| Regra | Implementação | Onde |
|---|---|---|
| Papel A4 (21 × 29,7 cm) | `section.page_width/height` | `adjust._configure_sections` ✓ |
| Margens espelhadas: sup/esq 3 cm, inf/dir 2 cm | `mirrorMargins`, `top/inside/bottom/outside` | `adjust._configure_mirror_margins` ✓ |
| Fonte Arial ou Times New Roman, 12 pt, preto | `docDefaults` + `Normal` style + runs | `adjust._configure_doc_defaults`, `_set_run_font` ✓ |
| Espaçamento 1,5 (texto); simples (citas longas, notas, refs, legendas) | `line_spacing` por tipo de parágrafo | `adjust._apply_paragraph` ✓ |
| Recuo 1ª linha 1,25 cm | `first_line_indent` | `adjust._apply_paragraph` (corpo) ✓ |
| Texto justificado | `alignment = JUSTIFY` | `adjust._apply_paragraph` ✓ |
| Paginação: conta desde folha de rosto; oculta até Introdução; arábico sup. dir. 2 cm, tam. 10 | `header/footer` com `PAGE` field; section `start=0` | `adjust._configure_headers`, `_set_page_header` ✓ |
| Sem ornamentos/bordas/cores (preto) | Remover `w:color` theme, `w:shd`, borders | `adjust._clear_color_theme`, `_clear_borders` |

**Já implementado** (exceto bug do `adjust_docx`).

---

### 2.3 Elementos Visuais (NBR 6022 / 14724)

| Item | Ação | Detecção | Formatação |
|---|---|---|---|
| Tabela: título **acima** (Fonte 10, negrito) | Validar posição; formatar se encontrado | `classify.is_caption` + contexto "Tabela"/"Table" | Centralizado, negrito, tamanho 10, espaço simples |
| Figura/Quadro: título **abaixo** | Validar posição | `classify.is_caption` + "Figura"/"Quadro"/"Figure" | Centralizado, negrito, tamanho 10, espaço simples |
| Numeração sequencial (Tabela 1, Figura 1...) | **Auto-corrigir** se detectado padrão "Tabela X" / "Figura X" | Regex `^(Tabela|Figura|Quadro)\s+\d+` | Renumerar sequencialmente por tipo; manter "–" entre número e título |
| Fonte obrigatória abaixo do elemento | Validar presença; reportar se ausente | `classify.is_source` ("Fonte:") | Tamanho 10, espaço simples, alinhado à esquerda |
| Elementos citados no texto antes de aparecerem | Validar cross-ref; reportar | Buscar "Tabela X", "Figura Y" no texto antes do elemento | Apenas relatório (`pendencias`) |
| Legenda legível (mínimo 10 pt) | Garantir tamanho ≥ 10 | Fonte detectada em caption/source | Forçar 10 pt se menor |

---

### 2.4 Citações (NBR 10520)

| Item | Ação | Detecção | Formatação |
|---|---|---|---|
| Citação curta (≤3 linhas): no texto, **entre aspas** | **Auto-corrigir**: adicionar aspas se ausentes; remover se em citação longa | Heurística: parágrafo com `"` ou `'` nas bordas OU padrão `(AUTOR, ano)` em linha | Aspas duplas `"` no início/fim; manter no corpo do texto (sem recuo extra) |
| Citação longa (>3 linhas): recuo 4 cm, fonte 10/11, espaço simples, **sem aspas** | **Auto-corrigir**: remover aspas; aplicar indent 4 cm | `classify.is_long_quote` (≥240 chars OU indent ≥3 cm OU padrão `(AUTOR, ano)` OU inicia com aspas) | `left_indent=4cm`, `first_line_indent=0`, `size=10`, `line_spacing=1.0`, `bold=False` |
| Autor ≤3 sobrenomes por extenso na 1ª ocorrência; depois "et al." | **Validar e reportar**; não reescrever conteúdo | Regex `_CITATION` em `classify.py` | Apenas `pendencias`: "Verificar formato de autor em citação: [trecho]" |
| Citação indireta: (SOBRENOME, ano) | Validar padrão | Regex | `pendencias` se padrão divergente |
| Citação direta curta: (SOBRENOME, ano, p. X) | Validar padrão | Regex | `pendencias` se padrão divergente |
| Notas de rodapé: fonte 10, espaço simples, separador 5 cm | **Auto-formatar** notas detectadas | `footnote` elements no docx | `size=10`, `line_spacing=1.0`, separator `width=5cm` |

---

### 2.5 Referências (NBR 6023:2018)

| Item | Ação | Detecção | Formatação |
|---|---|---|---|
| Ordem alfabética pelo sobrenome | **Validar e reportar**; opcional auto-ordenar (config) | Bloco após título "REFERÊNCIAS" | `pendencias`: "Referências fora de ordem alfabética: [lista]" |
| Espaçamento simples entre linhas; espaço duplo (linha em branco) entre referências | **Auto-formatar** bloco de referências | Parágrafos no modo `reference` | `line_spacing=1.0`, `space_after=12pt` (≈1 linha em branco) |
| Recuo 1,25 cm na 2ª linha (entrelinha pendente) | **Auto-formatar** entradas | Parágrafos no modo `reference` | `first_line_indent=0`, `left_indent=1.25cm`, `hanging=1.25cm` |
| Negrito no ano das publicações | **Auto-formatar** ano detectado (4 dígitos entre parênteses ou após ponto) | Regex `\b(19|20)\d{2}\b` em parágrafos de referência | `bold=True` apenas no ano |
| DOI no final | Validar presença; não modificar | Regex `10\.\d{4,}/.+` ou `doi.org` | `pendencias` se DOI ausente em entrada que deveria ter |
| Apenas obras efetivamente citadas no texto | **Cross-check** citações ↔ referências | Extrair autores/anos de citações no texto vs entradas | `pendencias`: "Citadas mas não referenciadas: [...]"; "Referenciadas mas não citadas: [...]" |
| Autor ≤3 sobrenomes por extenso; >3 → 1º + et al. | Validar; reportar | Parsing de cada entrada de referência | `pendencias` por entrada |
| Tipos testados: livro, capítulo, artigo, eletrônico, tese/dissertação, norma | Validar estrutura mínima por tipo | Heurística por campos (editora, ISBN, ISSN, DOI, URL, local) | `pendencias` se campos obrigatórios faltando |

---

### 2.6 Capa e Folha de Rosto

| Campo | Fonte | Formatação |
|---|---|---|
| Instituição (superior) | Input do usuário (frontend) | Centralizado, maiúsculas, negrito, tamanho 14-16 |
| Autor(es) (centralizado, meio da página) | Input do usuário | Centralizado, negrito, tamanho 12-14 |
| Título (negrito, pode ser maior) | Input do usuário | Centralizado, negrito, tamanho 16-18 |
| Subtítulo (se houver) | Input do usuário | Centralizado, normal, tamanho 14 |
| Cidade e ano (inferior) | Input do usuário (ano = atual por default) | Centralizado, normal, tamanho 12 |

**Comportamento:**
- Se documento **já tem** capa/folha de rosto detectada (estilos `Title`/`Subtitle` nas primeiras páginas): **validar e preservar**, apenas reportar divergências
- Se **não tem**: gerar template nas 2 primeiras páginas (capa + folha de rosto verso em branco para ficha catalográfica)
- Paginação: capa = página 0 (não conta), folha de rosto = página 1 (oculta), introdução = página 1 visível

---

## 3. Arquitetura

### 3.1 Novo Módulo: `abnt/validate.py`

```python
# API pública
def validate_all(doc: Document, metadata: dict | None = None) -> ValidationReport:
    return ValidationReport(
        estrutura=validate_structure(doc),
        citacoes=validate_citations(doc),
        referencias=validate_references(doc),
        elementos_visuais=validate_visual_elements(doc),
        capa=validate_cover_page(doc, metadata),
        cross_check=cross_check_citations_references(doc),
    )

# Estruturas de retorno (dataclasses)
@dataclass
class ValidationReport:
    estrutura: StructureValidation
    citacoes: CitationValidation
    referencias: ReferenceValidation
    elementos_visuais: VisualValidation
    capa: CoverValidation
    cross_check: CrossCheckResult

@dataclass
class StructureValidation:
    encontrados: list[str]
    faltando: list[str]
    ordem_incorreta: list[tuple[str, str]]  # (esperado, encontrado)
    pendencias: list[str]

@dataclass
class CitationValidation:
    curtas_sem_aspas: list[str]
    longas_com_aspas: list[str]
    autor_formato: list[str]
    footnotes_ok: bool
    pendencias: list[str]

@dataclass
class ReferenceValidation:
    fora_ordem: list[str]
    sem_entrelinha: bool
    sem_negrito_ano: bool
    sem_doi: list[str]
    citadas_nao_referenciadas: list[str]
    referenciadas_nao_citadas: list[str]
    autor_formato: list[str]
    pendencias: list[str]

@dataclass
class VisualValidation:
    caption_posicao: list[str]  # "Tabela 2: título abaixo (deveria ser acima)"
    numeracao_faltando: list[str]
    fonte_faltando: list[str]
    cross_ref_ordem: list[str]
    pendencias: list[str]

@dataclass
class CoverValidation:
    tem_capa: bool
    tem_folha_rosto: bool
    campos_faltando: list[str]
    divergencias: list[str]

@dataclass
class CrossCheckResult:
    citacoes_unicas: set[str]  # normalizadas
    referencias_unicas: set[str]
    matches: dict[str, str]  # citaçao -> referencia
    orphans_citacoes: list[str]
    orphans_referencias: list[str]
```

### 3.2 Extensões em `abnt/adjust.py`

```python
# Novas funções de auto-correção (chamadas APÓS validação, se habilitado)
def apply_hanging_indent_to_references(doc: Document) -> int
def bold_years_in_references(doc: Document) -> int
def fix_short_quote_quotes(doc: Document) -> int      # adicionar aspas
def fix_long_quote_quotes(doc: Document) -> int       # remover aspas
def renumber_captions(doc: Document) -> dict[str, int]  # {"tabela": 3, "figura": 5}
def fix_caption_placement(doc: Document) -> int
def ensure_cover_page(doc: Document, metadata: dict) -> bool
```

### 3.3 Integração no Fluxo (`app/main.py`)

```python
@app.post("/api/format")
async def format_document(request: Request):
    # 1. Upload → Blob
    # 2. Download → temp .docx
    # 3. VALIDAÇÃO PRÉ-FORMATAÇÃO
    report = validate.validate_all(doc, metadata=request.metadata)
    # 4. FORMATAÇÃO (existente + novas auto-correções)
    adjust.adjust_docx(doc, font_name, filename)
    # opcional: auto-fixes baseados em flags do request
    if request.auto_fix_references:
        adjust.apply_hanging_indent_to_references(doc)
        adjust.bold_years_in_references(doc)
    if request.auto_fix_citations:
        adjust.fix_short_quote_quotes(doc)
        adjust.fix_long_quote_quotes(doc)
    if request.auto_fix_captions:
        adjust.renumber_captions(doc)
        adjust.fix_caption_placement(doc)
    if request.generate_cover and not report.capa.tem_capa:
        adjust.ensure_cover_page(doc, request.metadata)
    # 5. VALIDAÇÃO PÓS-FORMATAÇÃO (para relatório final)
    final_report = validate.validate_all(doc, metadata=request.metadata)
    # 6. Upload resultado → Blob
    # 7. Retornar {download_url, report: final_report}
```

---

## 4. Frontend (`public/`)

### 4.1 `index.html` — Novos Campos
```html
<!-- Metadados da Capa (opcionais, colapsáveis) -->
<details id="metadata-capa">
  <summary>Metadados da Capa (para gerar/validar)</summary>
  <input id="instituicao" placeholder="Universidade Exemplo">
  <input id="autor" placeholder="Nome Completo do Autor">
  <input id="titulo" placeholder="Título do Trabalho">
  <input id="subtitulo" placeholder="Subtítulo (opcional)">
  <input id="cidade" placeholder="Cidade">
  <input id="ano" type="number" value="2026">
</details>

<!-- Auto-fix toggles -->
<fieldset id="auto-fix-options">
  <legend>Auto-correções (aplicar além de reportar)</legend>
  <label><input type="checkbox" name="fix_refs" checked> Referências (entrelinha, ano negrito, ordenação)</label>
  <label><input type="checkbox" name="fix_citas" checked> Citações (aspas curtas/longas)</label>
  <label><input type="checkbox" name="fix_captions"> Legendas (numeração, posição)</label>
  <label><input type="checkbox" name="gen_cover"> Gerar capa se ausente</label>
</fieldset>
```

### 4.2 `app.js` — Relatório Expandido
```javascript
// Nova estrutura de relatório
report = {
  encontrados: [...],
  faltando: [...],
  pendencias: [...],
  validacao: {
    estrutura: { ordem_incorreta: [...], ... },
    citacoes: { curtas_sem_aspas: [...], longas_com_aspas: [...], ... },
    referencias: { fora_ordem: [...], sem_entrelinha: true, ... },
    elementos_visuais: { caption_posicao: [...], numeracao_faltando: [...], ... },
    capa: { tem_capa: true, campos_faltando: [...], ... },
    cross_check: { orphans_citacoes: [...], orphans_referencias: [...] }
  }
}

// UI: Abas ou acordeões por categoria
// Cores: verde (ok), amarelo (atenção), vermelho (ação necessária)
```

---

## 5. Testes

Adicionar em `tests/`:
- `test_validate_structure.py` — ordem NBR 14724, elementos obrigatórios/opcionais
- `test_validate_references.py` — ordenação, entrelinha, negrito ano, DOI, cross-check
- `test_validate_citations.py` — aspas curtas/longas, autor et al., notas rodapé
- `test_validate_visual.py` — posição caption, numeração, fonte
- `test_validate_cover.py` — geração/validação capa
- `test_adjust_fixes.py` — cada auto-correção isolada
- `test_integration_full.py` — fluxo completo .docx → validação → formatação → relatório

---

## 6. Critérios de Aceite

1. ✅ `start.bat` → `.docx` upload funciona (bug corrigido)
2. ✅ Todas as 6 categorias têm validação implementada
3. ✅ Auto-correções aplicadas apenas quando checkbox marcado
4. ✅ Relatório mostra status por categoria + `pendencias` acionáveis
5. ✅ Capa/Folha de rosto gerada/validada com metadados do usuário
6. ✅ Formatação **não altera conteúdo textual** — apenas propriedades de estilo
7. ✅ Testes passam (novos + existentes)

---

## 7. Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Falsos positivos em parsing de citações/referências | Reportar como `pendencias` (não auto-corrigir); testes com amostras reais |
| Ordem de referências: auto-ordenar pode quebrar numeração [1], [2] no texto | Default: **apenas reportar**; auto-ordenar apenas se checkbox explícito + aviso |
| Capa gerada sobrescreve conteúdo existente | Detectar `Title`/`Subtitle` nas 2 primeiras páginas → preservar, só validar |
| Performance em documentos grandes (>100 páginas) | Validação em passada única; `validate_all` opcional no fluxo |
| Conflito entre `adjust.py` formatação e `validate.py` detecção | `validate` roda **antes** e **depois**; `adjust` só formata, não classifica |

---

## 8. Próximos Passos

1. Aprovação deste spec
2. Invocar `writing-plans` → plano de implementação detalhado
3. Execução por fases (bug fix → validate.py → adjust fixes → API → frontend → testes)