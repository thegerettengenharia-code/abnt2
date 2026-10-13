# Spec: Editor Online Estilo Mettzer (Open Source)

**Data:** 2026-10-12
**Status:** Aprovado para implementação
**Classificação:** Architectural
**Abordagem:** Monolito Next.js 14 + FastAPI Service (Abordagem A)

---

## 1. Resumo

Criar um **editor WYSIWYG online open source** para trabalhos acadêmicos ABNT/APA, inspirado no Mettzer, com:
- Formatação tempo real (TipTap + Python service)
- Templates prontos (TCC, artigo, projeto, relatório, fichamento)
- Gerador de referências (Crossref/OpenAlex → ABNT)
- Import .docx / Export PDF + .docx
- Auth multi-provider (NextAuth)
- Dashboard de trabalhos
- Deploy único no Vercel + FastAPI no Fluid Compute/Railway

**Filosofia:** Open source first, extensível, sem vendor lock-in, reusa `abnt/` existente.

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VERCEL                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        NEXT.JS 14 (APP ROUTER)                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ Dashboard   │  │ Editor      │  │ Templates   │  │ Auth       │  │   │
│  │  │ (RSC)       │  │ (Client)    │  │ (RSC)       │  │ (NextAuth) │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │   │
│  │         │                │                │                │         │   │
│  │  ┌──────▼────────────────▼────────────────▼────────────────▼────┐   │   │
│  │  │                    NEXT.JS API ROUTES                        │   │   │
│  │  │  /api/works | /api/templates | /api/references | /api/files │   │   │
│  │  └────────────────────────────┬────────────────────────────────┘   │   │
│  └───────────────────────────────│────────────────────────────────────┘   │
│                                  │ HTTP (internal, same region)          │
└──────────────────────────────────│────────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI SERVICE (Fluid Compute / Railway)            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ /format         │  │ /validate       │  │ /references                 │ │
│  │ (adjust_docx)   │  │ (validate_all)  │  │ (generate_from_doi_isbn)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ /import-docx    │  │ /export-docx    │  │ /export-pdf                 │ │
│  │ (mammoth+abnt)  │  │ (python-docx)   │  │ (playwright/chromium)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        POSTGRESQL (Neon / Vercel Postgres / Supabase)       │
│  works, templates, references, users, accounts, sessions, verification    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Comunicação:**
- Next.js → FastAPI: HTTP interno (mesma região, baixa latência)
- Auth: NextAuth.js (JWT strategy, cookies httpOnly)
- Files: Vercel Blob (temporário) ou Supabase Storage

---

## 3. Tech Stack

| Camada | Escolha | Justificativa |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) + TypeScript | Vercel nativo, RSC, Server Actions |
| **Editor** | TipTap 2.x (ProseMirror wrapper) | Extensível, headless, ABNT via extensions |
| **Styling** | Tailwind CSS + shadcn/ui | Consistente, acessível, dark mode |
| **Backend API** | Next.js API Routes + Server Actions | Serverless, mesmo deploy, type-safe |
| **Auth** | NextAuth.js v5 (Auth.js) | Open source, multi-provider, edge-compatible |
| **Banco** | PostgreSQL (Neon serverless) + Prisma ORM | Grátis hobby, auto-scale, type-safe |
| **Formatação** | FastAPI + `abnt/` (Python 3.12) | Reusa código complexo, PyMuPDF, python-docx |
| **Deploy** | Vercel (Next.js) + Vercel Fluid Compute (FastAPI) | Um painel, auto-scale, $0 hobby |
| **Storage** | Vercel Blob (temp) / Supabase Storage | Integrado, CDN global |

---

## 4. Database Schema (Prisma)

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id            String    @id @default(cuid())
  name          String?
  email         String    @unique
  emailVerified DateTime?
  image         String?
  passwordHash  String?   // para credentials provider
  role          Role      @default(STUDENT)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  accounts      Account[]
  sessions      Session[]
  works         Work[]
  templates     Template[]
  references    Reference[]
}

