import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import Link from "next/link"

const templates = [
  {
    id: "tcc-abnt",
    name: "TCC ABNT",
    category: "TCC",
    description: "Trabalho de Conclusão de Curso completo com todos os elementos pré-textuais, textuais e pós-textuais (NBR 14724).",
  },
  {
    id: "artigo-cientifico",
    name: "Artigo Científico",
    category: "ARTICLE",
    description: "Artigo para publicação em periódicos científicos. Estrutura IMRaD com referências ABNT.",
  },
  {
    id: "projeto-pesquisa",
    name: "Projeto de Pesquisa",
    category: "PROJECT",
    description: "Projeto de pesquisa acadêmica com introdução, fundamentação teórica, metodologia, cronograma.",
  },
  {
    id: "relatorio-estagio",
    name: "Relatório de Estágio",
    category: "REPORT",
    description: "Relatório de estágio supervisionado com descrição de atividades, análise e conclusões.",
  },
  {
    id: "fichamento",
    name: "Fichamento",
    category: "FICHAMENTO",
    description: "Fichamento direto, indireto ou de citações para organização de leituras acadêmicas.",
  },
]

export default async function TemplatesPage() {
  const session = await auth()
  if (!session?.user) redirect("/auth/signin")

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <Link href="/" className="text-xl font-bold text-blue-600">Editor ABNT</Link>
              <Link href="/dashboard" className="text-sm font-medium text-gray-700 hover:text-blue-600">Meus Trabalhos</Link>
              <Link href="/templates" className="text-sm font-medium text-blue-600">Templates</Link>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{session.user.name || session.user.email}</span>
              <form action="/api/auth/signout" method="POST">
                <button type="submit" className="text-sm text-gray-600 hover:text-gray-900">Sair</button>
              </form>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900">Templates Oficiais ABNT</h1>
          <p className="mt-2 text-gray-600">
            Escolha um template para começar seu trabalho com a estrutura correta já montada.
            Todos os templates seguem a NBR 14724 e normas correlatas.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <article key={template.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                  {template.category}
                </span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{template.name}</h3>
              <p className="text-gray-600 mb-4">{template.description}</p>
              <Link
                href={`/editor/new?template=${template.id}`}
                className="inline-flex items-center gap-1 text-blue-600 font-medium hover:text-blue-700"
              >
                Usar este template
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </Link>
            </article>
          ))}
        </div>

        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-xl p-8">
          <h3 className="text-xl font-semibold text-blue-900 mb-2">Precisa de outro tipo de documento?</h3>
          <p className="mt-2 text-blue-800">
            Templates para PIM, Tese, Dissertação, Resenha Crítica e outros estão disponíveis na biblioteca completa.
            <Link href="#" className="ml-1 font-medium underline hover:text-blue-700">Ver todos</Link>
          </p>
        </div>
      </main>
    </div>
  )
}