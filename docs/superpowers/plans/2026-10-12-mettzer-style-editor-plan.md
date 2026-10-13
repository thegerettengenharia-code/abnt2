# Metter Online Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an open-source online editor for academic works with ABNT formatting, templates, reference generator, and import/export — deployed on Vercel with Next.js 14 + TipTap + FastAPI service.

**Architecture:** Monolito Next.js 14 (App Router) + FastAPI service no Fluid Compute/Railway + PostgreSQL Neon + NextAuth.js v5. Editor TipTap com extensões ABNT. Reutiliza `abnt/` existente em Python. Um deploy (Vercel), auto-scale, $0 hobby tier.

**Tech Stack:**
- Frontend: Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- Editor: TipTap 2.x + ProseMirror + ABNT extensions (custom)
- Backend: FastAPI (Python 3.12) — service de formatação/validação
- Banco: PostgreSQL (Neon serverless) + Prisma ORM
- Auth: NextAuth.js v5 (Auth.js) com GitHub + Google + Email
- Deploy: Vercel (Next.js) + Vercel Fluid Compute (FastAPI) + Vercel Blob
- Editor WYSIWYG: TipTap with nodes: abntHeading, shortQuote, longQuote, referenceEntry, abntTable, abntFigure, coverPage, etc.
- Formatação: Python `adjust.py` / `classify.py` / `config.py` chamados via HTTP interno

**Spec:** `docs/superpowers/specs/2026-10-12-mettzer-style-editor-design.md`

---

## Global Constraints (copiados verbatim da Spec)

1. Open source — código fonte público, MIT/Apache 2.0 license
2. Vercel (atual) / Railway / Render / AWS / self-hosted — deploy único
3. FastAPI service reusa `abnt/` existente — não portar para TypeScript
4. Formatação **apenas** nos elementos detectados — não adiciona/remove conteúdo
5. Validação **antes** e **depois** da formatação → relatório expandido
6. Formatação **não altera** conteúdo textual — apenas propriedades de estilo
7. Flask/NextAuth auth multi-provider (GitHub, Google, email)
8. MVP: Editor + Templates + Import/Export .docx/.pdf + Gerador referências

---

## Review Focus

1. **TipTap ↔ python-docx roundtrip** — perda de formatação complexa (tabelas aninhadas, listas multinível). Teste: roundtrip .docx → JSON → .docx preserva 90% estilos.
2. **Numeração sequencial dinâmica** — tabelas/figuras movidas/deletadas/copiadas. Teste: plugin `abntNumbering` atualiza counters em transações.
3. **Crossref/OpenAlex rate limit + downtime** — cache + fallback manual. Teste: references graceful degradation.
4. **Auth session sharing Vercel Edge ↔ Node** — NextAuth v5 JWT strategy resolve. Teste: auth edge/node produção.
5. **Playwright/Chromium no Fluid Compute** — binary size, cold start. Mitigação: fallback Railway + Puppeteer leve. Teste: PDF export produção.

---

## Tasks by Phase

### **Phase 1: Setup & Auth + Database (Tasks 1–10)**

#### **Task 1: Monolito Next.js 14 + Prisma**

**Files:**
- Create: `package.json` (next@14, typescript, tailwind, prisma)
- Create: `prisma/schema.prisma` (User, Work, Template, Reference, etc.)
- Create: `next.config.mjs`
- Create: `tsconfig.json`
- Modify: `.gitignore`
- Test: `npx prisma migrate dev --name init`

**Interfaces:**
- Consome: nada (setup inicial)
- Produz: schema Prisma, migrations aplicadas

- [ ] **Step 1: Write the failing test**
  Run: `npx prisma migrate make --name init` → espera erro se já existe migration
- [ ] **Step 2: Run test to verify it fails**
  Expected: FAIL migration already exists
- [ ] **Step 3: Implement `npx prisma init` + `prisma migrate make --name init`**
  One line: `prisma init --database-url="postgresql://..."` e answer template1
- [ ] **Step 4: Run test to verify it passes**
  Run: `npx prisma migrate dev --name init` → cria DB + migrations