model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String? @db.Text
  access_token      String? @db.Text
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String? @db.Text
  session_state     String?

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
}

model Session {
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}

model VerificationToken {
  identifier String
  token      String   @unique
  expires    DateTime

  @@unique([identifier, token])
}

model Work {
  id          String   @id @default(cuid())
  title       String
  content     Json     // TipTap JSON document
  html        String?  @db.Text // rendered HTML for PDF export
  status      WorkStatus @default(DRAFT)
  templateId  String?
  userId      String
  metadata    Json?    // { instituicao, autor, titulo, subtitulo, cidade, ano, tipo }
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  publishedAt DateTime?

  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  template    Template? @relation(fields: [templateId], references: [id], onDelete: SetNull)
  versions    WorkVersion[]
  comments    Comment[]
  references  WorkReference[]
}

model WorkVersion {
  id        String   @id @default(cuid())
  workId    String
  content   Json     // TipTap JSON snapshot
  label     String?  // "v1.0 - antes da orientação"
  createdAt DateTime @default(now())

  work Work @relation(fields: [workId], references: [id], onDelete: Cascade)
}

model Template {
  id          String   @id @default(cuid())
  name        String   // "TCC ABNT", "Artigo Científico APA"
  description String?
  category    TemplateCategory
  content     Json     // TipTap JSON structure with placeholders
  schema      Json     // TipTap schema extensions for this template
  isOfficial  Boolean  @default(false)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  works       Work[]
}

model Reference {
  id          String   @id @default(cuid())
  userId      String
  sourceType  SourceType // DOI, ISBN, URL, MANUAL
  sourceId    String   // DOI/ISBN/URL hash
  data        Json     // parsed CSL-JSON
  abnt        String   // formatted ABNT string
  createdAt   DateTime @default(now())

  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  workRefs    WorkReference[]
}

model WorkReference {
  id           String    @id @default(cuid())
  workId       String
  referenceId  String
  citationKey  String?   // "SILVA, 2023" for in-text citation
  order        Int       @default(0)

  work         Work      @relation(fields: [workId], references: [id], onDelete: Cascade)
  reference    Reference @relation(fields: [referenceId], references: [id], onDelete: Cascade)

  @@unique([workId, referenceId])
}

model Comment {
  id        String   @id @default(cuid())
  workId    String
  userId    String
  content   String   @db.Text
  position  Json?    // { from: number, to: number, anchor: string }
  resolved  Boolean  @default(false)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  work Work @relation(fields: [workId], references: [id], onDelete: Cascade)
  user User @relation(fields: [userId], references: [id], onDelete: Cascade)
}

enum Role {
  STUDENT
  PROFESSOR
  RESEARCHER
  ADMIN
}

enum WorkStatus {
  DRAFT
  IN_REVIEW
  APPROVED
  PUBLISHED
}

enum TemplateCategory {
  TCC
  ARTICLE
  PROJECT
  REPORT
  FICHAMENTO
  PIM
  THESIS
  DISSERTATION
  OTHER
}

enum SourceType {
  DOI
  ISBN
  URL
  MANUAL
}
```

---

## 5. TipTap Extensions para ABNT

### 5.1 Extensões Core (sempre ativas)

```typescript
// extensions/abnt-core.ts
import { Extension, mergeAttributes } from '@tiptap/core'

export const AbntCore = Extension.create({
  name: 'abntCore',
  addGlobalAttributes() {
    return [{
      types: ['paragraph', 'heading', 'textStyle'],
      attributes: {
        abntRole: {
          default: 'body',
          parseHTML: element => element.getAttribute('data-abnt-role') || 'body',
          renderHTML: attributes => ({
            'data-abnt-role': attributes.abntRole
          })
        }
      }
    }]
  }
})
```

### 5.2 Heading ABNT (numeração automática)

```typescript
// extensions/abnt-heading.ts
import { Heading, HeadingOptions } from '@tiptap/extension-heading'

