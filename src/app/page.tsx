import Link from "next/link"
import { auth } from "@/lib/auth"

export default async function HomePage() {
  const session = await auth()

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold text-blue-600">
                Editor ABNT
              </Link>
            </div>
            <div className="flex items-center gap-4">
              {session ? (
                <>
                  <Link href="/dashboard" className="text-sm font-medium text-gray-700 hover:text-blue-600">
                    Dashboard
                  </Link>
                  <Link href="/templates" className="text-sm font-medium text-gray-700 hover:text-blue-600">
                    Templates
                  </Link>
                </>
              ) : (
                <>
                  <Link href="/auth/signin" className="text-sm font-medium text-gray-700 hover:text-blue-600">
                    Entrar
                  </Link>
                  <Link href="/auth/signin" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
                    Começar Grátis
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-900 tracking-tight">
            Formatação ABNT Automática
            <br />
            <span className="text-blue-600">para seus Trabalhos Acadêmicos</span>
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto">
            Editor WYSIWYG open source com formatação ABNT em tempo real, templates prontos,
            gerador de referências e exportação para PDF e DOCX.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            {!session ? (
              <>
                <Link
                  href="/auth/signin"
                  className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  Começar Grátis
                </Link>
                <Link
                  href="/templates"
                  className="border-2 border-gray-300 text-gray-700 px-8 py-3 rounded-lg text-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Ver Templates
                </Link>
              </>
            ) : (
              <Link
                href="/dashboard"
                className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Ir para o Dashboard
              </Link>
            )}
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            title="Editor WYSIWYG"
            description="Escreva naturalmente com formatação ABNT aplicada em tempo real. Headings numerados, citações, referências, tabelas e figuras formatados automaticamente."
          />
          <FeatureCard
            title="Templates Oficiais"
            description="TCC, Artigo Científico, Projeto de Pesquisa, Relatório de Estágio, Fichamento e mais. Estrutura NBR 14724 completa com placeholders."
          />
          <FeatureCard
            title="Gerador de Referências"
            description="Insira DOI, ISBN ou URL e gere a referência ABNT (NBR 6023:2018) automaticamente. Crossref, OpenLibrary e OpenAlex integrados."
          />
        </div>

        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            title="Import/Export"
            description="Importe seu .docx existente e formate em segundos. Exporte para PDF (pronto para impressão) ou .docx com formatação ABNT perfeita."
          />
          <FeatureCard
            title="Validação em Tempo Real"
            description="Verificador ABNT rodando enquanto você escreve: margens, citações, referências, estrutura NBR 14724, numeração de figuras/tabelas."
          />
          <FeatureCard
            title="Open Source"
            description="Código 100% aberto (MIT). Deploy no Vercel, Railway ou self-hosted. Sem vendor lock-in. Comunidade bem-vinda para contribuir."
          />
        </div>

        <div className="mt-20 text-center">
          <p className="text-gray-600">
            Usado por estudantes, pesquisadores e professores em universidades de todo o Brasil.
          </p>
          <div className="mt-4 flex items-center justify-center gap-8 text-sm text-gray-500">
            <span>MIT License</span>
            <span>•</span>
            <span>TypeScript + Next.js 14</span>
            <span>•</span>
            <span>TipTap + ProseMirror</span>
            <span>•</span>
            <span>PostgreSQL + Prisma</span>
          </div>
        </div>
      </div>

      <footer className="mt-20 border-t py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
          <p>Editor ABNT Online - Open Source</p>
          <p className="mt-1">
            <a href="https://github.com" className="hover:text-blue-600" target="_blank" rel="noopener">
              GitHub
            </a>
            {" • "}
            <a href="/docs" className="hover:text-blue-600">
              Documentação
            </a>
            {" • "}
            <a href="/contribuir" className="hover:text-blue-600">
              Contribuir
            </a>
          </p>
        </div>
      </footer>
    </main>
  )
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}