- [ ] **Step 5: Commit**
  ```bash
  git add prisma/ migration/
  git commit -m "feat: setup prisma schema and initial migration"
  ```

#### **Task 2: Configuração Next.js 14 (App Router)**

**Files:**
- Modify: `next.config.mjs` — `output: "standalone"`, `images.loader: "akamai"`, `env: { DATABASE_URL }`
- Create: `app/layout.tsx` — `<html><head/>`, `<body><Navbar/><Outlet/><Footer/></body></html>`
- Create: `app/page.tsx` — landing page (hero, templates preview, CTA login)
- Create: `app/globals.css` — Tailwind base + shadcn/ui imports
- Test: `npm run dev` → acessa `localhost:3000`

**Interfaces:**
- Consome: nothing
- Produz: Next.js rodando local

- [ ] **Step 1: Write the failing test**
  Run: `npm run dev` → erro se missing deps ou config
- [ ] **Step 2: Run test to verify it fails**
  Expected: dev server não sobe ou página 404
- [ ] **Step 3: Implement** os arquivos acima (copy do spec)
- [ ] **Step 4: Run test to verify it passes**
  Run: `npm run dev` → página inicial carrega em `localhost:3000`
- [ ] **Step 5: Commit**
  ```bash
  git add app/ next.config.mjs tsconfig.json
  git commit -m "feat: nextjs 14 app router setup + landing page"
  ```

#### **Task 3: NextAuth.js v5 (Auth.js) com GitHub + Google + Email**

**Files:**
- Create: `lib/auth.ts` — NextAuth config com PrismaAdapter, GitHub, Google, Credentials
- Create: `app/api/auth/[...nextauth]/route.ts` — NextAuth handler
- Modify: `prisma/schema.prisma` — add `accounts`, `sessions`, `verificationToken` (Prisma auto-adiciona se usar adapter)
- Create: `app/auth/signin/page.tsx` — página login/register
- Create: `app/auth/callback/route.tsx` — callback handlers
- Test: `npm run auth:test` (simular login)

**Interfaces:**
- Consome: Prisma schema com User, Account, Session, VerificationToken
- Produz: sessão auth, usuário logged in

- [ ] **Step 1: Write the failing test**
  Run: `curl - POST /api/auth/signin` → 401 ou redirect
- [ ] **Step 2: Run test to verify it fails**
  Expected: auth não configurado, redirect loop
- [ ] **Step 3: Implement** lib/auth.ts + routes + signin page
- [ ] **Step 4: Run test to verify it passes**
  Run: login com GitHub → usuario criado/logado → redirect para `/dashboard`
- [ ] **Step 5: Commit**
  ```bash
  git add lib/ auth/ prisma/schema.prisma
  git commit -m "feat: nextauth auth with github/google/email providers"
  ```

#### **Task 4: Prisma Schema Completo + Migrations**

**Files:**
- Modify: `prisma/schema.prisma` — Work, Template, Reference, WorkVersion, Comment, TemplateCategory, SourceType, Role, WorkStatus
- Run: `npx prisma migrate add --name auth-and-models`
- Run: `npx prisma migrate deploy`
- Test: `npx prisma generate` + `npx prisma studio`

**Interfaces:**
- Consome: Task 2 auth básico
- Produz: schema completo, migrations aplicadas ao DB

- [ ] **Step 1: Write the failing test**
  Run: `npx prisma migrate add --name auth-and-models` → erro se schema já tem fields
- [ ] **Step 2: Run test to verify it fails**
  Expected: migration error — field already exists ou missing import
- [ ] **Step 3: Implement** schema.prisma completo (copy das definições da Spec)
- [ ] **Step 4: Run test to verify it passes**
  Run: `npx prisma migrate deploy` → migrations aplicadas; `npx prisma studio` → tabelas criadas
- [ ] **Step 5: Commit**
  ```bash
  git add prisma/ migrations/
  git commit -m "feat: prisma schema complete + migrations deploy"
  ```

#### **Task 5: Dashboard (Lista/cria/exclui trabalhos)**