export const AbntHeading = Heading.extend<HeadingOptions>({
  name: 'abntHeading',
  addOptions() {
    return {
      ...this.parent?.(),
      levels: [1, 2, 3, 4],
      numbering: true // auto-number via ProseMirror plugin
    }
  },
  addAttributes() {
    return {
      ...this.parent?.(),
      level: {
        default: 1,
        rendered: false
      },
      isUnnumbered: {
        default: false,
        parseHTML: element => element.hasAttribute('data-unnumbered'),
        renderHTML: attributes => {
          if (attributes.isUnnumbered) return { 'data-unnumbered': '' }
          return {}
        }
      }
    }
  },
  addCommands() {
    return {
      ...this.parent?.(),
      setAbntHeading: (attrs: { level: number; isUnnumbered?: boolean }) => ({ commands }) => {
        return commands.setHeading({ level: attrs.level, ...attrs })
      }
    }
  }
})
```

### 5.3 Citação Curta/Longa

```typescript
// extensions/abnt-citation.ts
import { Node, NodeSpec } from '@tiptap/pm/model'

export const ShortQuote = Node.create({
  name: 'shortQuote',
  group: 'inline',
  content: 'inline*',
  inline: true,
  addAttributes() {
    return {
      author: { default: '' },
      year: { default: '' },
      page: { default: '' }
    }
  },
  parseHTML() {
    return [{ tag: 'span[data-short-quote]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(HTMLAttributes, {
      'data-short-quote': '',
      'data-author': HTMLAttributes.author,
      'data-year': HTMLAttributes.year,
      'data-page': HTMLAttributes.page,
      class: 'abnt-short-quote'
    }), 0]
  },
  addCommands() {
    return {
      insertShortQuote: (attrs) => ({ commands }) => {
        return commands.insertContent({
          type: 'shortQuote',
          attrs,
          content: [{ type: 'text', text: `"${attrs.text}" (${attrs.author}, ${attrs.year}${attrs.page ? `, p. ${attrs.page}` : ''})` }]
        })
      }
    }
  }
})

export const LongQuote = Node.create({
  name: 'longQuote',
  group: 'block',
  content: 'inline*',
  addAttributes() {
    return {
      author: { default: '' },
      year: { default: '' },
      page: { default: '' }
    }
  },
  parseHTML() {
    return [{ tag: 'blockquote[data-long-quote]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['blockquote', mergeAttributes(HTMLAttributes, {
      'data-long-quote': '',
      class: 'abnt-long-quote'
    }), 0]
  }
})
```

### 5.4 Referência (entrada bibliográfica)

```typescript
// extensions/abnt-reference.ts
export const ReferenceEntry = Node.create({
  name: 'referenceEntry',
  group: 'block',
  content: 'inline*',
  addAttributes() {
    return {
      referenceId: { default: '' }, // UUID from Reference table
      type: { default: 'book' }, // book, article, thesis, etc.
      authors: { default: [] }, // [{ surname, given, prefix }]
      year: { default: '' },
      title: { default: '' },
      doi: { default: '' }
    }
  },
  parseHTML() {
    return [{ tag: 'p[data-reference-entry]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['p', mergeAttributes(HTMLAttributes, {
      'data-reference-entry': '',
      'data-reference-id': HTMLAttributes.referenceId,
      class: 'abnt-reference-entry'
    }), 0]
  }
})
```

### 5.5 Tabela/Figura com Legenda e Fonte

```typescript
// extensions/abnt-figure-table.ts
export const AbntTable = Node.create({
  name: 'abntTable',
  group: 'block',
  content: 'caption? (tableHeader? tableBody)',
  tableRole: 'table',
  addAttributes() {
    return {
      number: { default: 0 },
      title: { default: '' },
      source: { default: '' }
    }
  },
  // ... table editing commands + caption above
})

