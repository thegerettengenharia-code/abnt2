# Editor ABNT Online

Editor WYSIWYG open source para trabalhos acadêmicos com formatação ABNT automática, templates prontos, gerador de referências e exportação para PDF/DOCX.

## 🚀 Funcionalidades

- **Editor WYSIWYG** com TipTap + ProseMirror
- **Formatação ABNT em tempo real** (NBR 14724, 6023, 10520, 6022)
- **Templates oficiais**: TCC, Artigo, Projeto, Relatório, Fichamento
- **Gerador de referências**: DOI, ISBN, URL → ABNT (Crossref, OpenLibrary, OpenAlex)
- **Import/Export**: .docx → Editor → .docx/PDF
- **Validação em tempo real** com relatório detalhado
- **Autenticação**: GitHub, Google, Email (NextAuth.js)
- **Open Source** (MIT) — deploy no Vercel, Railway ou self-hosted

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        VERCEL                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 NEXT.JS 14 (APP ROUTER)             │   │
│  │  Dashboard │ Editor │ Templates │ Auth │ API Routes │   │
│  └────────────────────────────┬────────────────────────┘   │
│                               │ HTTP (internal)             │
└───────────────────────────────┼─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  FASTAPI SERVICE (Fluid Compute/Railway)    │
│  /format  |  /validate  |  /references  |  /import-docx    │
│  /export-docx  |  /export-pdf                                    │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL (Neon / Vercel Postgres)            │
│  Works, Templates, References, Users, Comments              │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Stack Tecnológico

| Camada | Tecnologia |
|--------|------------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| Editor | TipTap 2.x + ProseMirror |
| Backend API | Next.js API Routes + Server Actions |
| Formatação ABNT | FastAPI + Python (reutiliza `abnt/`) |
| Banco de Dados | PostgreSQL (Neon serverless) + Prisma ORM |
| Auth | NextAuth.js v5 (GitHub, Google, Email) |
| Deploy | Vercel (Next.js) + Vercel Fluid Compute (FastAPI) |

## 🚀 Início Rápido

### Pré-requisitos

- Node.js 20+
- Docker & Docker Compose
- PostgreSQL (ou usar Neon)

### Desenvolvimento Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/editor-abnt-online.git
cd editor-abnt-online

# Suba os containers (PostgreSQL + FastAPI + Next.js)
docker compose up -d

# Instale dependências do Next.js
npm install

# Configure variáveis de ambiente
cp .env.example .env.local
# Edite .env.local com suas credenciais

# Rode as migrations do Prisma
npx prisma migrate dev --name init

# Inicie o servidor de desenvolvimento
npm run dev
```

Acesse:
- **Next.js**: http://localhost:3000
- **FastAPI Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (user: postgres, pass: postgres, db: abnt_editor)

### Variáveis de Ambiente

```env
# .env.local
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/abnt_editor"
NEXTAUTH_SECRET="sua-chave-secreta-aqui"
NEXTAUTH_URL="http://localhost:3000"
GITHUB_ID="seu-github-client-id"
GITHUB_SECRET="seu-github-client-secret"
GOOGLE_ID="seu-google-client-id"
GOOGLE_SECRET="seu-google-client-secret"
FASTAPI_URL="http://localhost:8000"
```

## 📦 Deploy no Vercel

### 1. Configure o projeto no Vercel

1. Importe o repositório no Vercel
2. Configure as variáveis de ambiente:
   - `DATABASE_URL` (Neon/PostgreSQL)
   - `NEXTAUTH_SECRET` (gere com `openssl rand -base64 32`)
   - `NEXTAUTH_URL` (sua URL do Vercel)
   - `GITHUB_ID`, `GITHUB_SECRET`
   - `GOOGLE_ID`, `GOOGLE_SECRET`
   - `FASTAPI_URL` (URL do serviço FastAPI no Fluid Compute)

### 2. Deploy do FastAPI (Vercel Fluid Compute)

O FastAPI roda como uma Serverless Function no Vercel:

```json
// vercel.json (na raiz do projeto)
{
  "framework": "nextjs",
  "functions": {
    "service/main.py": {
      "maxDuration": 30,
      "runtime": "python3.12"
    }
  }
}
```

Ou use Railway/Render para o FastAPI se preferir mais controle.

## 📁 Estrutura do Projeto

```
.
├── prisma/
│   └── schema.prisma          # Schema do banco de dados
├── src/
│   ├── app/                   # Next.js App Router
│   │   ├── api/               # API Routes
│   │   ├── auth/              # Páginas de auth
│   │   ├── dashboard/         # Dashboard do usuário
│   │   ├── editor/            # Editor TipTap
│   │   ├── templates/         # Galeria de templates
│   │   └── page.tsx           # Landing page
│   ├── components/
│   │   ├── tiptap/            # Editor TipTap + extensões ABNT
│   │   └── ...
│   ├── hooks/                 # React hooks (useAbntValidation)
│   └── lib/                   # Utilitários (auth, prisma, service)
├── service/                   # FastAPI Service (Python)
│   ├── main.py                # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── abnt/                      # Módulos Python originais (reutilizados)
│   ├── adjust.py
│   ├── classify.py
│   ├── config.py
│   └── pdf_docx.py
├── docker-compose.yml
├── docker-compose.prod.yml
├── next.config.cjs
├── tailwind.config.js
├── prisma/schema.prisma
└── package.json
```

## 🧪 Testes

```bash
# Testes unitários
npm run test

# Testes E2E (Playwright)
npx playwright test

# Testes do FastAPI
cd service && pytest
```

## 📝 Extensões ABNT do TipTap

O editor inclui extensões customizadas para formatação ABNT:

| Extensão | Node/Mark | Descrição |
|----------|-----------|-----------|
| `abntHeading` | Node | Headings numerados (1, 2, 3) + sem numeração |
| `shortQuote` | Node | Citação curta (≤3 linhas) com aspas |
| `longQuote` | Node | Citação longa (>3 linhas) com recuo 4cm |
| `referenceEntry` | Node | Entrada bibliográfica com ano em negrito |
| `abntTable` | Node | Tabela com legenda acima, numeração sequencial |
| `abntFigure` | Node | Figura/quadro com legenda abaixo, numeração |

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'feat: adiciona nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

### Padrões de Código

- TypeScript estrito
- ESLint + Prettier
- Commits convencionais (feat, fix, docs, refactor, test)
- Testes para novas funcionalidades

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [TipTap](https://tiptap.dev/) - Editor headless incrível
- [NextAuth.js](https://next-auth.js.org/) - Autenticação simples e poderosa
- [Prisma](https://www.prisma.io/) - ORM type-safe
- [FastAPI](https://fastapi.tiangolo.com/) - API Python moderna
- Comunidade ABNT brasileira

---

Feito com ❤️ para a comunidade acadêmica brasileira.