**Files:**
- Create: `app/dashboard/page.tsx` — grid de trabalhos, filtros, botão "Novo"
- Create: `app/api/works/route.ts` — GET (lista works do usuário) + POST (cria novo work)
- Modify: `lib/auth.ts` — proteger rotas com `auth()`
- Test: `npx playwright test --grep dashboard`

**Interfaces:**
- Consome: User session (Task 3), Prisma (Task 4)
- Produz: lista de works, form create

- [ ] **Step 1: Write the failing test**
  Run: `curl GET /api/works` sem auth → 401
- [ ] **Step 2: Run test to verify it fails**
  Expected: 401 Unauthorized
- [ ] **Step 3: Implement** app/dashboard + api/works + protect routes
- [ ] **Step 4: Run test to verify it passes**
  Run: login → GET /api/works → lista vazio; criar work → aparece na lista
- [ ] **Step 5: Commit**
  ```bash
  git add app/dashboard/ app/api/works/ lib/auth.ts
  git commit -m "feat: dashboard + CRUD works com auth protection"
  ```

#### **Task 6: TipTap Editor (Setup básico + Toolbar)**

**Files:**
- Create: `components/tiptap/Editor.tsx` — `<Editor />` com `tipTap`, toolbar básica (bold, italic, heading)
- Create: `components/tiptap/Toolbar.tsx` — botões: fonte, tamanho, negrito, itálico, heading 1/2/3
- Import: `npm i @tiptap/react @tiptap/starter-kit`
- Test: `npm run dev` → editor carrega, toolbar funciona

**Interfaces:**
- Consome: nada (setup UI)
- Produz: editor TipTap renderizado

- [ ] **Step 1: Write the failing test**
  Run: `npm run dev` → erro se @tiptap packages missing ou config TS
- [ ] **Step 2: Run test to verify it fails**
  Expected: editor não renderiza ou toolbar quebra
- [ ] **Step 3: Implement** Editor + Toolbar componentes (copy do spec, TipKit básico)
- [ ] **Step 4: Run test to verify it passes**
  Run: editor carrega com toolbar [B I U] + headings
- [ ] **Step 5: Commit**
  ```bash
  git add components/tiptap/
  git commit -m "feat: TipTap editor basic setup + toolbar"
  ```

#### **Task 7: ABNT Core Extensions (headings, citações, referências)**

**Files:**
- Create: `components/tiptap/extensions/abnt-core.ts` — global attributes abntRole
- Create: `components/tiptap/extensions/abnt-heading.ts` — heading numerado/nao-numerado
- Create: `components/tiptap/extensions/abnt-citation.ts` — ShortQuote + LongQuote nodes
- Create: `components/tiptap/extensions/abnt-reference.ts` — ReferenceEntry node
- Modify: `components/tiptap/Editor.tsx` — adicionar extensions ao editor
- Test: validar headings numeração + citações

**Interfaces:**
- Consome: Editor (Task 6)
- Produz: TipTap com formatação ABNT (headings num, citações, referências)

- [ ] **Step 1: Write the failing test**
  Run: `npm run dev` → editor carrega mas extensions dão erro (missing import)
- [ ] **Step 2: Run test to verify it fails**
  Expected: TypeError: cannot read properties of undefined (extension not applied)
- [ ] **Step 3: Implement** extensions ABNT (copy spec, registrações no Editor)
- [ ] **Step 4: Run test to verify it passes**
  Run: heading 1 auto-number "1", "2"; citação curta `(SILVA, 2023)`; referência entrada salva
- [ ] **Step 5: Commit**
  ```bash
  git add components/tiptap/extensions/ lib/tiptap/
  git commit -m "feat: ABNT core extensions + heading num + citations"
  ```

#### **Task 8: Templates (TCC, Artigo, Projeto + placeholders)**

**Files:**
- Create: `templates/tcc-abnt.json` — JSON content + schema (ver spec section 8)
- Create: `components/templates/Gallery.tsx` — grid de cards, preview, "Usar este template"
- Modify: Editor.tsx — ao clicar em template, substituir content inicial
- Test: novo work a partir de template carrega corretamente