export const AbntFigure = Node.create({
  name: 'abntFigure',
  group: 'block',
  content: '(image caption?)',
  addAttributes() {
    return {
      number: { default: 0 },
      title: { default: '' },
      source: { default: '' },
      type: { default: 'figure' } // figure, quadro, grafico
    }
  }
  // caption below, source below caption
})
```

### 5.6 Plugin de Numeração Sequencial

```typescript
// plugins/abnt-numbering.ts
import { Plugin, PluginKey } from '@tiptap/pm/state'

export const abntNumberingPlugin = new Plugin({
  key: new PluginKey('abntNumbering'),
  state: {
    init() {
      return { tables: 0, figures: 0, quadros: 0, equations: 0 }
    },
    apply(tr, prev) {
      // Inspect transaction for added/removed abntTable/abntFigure
      // Update counters, store in state
      return nextState
    }
  },
  props: {
    decorations(state) {
      // Add dynamic numbers to captions via Decoration.widget
    }
  }
})
```

---

## 6. FastAPI Service API (Python)

```python
# service/main.py
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import json

app = FastAPI(title="ABNT Format Service")

# --- Models ---
class FormatRequest(BaseModel):
    content: dict  # TipTap JSON
    font: str = "Times New Roman"
    metadata: Optional[dict] = None  # capa fields
    auto_fix: Optional[dict] = None  # {refs, citations, captions, cover}

class ValidateRequest(BaseModel):
    content: dict
    metadata: Optional[dict] = None

class ReferenceRequest(BaseModel):
    dois: List[str] = []
    isbns: List[str] = []
    urls: List[str] = []

class ExportRequest(BaseModel):
    content: dict
    format: str  # "docx" | "pdf"
    filename: str

# --- Endpoints ---
@app.post("/format")
async def format_document(req: FormatRequest):
    """Aplica formatação ABNT ao TipTap JSON → retorna TipTap JSON formatado"""
    # 1. TipTap JSON → python-docx Document
    # 2. adjust.adjust_docx(doc, font, metadata)
    # 3. python-docx Document → TipTap JSON
    # 4. validate.validate_all(doc, metadata) → report
    return {"content": formatted_json, "report": validation_report}

@app.post("/validate")
async def validate_document(req: ValidateRequest):
    """Valida sem modificar → retorna ValidationReport"""
    return validation_report

@app.post("/references/generate")
async def generate_references(req: ReferenceRequest):
    """Crossref (DOI) / OpenLibrary (ISBN) / OpenAlex (URL) → ABNT entries"""
    entries = []
    for doi in req.dois:
        csl = await crossref_fetch(doi)
        abnt = csl_to_abnt(csl)
        entries.append({"csl": csl, "abnt": abnt, "source": "doi", "source_id": doi})
    # similar for ISBN, URL
    return {"references": entries}

@app.post("/import-docx")
async def import_docx(file: UploadFile = File(...)):
    """Upload .docx → TipTap JSON"""
    # mammoth.js style conversion via python-docx + custom mapping
    return {"content": tiptap_json}

@app.post("/export-docx")
async def export_docx(req: ExportRequest):
    """TipTap JSON → .docx (bytes)"""
    return StreamingResponse(docx_bytes, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.post("/export-pdf")
async def export_pdf(req: ExportRequest):
    """TipTap JSON → PDF (bytes) via Playwright/Chromium"""
    # render HTML → PDF with print CSS
    return StreamingResponse(pdf_bytes, media_type="application/pdf")
```

---

## 7. Next.js API Routes (TypeScript)

```typescript
// app/api/works/route.ts
import { getServerSession } from 'next-auth'
import { prisma } from '@/lib/prisma'
import { authOptions } from '@/lib/auth'

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session?.user) return new Response('Unauthorized', { status: 401 })

  const works = await prisma.work.findMany({
    where: { userId: session.user.id },
    include: { template: true, _count: { select: { versions: true } } },
    orderBy: { updatedAt: 'desc' }
  })
  return Response.json(works)
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user) return new Response('Unauthorized', { status: 401 })

  const { title, templateId, metadata } = await req.json()
  const work = await prisma.work.create({
    data: {
      title,
      templateId,
      userId: session.user.id,
      content: await getTemplateContent(templateId),
      metadata
    }
  })
  return Response.json(work)
}

