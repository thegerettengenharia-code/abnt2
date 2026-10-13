# Roadmap - Editor ABNT Online

## Versão 1.0 (MVP) - ✅ Em desenvolvimento

**Objetivo**: Editor funcional com formatação ABNT básica, templates, import/export, referências.

| Feature | Status |
|---------|--------|
| Next.js 14 + TipTap Editor | ✅ |
| Extensões ABNT (headings, citações, referências, tabelas, figuras) | ✅ |
| Autenticação (GitHub, Google, Email) | ✅ |
| Dashboard de trabalhos | ✅ |
| Templates oficiais (TCC, Artigo, Projeto, Relatório, Fichamento) | ✅ |
| Validação ABNT tempo real | ✅ |
| Import .docx → Editor | ✅ |
| Export .docx + PDF | ✅ |
| Gerador referências (DOI, ISBN, URL) | ✅ |
| Deploy Vercel + FastAPI | ✅ |
| Testes E2E (Playwright) | ✅ |
| Documentação + README | ✅ |

---

## Versão 1.1 (Q1 2027) - Qualidade de Vida

**Objetivo**: Polimento, performance, acessibilidade.

| Feature | Descrição |
|---------|-----------|
| **Modo Escuro** | Toggle dark/light mode persistido |
| **Atalhos de Teclado** | Ctrl+B, Ctrl+I, Ctrl+1/2/3, etc. |
| **Auto-save** | Salvamento automático a cada 30s + indicador visual |
| **Histórico de Versões** | UI para ver/restaurar versões anteriores (WorkVersion) |
| **Busca no Editor** | Ctrl+F com highlight + replace |
| **Contagem de Palavras/Caracteres** | Status bar com contagem em tempo real |
| **Melhor Acessibilidade** | ARIA labels, navegação por teclado, screen readers |
| **Performance** | Lazy loading de extensões, virtualização de documentos grandes |
| **PWA** | Installable, offline-first com Service Workers |

---

## Versão 1.2 (Q2 2027) - Colaboração

**Objetivo**: Trabalho em equipe, orientação, revisão.

| Feature | Descrição |
|---------|-----------|
| **Comentários Inline** | Selecionar texto → adicionar comentário (thread) |
| **Modo Sugestão** | Track changes estilo Google Docs/Word |
| **Compartilhamento** | Link público/privado com permissões (ver, comentar, editar) |
| **Notificações** | Email + in-app para comentários, menções, aprovações |
| **Papéis** | Autor, Orientador, Coorientador, Revisor, Leitor |
| **Fluxo de Aprovação** | Autor → Orientador → Banca → Publicado |
| **Convites** | Email + link mágico para colaboradores |
| **Presença em Tempo Real** | Avatares de quem está editando (cursor awareness) |

---

## Versão 2.0 (Q3-Q4 2027) - Inteligência Artificial

**Objetivo**: IA integrada para escrita, pesquisa, formatação.

| Feature | Descrição |
|---------|-----------|
| **Gerador de Tema** | "Me dê 5 temas para TCC sobre IA na educação" → lista com referências |
| **Gerador de Resumo/Abstract** | Selecionar texto → gerar resumo ABNT (≤250 palavras) |
| **Seleção de Citações** | "Encontre citações sobre X" → busca Crossref/OpenAlex → insere formatado |
| **Assistente de Escrita** | "Reescreva este parágrafo em linguagem acadêmica" |
| **Verificador de Plágio** | Integração com Turnitin/Copyleaks (opcional, API paga) |
| **Tradução de Resumo** | PT → EN (Abstract) automático com terminologia técnica |
| **Sugestão de Referências** | Baseado no texto escrito, sugere papers relevantes |
| **Corretor Gramatical PT-BR** | LanguageTool ou similar integrado |

---

## Versão 2.1 (2028) - Ecossistema Acadêmico

**Objetivo**: Integração com ferramentas existentes.

| Feature | Descrição |
|---------|-----------|
| **Export Overleaf/LaTeX** | .tex pronto para compilar no Overleaf |
| **Import Zotero/Mendeley** | Sincronizar biblioteca de referências |
| **Export BibTeX/RIS** | Para uso em outros gerenciadores |
| **Integração Google Scholar** | Buscar citações direto do Scholar |
| **API Pública** | Webhooks, OAuth para integrações terceiras |
| **Marketplace de Templates** | Comunidade compartilha templates institucionais |

---

## Versão 3.0 (2029+) - Plataforma Completa

**Objetivo**: Hub acadêmico completo.

| Feature | Descrição |
|---------|-----------|
| **Hub de Publicação** | Submeter artigos para periódicos parceiros |
| **Perfil Acadêmico** | ORCID, publicações, métricas, redes |
| **Gestão de Projetos** | Cronograma, tarefas, marcos, entregáveis |
| **Biblioteca Pessoal** | PDFs anotados, highlights, notas |
| **Cursos/Trilhas** | "Como fazer TCC", "Escrita Acadêmica", "Estatística" |
| **Comunidade** | Fóruns, dúvidas, mentoria entre pares |

---

## Priorização Técnica (Dívida Técnica)

| Item | Prioridade | Esforço |
|------|------------|---------|
| Testes de carga (k6) | Alta | Médio |
| CI/CD completo (GitHub Actions) | Alta | Baixo |
| Monitoring (Sentry, Vercel Analytics) | Alta | Baixo |
| Rate limiting API | Média | Baixo |
| Cache Redis (Upstash) para referências | Média | Médio |
| Migração para React Server Components completos | Baixa | Alto |
| Edge Functions para auth | Baixa | Médio |

---

## Métricas de Sucesso

| Métrica | Target v1.0 | Target v1.2 | Target v2.0 |
|---------|-------------|-------------|-------------|
| Usuários ativos mensais | 1.000 | 10.000 | 100.000 |
| Trabalhos criados/mês | 500 | 5.000 | 50.000 |
| Taxa de conversão (visitante → trial) | 5% | 8% | 12% |
| NPS | > 40 | > 50 | > 60 |
| Tempo médio formatação/doc | < 2 min | < 1 min | < 30s |
| Taxa de erro formatação | < 2% | < 1% | < 0.5% |

---

## Contribuindo com o Roadmap

Tem ideias? Abra uma **Discussion** no GitHub com a tag `roadmap` ou `feature-request`. A comunidade vota e os maintainers priorizam.

---

*Última atualização: 2026-10-12*