**Interfaces:**
- Consome: Editor (Task 7), Prisma (Task 4) — Template model
- Produz: novo work com estrutura de template

- [ ] **Step 1: Write the failing test**
  Run: clicar "Usar template TCC" → error se JSON inválido ou template não mapeado
- [ ] **Step 2: Run test to verify it fails**
  Expected: editor content não atualiza ou quebra ao carregar template JSON
- [ ] **Step 3: Implement** templates JSON + gallery + mapeamento para content inicial
- [ ] **Step 4: Run test to verify it passes**
  Run: novo work → content = JSON do template TCC com placeholders visíveis
- [ ] **Step 5: Commit**
  ```bash
  git add templates/ components/templates/ components/tiptap/Editor.tsx
  git commit -m "feat: templates gallery + JSON structures + placeholder mapping"
  ```

#### **Task 9: Import .docx → TipTap JSON**

**Files:**
- Create: `components/tiptap/imports/importDocx.tsx` — botão "Import .docx"
- Criar endpoint FastAPI `/import-docx` (Task 14 será separado, mas helper aqui)
- Usar `mammoth.docx` + mapping manual para nodes TipTap
- Test: upload .docx simples → content editor populado

**Interfaces:**
- Consome: upload .docx (File), FastAPI `/import-docx`
- Produz: TipTap JSON no editor

- [ ] **Step 1: Write the failing test**
  Run: tentar import .docx → error se mammoth não instalado ou endpoint não existe
- [ ] **Step 2: Run test to verify it fails**
  Expected: import button broken ou console error
- [ ] **Step 3: Implement** import helper + endpoint FastAPI helper (wrapper para Task 14)
- [ ] **Step 4: Run test to verify it passes**
  Run: upload .docx (ex: relatório simples) → content editor populado com headings + parágrafos
- [ ] **Step 5: Commit**
  ```bash
  git add components/tiptap/imports/ service/import_docx.py
  git commit -m "feat: .docx import via mammoth + python mapping"
  ```

#### **Task 10: Validação ABNT Tempo Real (useAbntValidation)**

**Files:**
- Create: `hooks/useAbntValidation.ts` — fetch `/api/validate` a cada transaction
- Create: `components/tiptap/validation/ValidationPanel.tsx` — lista issues (margem esquerda, citation issues, etc)
- Modify: Editor.tsx — integrar hook + panel
- Test: digitar no editor → issues aparecem/desaparecem

**Interfaces:**
- Consome: Editor JSON, FastAPI `/validate`
- Produz: lista visual de issues + cores (verde/amarelo/vermelho)

- [ ] **Step 1: Write the failing test**
  Run: digitar no editor → error se `/api/validate` não existe ainda
- [ ] **Step 2: Run test to verify it fails**
  Expected: validation panel não aparece ou console error fetch
- [ ] **Step 3: Implement** hook + panel + integrar no Editor
- [ ] **Step 4: Run test to verify it passes**
  Run: digitar citação sem aspas → issue "curtas sem aspas" aparece em vermelho
- [ ] **Step 5: Commit**
  ```bash
  git add hooks/ components/tiptap/validation/ lib/service/validate.py
  git commit -m "feat: real-time ABNT validation + issue panel"
  ```

---

### **Phase 2: FastAPI Service + Formatação (Tasks 11–18)**

#### **Task 11: FastAPI Service Scaffold + /format**

**Files:**
- Create: `service/main.py` — FastAPI app + `/format` endpoint skeleton
- Create: `service/models.py` — Pydantic models (FormatRequest, FormatResponse)
- Create: `service/format.py` — lógica: TipTap JSON → python-docx → adjust.adjust_docx → json de volta
- Create: `service/validate.py` — validação validate_all (wrapper para abnt.validate)
- Test: `uvicorn service.main:app --reload` → docs em `/docs`

**Interfaces:**
- Consome: TipTap JSON + font + metadata
- Produz: TipTap JSON formatado + ValidationReport