// app/api/works/[id]/format/route.ts
export async function POST(req: Request, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions)
  const work = await prisma.work.findUnique({ where: { id: params.id } })
  // check ownership
  // call FastAPI /format
  // save version
  // update work content
  // return { content, report }
}

// app/api/references/generate/route.ts
export async function POST(req: Request) {
  const { dois, isbns, urls } = await req.json()
  // call FastAPI /references/generate
  // save to Reference table
  // return references
}
```

---

## 8. Templates (JSON + Placeholders)

```json
// templates/tcc-abnt.json
{
  "name": "TCC ABNT",
  "category": "TCC",
  "content": {
    "type": "doc",
    "content": [
      { "type": "coverPage", "attrs": { "placeholder": true } },
      { "type": "titlePage", "attrs": { "placeholder": true } },
      { "type": "approvalPage", "attrs": { "placeholder": true } },
      { "type": "dedication", "attrs": { "placeholder": true } },
      { "type": "acknowledgments", "attrs": { "placeholder": true } },
      { "type": "epigraph", "attrs": { "placeholder": true } },
      { "type": "abstract", "attrs": { "lang": "pt", "placeholder": true } },
      { "type": "abstract", "attrs": { "lang": "en", "placeholder": true } },
      { "type": "listOfFigures", "attrs": { "placeholder": true } },
      { "type": "listOfTables", "attrs": { "placeholder": true } },
      { "type": "listOfAbbreviations", "attrs": { "placeholder": true } },
      { "type": "tableOfContents", "attrs": { "placeholder": true } },
      { "type": "heading", "attrs": { "level": 1, "text": "Introdução" } },
      { "type": "paragraph", "attrs": { "placeholder": "Escreva a introdução..." } },
      { "type": "heading", "attrs": { "level": 1, "text": "Desenvolvimento" } },
      { "type": "heading", "attrs": { "level": 2, "text": "Capítulo 1" } },
      { "type": "paragraph", "attrs": { "placeholder": "..." } },
      { "type": "heading", "attrs": { "level": 1, "text": "Considerações Finais" } },
      { "type": "paragraph", "attrs": { "placeholder": "..." } },
      { "type": "references", "attrs": { "placeholder": true } },
      { "type": "appendix", "attrs": { "placeholder": true } },
      { "type": "annex", "attrs": { "placeholder": true } }
    ]
  },
  "schema": {
    "nodes": ["coverPage", "titlePage", "approvalPage", "dedication", "acknowledgments", "epigraph", "abstract", "listOfFigures", "listOfTables", "listOfAbbreviations", "tableOfContents", "references", "appendix", "annex", "abntHeading", "shortQuote", "longQuote", "referenceEntry", "abntTable", "abntFigure"],
    "marks": ["bold", "italic", "underline", "strike", "code", "link", "abntCitation"]
  }
}
```

---

## 9. Fluxo de Import/Export

### Import .docx → TipTap
```
.docx (upload) 
  → FastAPI /import-docx 
    → python-docx parse 
    → classify.py detecta estrutura 
    → mapear para TipTap nodes (heading→abntHeading, table→abntTable, etc.)
    → retornar TipTap JSON
  → Next.js carrega no Editor
```

### Export TipTap → .docx
```
TipTap JSON (save)
  → FastAPI /export-docx
    → TipTap JSON → python-docx Document (via serializer)
    → adjust.adjust_docx() aplica formatação ABNT final
    → retornar .docx bytes
  → Download
```

### Export TipTap → PDF
```
TipTap JSON 
  → Next.js Server Action
    → render HTML via TipTap HTML serializer + print CSS (@page, @media print)
    → Playwright/Chromium headless → PDF
    → retornar PDF bytes
  → Download
