# Guia de Contribuição

Obrigado por querer contribuir com o Editor ABNT Online! 🎓

## 🚀 Como Contribuir

### 1. Reportar Bugs

- Use o template de **Bug Report** no GitHub Issues
- Inclua: versão do Node.js, OS, passos para reproduzir, screenshots
- Verifique se o bug já não foi reportado

### 2. Sugerir Funcionalidades

- Use o template de **Feature Request**
- Descreva o problema que resolve e o caso de uso
- Considere se é dentro do escopo ABNT (NBR 14724, 6023, 10520, 6022)

### 3. Pull Requests

1. Fork o repositório
2. Crie uma branch: `git checkout -b feat/nova-funcionalidade` ou `fix/correcao-bug`
3. Faça suas alterações com commits atômicos
4. Execute os testes: `npm test && npx playwright test`
5. Push e abra o PR

## 📋 Padrões de Código

### Commits (Conventional Commits)

```
feat: adiciona validação de citações longas
fix: corrige numeração de figuras ao mover
docs: atualiza README com deploy no Railway
refactor: extrai hook useAbntValidation
test: adiciona testes para gerador de referências
```

### TypeScript

- Strict mode ativado
- Tipos explícitos para props de componentes
- Interfaces para props de componentes React
- Evite `any` — use `unknown` ou tipos específicos

### React/Next.js

- Componentes funcionais com hooks
- Server Components por padrão, Client Components apenas quando necessário (`"use client"`)
- Server Actions para mutações
- Suspense para loading states

### Python (FastAPI Service)

- Type hints obrigatórios
- Pydantic models para request/response
- Async/await para I/O
- Docstrings no formato Google/NumPy

## 🧪 Testes

### Unitários (Jest/Vitest)

```bash
npm run test
```

### E2E (Playwright)

```bash
npx playwright test
```

### FastAPI (pytest)

```bash
cd service && pytest -v
```

### Cobertura Mínima

- Novos componentes: ≥ 80%
- Novos hooks: ≥ 90%
- Novos endpoints API: ≥ 70%

## 🎨 ABNT - Regras de Formatação

Ao implementar formatação, consulte as normas oficiais:

| Norma | Descrição |
|-------|-----------|
| NBR 14724 | Estrutura e apresentação de trabalhos acadêmicos |
| NBR 6023 | Referências bibliográficas |
| NBR 10520 | Citações em documentos |
| NBR 6022 | Apresentação de tabelas e figuras |
| NBR 6027 | Sumários |
| NBR 6028 | Resumos |

**Princípio fundamental**: O editor **apenas formata** elementos detectados — **não adiciona nem remove conteúdo**.

## 📦 Estrutura de Branches

| Branch | Propósito |
|--------|-----------|
| `main` | Produção (protegida) |
| `develop` | Integração contínua |
| `feat/*` | Novas funcionalidades |
| `fix/*` | Correções de bugs |
| `docs/*` | Documentação |
| `refactor/*` | Refatorações |

## 🔍 Code Review Checklist

- [ ] Tipos TypeScript corretos
- [ ] Testes passam
- [ ] Lint passa (`npm run lint`)
- [ ] Build passa (`npm run build`)
- [ ] Documentação atualizada (se necessário)
- [ ] Commits seguem conventional commits
- [ ] Sem `console.log` ou código de debug
- [ ] Acessibilidade (ARIA labels, contraste, foco)

## 🐛 Debugging

### Frontend

```bash
# Logs do Next.js
npm run dev

# Debug no VS Code (launch.json)
{
  "type": "nextjs",
  "request": "launch",
  "name": "Next.js Debug"
}
```

### FastAPI

```bash
cd service
uvicorn main:app --reload --port 8000

# Logs
tail -f logs/fastapi.log
```

### Banco de Dados

```bash
# Prisma Studio
npx prisma studio

# Migrations
npx prisma migrate dev
npx prisma migrate deploy
```

## 📞 Dúvidas?

- Abra uma **Discussion** no GitHub
- Marque como `question`
- A comunidade e maintainers responderão

---

Obrigado por ajudar a tornar a formatação ABNT acessível a todos! 🇧🇷