- [ ] **Step 1: Write the failing test**
  Run: `uvicorn service.main:app` → error se missing deps (python-docx, adjust)
- [ ] **Step 2: Run test to verify it fails**
  Expected: ImportError ou AttributeError (adjust_docx missing line)
- [ ] **Step 3: Implement** scaffold + ajustar o bug crítico do `def adjust_docx(...)` (missing line + 3-arg calls fix)
- [ ] **Step 4: Run test to verify it passes**
  Run: `uvicorn service.main:app` → docs funcionam; `/format` POST com JSON teste retorna JSON formatado
- [ ] **Step 5: Commit**
  ```bash
  git add service/ main.py
  git commit -m "feat: FastAPI scaffold + /format endpoint + adjust_docx bug fix"
  ```

#### **Task 12: /validate Endpoint + ValidationReport**

**Files:**
- Modify: `service/validate.py` — função `validate_all(doc, metadata)` → Structure/Citation/Reference/Visual/Cover/CrossCheck
- Modify: `service/models.py` — ValidationReport, StructureValidation, CitationValidation, ReferenceValidation, VisualValidation, CoverValidation, CrossCheckResult dataclasses
- Test: POST /validate com JSON TipTap → report JSON estruturado

**Interfaces:**
- Consome: TipTap JSON + metadata opcional
- Produz: ValidationReport com fields por categoria

- [ ] **Step 1: Write the failing test**
  Run: `curl - POST /validate` → 422 ou error de modelo Pydantic
- [ ] **Step 2: Run test to verify it fails**
  Expected: ValidationReport fields faltando ou tipos incompatíveis
- [ ] **Step 3: Implement** validate.py + models.py dataclasses (espec section 3.1)
- [ ] **Step 4: Run test to verify it passes**
  Run: validation report traz `estrutura.encontrados`, `citacoes.curtas_sem_aspas`, `referencias.fora_ordem`, etc.
- [ ] **Step 5: Commit**
  ```bash
  git add service/validate.py service/models.py
  git commit -m "feat: validate_all + ValidationReport dataclasses"
  ```

#### **Task 13: /references/generate Endpoint**

**Files:**
- Modify: `service/references.py` — `generate_from_doi_isbn_url(dois, isbns, urls)` → CSL-JSON → ABNT string
- Usar `citeproc-python` + style `abnt.csl` (baixar do GitHub citeproc-styles) ou CSL manual
- Test: POST /references/generate com dois → retorna entrada ABNT salva + insere no editor

**Interfaces:**
- Consome: list[str] dois/isbns/urls
- Produz: [{csl, abnt, source, source_id}] + salva no DB Reference table

- [ ] **Step 1: Write the failing test**
  Run: `curl - POST /references/generate` → error se citeproc-python não instalado ou CSL style não encontrado
- [ ] **Step 2: Run test to verify it fails**
  Expected: ImportError ou CSLCannotParse
- [ ] **Step 3: Implement** references.py (baixar abnt.csl, implementar csl_to_abnt, cache em Redis Upstash opcional)
- [ ] **Step 4: Run test to verify it passes**
  Run: dois DOI → entrada ABNT formatada + salva no DB + retorna JSON
- [ ] **Step 5: Commit**
  ```bash
  git add service/references.py
  git commit -m "feat: references generator DOI/ISBN/URL → ABNT + citeproc-python"
  ```

#### **Task 14: /import-docx + /export-docx + /export-pdf**

**Files:**
- Modify: `service/import_docx.py` — `import_docx(file_bytes)` → TipTap JSON via python-docx + classify mapping (heading→abntHeading, table→abntTable, figcaption→abntFigure)
- Modify: `service/export_docx.py` — `export_to_docx(tiptap_json, font)` → Document python-docx + adjust.adjust_docx final
- Modify: `service/export_pdf.py` — `export_to_pdf(tiptap_json, html)` → render HTML + Playwright/Chromium headless → PDF bytes
- Test: import .docx → editor; export .docx → download; export PDF → download

**Interfaces:**
- Consome: arquivo .docx bytes / TipTap JSON
- Produz: TipTap JSON ou .docx/.pdf bytes