```

---

## 10. Gerador de Referências

```python
# service/references.py
import httpx
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc.source.json import CiteProcJSON

async def crossref_fetch(doi: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.crossref.org/works/{doi}")
        return r.json()['message']

async def openlibrary_fetch(isbn: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://openlibrary.org/isbn/{isbn}.json")
        return r.json()

def csl_to_abnt(csl: dict) -> str:
    """Converte CSL-JSON para string ABNT usando citeproc-python + style ABNT"""
    style = CitationStylesStyle('abnt.csl')  # style file
    bibliography = CitationStylesBibliography(style, CiteProcJSON([csl]), formatter)
    # render
    return formatted_string
```

---

## 11. Auth Flow (NextAuth v5)

```typescript
// lib/auth.ts
import NextAuth from 'next-auth'
import GitHub from 'next-auth/providers/github'
import Google from 'next-auth/providers/google'
import Credentials from 'next-auth/providers/credentials'
import { PrismaAdapter } from '@auth/prisma-adapter'
import { prisma } from './prisma'
import bcrypt from 'bcryptjs'

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    GitHub({ clientId: env.GITHUB_ID, clientSecret: env.GITHUB_SECRET }),
    Google({ clientId: env.GOOGLE_ID, clientSecret: env.GOOGLE_SECRET }),
    Credentials({
      name: 'Email',
      credentials: { email: {}, password: {} },
      authorize: async (credentials) => {
        const user = await prisma.user.findUnique({ where: { email: credentials.email } })
        if (!user?.passwordHash) return null
        const valid = await bcrypt.compare(credentials.password, user.passwordHash)
        return valid ? user : null
      }
    })
  ],
  callbacks: {
    session: ({ session, user }) => ({ ...session, user: { ...session.user, id: user.id } })
  },
  pages: { signIn: '/auth/signin' }
})
```

---

## 12. UI/UX - Telas Principais

| Rota | Descrição | Componentes |
|---|---|---|
| `/` | Landing page | Hero, features, templates preview, CTA |
| `/dashboard` | Lista trabalhos | Table/Grid, filtros, novo trabalho, busca |
| `/editor/[id]` | Editor TipTap | Toolbar ABNT, sidebar (estrutura, referências, comentários), status bar |
| `/templates` | Galeria templates | Cards por categoria, preview, "Usar este" |
| `/references` | Gerenciador referências | Busca DOI/ISBN/URL, lista salva, exportar .bib |
| `/settings` | Perfil, conta, plano | Avatar, email, senha, conectar GitHub/Google |
| `/auth/signin` | Login/Registro | NextAuth pages, magic link |

**Editor Toolbar (ABNT-specific):**
```
[Fonte: TNR/Arial] [Tamanho: 12] | [B I U] | 
[Heading 1] [Heading 2] [Heading 3] [Sem numeração] |
[Citação curta] [Citação longa] [Referência] |
[Tabela] [Figura] [Equação] |
[Lista numerada] [Lista bullets] [Recuo] |
[Verificar ABNT] [Gerar PDF] [Exportar .docx]
```

---

## 13. Validação ABNT no Editor (Tempo Real)

```typescript
// hooks/useAbntValidation.ts
import { useEditor } from '@tiptap/react'
import { useEffect, useState } from 'react'

interface AbntIssue {
  type: 'error' | 'warning' | 'info'
  category: 'structure' | 'formatting' | 'citations' | 'references' | 'visual' | 'cover'
  message: string
  position?: { from: number, to: number }
  autoFixable: boolean
}