- [ ] **Step 1: Write the failing test**
  Run: tentar import .docx → error se python-docx version incompatível ou mapping missing
- [ ] **Step 2: Run test to verify it fails**
  Expected: ImportError ou KeyError mapping node → paragraph style
- [ ] **Step 3: Implement** import_docx.py (mapping: `w:pStyle → "heading_1"` etc + classify.detect), export_docx.py (adjust.adjust_docx chamado pós-format), export_pdf.py (Playwright install + render)
- [ ] **Step 4: Run test to verify it passes**
  Run: upload .docx simples → JSON editor; export .docx → download abre no Word com formatação ABNT; export PDF → PDF visualmente fiel
- [ ] **Step 5: Commit**
  ```bash
  git add service/import_docx.py service/export_docx.py service/export_pdf.py
  git commit -m "feat: import .docx + export .docx + export PDF via Python service"
  ```

#### **Task 15: FastAPI CORS + Vercel Fluid Compute config**

**Files:**
- Modify: `service/main.py` — `app.add_middleware(CORSMiddleware, allow_origins=[...], allow_methods=["*"], allow_headers=["*"])`
- Create: `vercel.json` — FastAPI function config (min=0, max=1, timeout=30) — ou Railway
- Test: `vercel deploy` ou `vercel preview` — service acessível do Next.js

**Interfaces:**
- Consome: HTTP do Next.js (mesma região)
- Produz: JSON formatado/validado/referências

- [ ] **Step 1: Write the failing test**
  Run: do Next.js fetch('/api/format') → CORS error ou 500
- [ ] **Step 2: Run test to verify it fails**
  Expected: bloqueado por CORS ou erro de rota
- [ ] **Step 3: Implement** CORS middleware + vercel.json config + test cross-region fetch
- [ ] **Step 4: Run test to verify it passes**
  Run: do navegador Next.js `fetch('/api/format', {method: 'POST', body: json})` → JSON retornado sem erro
- [ ] **Step 5: Commit**
  ```bash
  git add service/main.py vercel.json
  git commit -m "feat: CORS + Vercel Fluid Compute config for FastAPI service"
  ```

---

### **Phase 3: Polish & Deploy (Tasks 19–22)**

#### **Task 16: Referências no Editor + Work References**

**Files:**
- Modify: `components/references/Gallery.tsx` — listar referências salvas, buscar DOI/ISBN/URL, inserir no editor
- Modify: `components/works/WorkShow.tsx` — sidebar referências, botão "Inserir citação"
- Modify: `useAbntValidation.ts` — issue "referências não citadas" + "citadas não referenciadas"
- Test: inserir citação `(SILVA, 2023)` no editor → aparecer na lista de referências + número no texto

**Interfaces:**
- Consome: editor state, FastAPI `/references/generate`, Prisma Reference table
- Produz: referência inserida no editor + workReferences no DB

- [ ] **Step 1: Write the failing test**
  Run: tentar inserir citação no editor → error se Reference table vazia ou citação key não encontrada
- [ ] **Step 2: Run test to verify it fails**
  Expected: citação não aparece no texto ou referência não salva
- [ ] **Step 3: Implement** referência gallery + inserção + validação cross-check
- [ ] **Step 4: Run test to verify it passes**
  Run: buscar DOI "10.1000/exemplo" → entrada aparece em referências + `(SILVA, 2023)` insere no cursor
- [ ] **Step 5: Commit**
  ```bash
  git add components/references/ components/works/ hooks/useAbntValidation.ts
  git commit -m "feat: reference manager + insert citations + cross-check validation"
  ```

#### **Task 17: Export .docx + PDF do Work (do Dashboard)**

**Files:**
- Modify: `app/works/[id]/page.tsx` — botões "Export .docx" + "Export PDF"
- Integrar com FastAPI `/export-docx` + `/export-pdf`
- Test: work aberto → exportar ambos os formatos → download

**Interfaces:**
- Consome: work content (TipTap JSON), metadata, FastAPI endpoints
- Produz: arquivos .docx/.pdf baixáveis