export function useAbntValidation(editor: Editor) {
  const [issues, setIssues] = useState<AbntIssue[]>([])
  
  useEffect(() => {
    const debounced = debounce(async () => {
      const json = editor.getJSON()
      const res = await fetch('/api/validate', {
        method: 'POST',
        body: JSON.stringify({ content: json })
      })
      const report = await res.json()
      setIssues(flattenReport(report))
    }, 1000)
    
    editor.on('transaction', debounced)
    return () => editor.off('transaction', debounced)
  }, [editor])
  
  return { issues, runValidation: () => debounced() }
}
```

---

## 14. Deploy & Environment

```bash
# .env.example
DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/db?sslmode=require"
NEXTAUTH_SECRET="generated-openssl-rand-base64-32"
NEXTAUTH_URL="http://localhost:3000"
GITHUB_ID=""
GITHUB_SECRET=""
GOOGLE_ID=""
GOOGLE_SECRET=""
VERCEL_BLOB_READ_WRITE_TOKEN=""
FASTAPI_URL="http://localhost:8000"  # local dev
# produção: FASTAPI_URL="https://abnt-service-xxx.vercel.app"
```

**Vercel Config:**
```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "prisma generate && next build",
  "devCommand": "next dev",
  "installCommand": "npm install",
  "regions": ["iad1"],
  "functions": {
    "app/api/**/*.ts": { "maxDuration": 30 }
  },
  "crons": [
    { "path": "/api/cron/cleanup-blobs", "schedule": "0 3 * * *" }
  ]
}
```

**Docker Compose (Local Dev):**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: abnt_editor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
  
  fastapi:
    build: ./service
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/abnt_editor"
    depends_on: ["postgres"]
    volumes: ["./service:/app", "./abnt:/app/abnt"]

  nextjs:
    build: .
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/abnt_editor"
      FASTAPI_URL: "http://fastapi:8000"
    depends_on: ["postgres", "fastapi"]
    volumes: [".:/app", "/app/node_modules", "/app/.next"]

volumes:
  pgdata:
```

---

## 15. Critérios de Aceite (MVP)

1. ✅ `docker compose up` sobe Next.js + FastAPI + Postgres
2. ✅ Login GitHub/Google/Email funciona
3. ✅ Dashboard lista/cria/exclui trabalhos
4. ✅ Editor carrega template TCC ABNT com placeholders
5. ✅ Toolbar ABNT: headings numerados, citações curta/longa, referências, tabelas/figuras numeradas
6. ✅ Validação tempo real mostra issues (margens, citações, referências, estrutura)
7. ✅ Import .docx → Editor preserva estrutura + formata
8. ✅ Export .docx → ABNT formatado (usa `abnt/adjust.py`)
9. ✅ Export PDF → visual fiel (print CSS + Playwright)
10. ✅ Gerador referências: DOI + ISBN → entrada ABNT salva + insere no editor
11. ✅ Deploy Vercel (Next.js) + Fluid Compute (FastAPI) + Neon Postgres
12. ✅ Testes: unit (extensions), integration (API), e2e (Playwright)

---

## 16. Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| TipTap + ProseMirror learning curve | Começar com `tiptap-starter-kit` + extensions oficiais; docs excelentes |
| PyMuPDF/Playwright no Vercel | FastAPI em Fluid Compute (Node.js + Python) ou Railway; PDF via `chromium` binary |
| Sincronização numeração (tabelas/figuras) | Plugin ProseMirror centralizado + persistir no JSON |
| Crossref/OpenAlex rate limits | Cache em Redis (Upstash) + fallback manual |
| Migração `abnt/` → service | Manter `abnt/` como lib; service é wrapper fino |
| Auth multi-tenant futuro | NextAuth + Prisma adapter suporta; adicionar `organizationId` depois |

---

## 17. Próximos Passos

1. **Spec aprovado** → invocar `writing-plans` para plano detalhado
2. **Setup repo**: `create-next-app` + `prisma init` + `fastapi` structure
3. **Fase 1**: Auth + Dashboard + Database
4. **Fase 2**: TipTap Editor + Core Extensions + Templates
5. **Fase 3**: FastAPI Service + Formatação/Validação
6. **Fase 4**: Import/Export + Referências
7. **Fase 5**: Polish, Testes, Deploy, README