- [ ] **Step 1: Write the failing test**
  Run: clicar export .docx → error se endpoint não recebe content ou filename
- [ ] **Step 2: Run test to verify it fails**
  Expected: download corrompido ou 500 error
- [ ] **Step 3: Implement** botões + fetch endpoints + blob download
- [ ] **Step 4: Run test to verify it passes**
  Run: work com template TCC → .docx download → abre no Word com formatação ABNT; PDF download → visualmente fiel
- [ ] **Step 5: Commit**
  ```bash
  git add app/works/ page.tsx service/export_*.py
  git commit -m "feat: work export .docx + PDF + download integrada"
  ```

#### **Task 18: Deploy Final no Vercel + Testes E2E**

**Files:**
- Modify: `vercel.json` — add Functions FastAPI, env vars (DATABASE_URL, FASTAPI_URL, NEXTAUTH_SECRET, etc)
- Create: `playwright.config.ts` — e2e tests (login, criar work, template, validação, import, export)
- Run: `npx playwright test` — todos os testes passam
- Deploy: `vercel --prod` — site online, funcional

**Interfaces:**
- Consome: nada (deploy)
- Produz: site público no Vercel, domínio vercel.app, todos os fluxos funcionando

- [ ] **Step 1: Write the failing test**
  Run: `npx playwright test` → erro se seletores seletores seletores seletores
- [ ] **Step 2: Run test to verify it fails**
  Expected: test fails no setup (browser not found, env vars missing)
- [ ] **Step 3: Implement** playwright config + e2e tests covering os 12 critérios de aceite da Spec
- [ ] **Step 4: Run test to verify it passes**
  Run: `npx playwright test --grep "full flow"` → todos os cenários passam (login → template → edit → validate → import → export)
- [ ] **Step 5: Commit**
  ```bash
  git add playwright.config.ts e2e/ tests/
  git commit -m "feat: e2e tests + vercel.prod deploy config"
  ```

#### **Task 19: README + License + Open Source Setup**

**Files:**
- Create: `README.md` — setup local (`docker compose up`), deployment (`vercel`), contribuição
- Create: `LICENSE` — MIT (ou Apache 2.0)
- Create: `.github/CONTRIBUTING.md` — guidelines for PRs, branch strategy, code style
- Test: `README` lido e entendido por novo contribuinte

**Interfaces:**
- Consome: nada (documentação)
- Produz: onboarding de novo dev

- [ ] **Step 1: Write the failing test**
  Run: `cat README.md` → ver se existe
- [ ] **Step 2: Run test to verify it fails**
  Expected: file não existe ou incompleto
- [ ] **Step 3: Implement** README + LICENSE + CONTRIBUTING (copy do spec section 18)
- [ ] **Step 4: Run test to verify it passes**
  Run: novo dev lê README → entende `docker compose up`, `vercel deploy`, `how to contribute`
- [ ] **Step 5: Commit**
  ```bash
  git add README.md LICENSE .github/CONTRIBUTING.md
  git commit -m "feat: README + license + contributing guide"
  ```

#### **Task 20: Roadmap Future (v2+v3)**

**Files:**
- Create: `docs/ROADMAP.md` — features planejadas pós-MVP: IA (tema/resumo/citações), colaboração (comentários, versões), publicação no Hub, plano de estudos, equações LaTeX, integração Overleaf

**Interfaces:**
- Consome: nada (documento de roadmap)
- Produz: plano de 12-18 meses para evolução do produto

- [ ] **Step 1: Write the failing test**
  Run: ver se `docs/ROADMAP.md` existe
- [ ] **Step 2: Run test to verify it fails**
  Expected: file não existe
- [ ] **Step 3: Implement** roadmap baseado no spec section 17 (v2+v3 wishes)
- [ ] **Step 4: Run test to verify it passes**
  Run: roadmap lido — contempla IA, colaboração, hub, LaTeX
- [ ] **Step 5: Commit**
  ```bash
  git add docs/ROADMAP.md
  git commit -m "feat: roadmap v2+v3 wishes"
  ```

---