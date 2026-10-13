import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"

export default async function DashboardPage() {
  const session = await auth()
  if (!session?.user) redirect("/auth/signin")

  const works = await prisma.work.findMany({
    where: { userId: session.user.id },
    include: { template: true, _count: { select: { versions: true } } },
    orderBy: { updatedAt: "desc" },
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <Link href="/" className="text-xl font-bold text-blue-600">Editor ABNT</Link>
              <Link href="/dashboard" className="text-sm font-medium text-blue-600">Meus Trabalhos</Link>
              <Link href="/templates" className="text-sm font-medium text-gray-700 hover:text-blue-600">Templates</Link>
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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Meus Trabalhos</h1>
          <Link
            href="/editor/new"
            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Novo Trabalho
          </Link>
        </div>

        {works.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 13l-7 7-7-7m14-8l-7 7-7-7" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">Nenhum trabalho ainda</h3>
            <p className="mt-2 text-gray-500">Comece criando seu primeiro trabalho a partir de um template.</p>
            <Link
              href="/templates"
              className="mt-6 inline-block bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700"
            >
              Escolher Template
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {works.map((work) => (
              <article key={work.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 truncate">{work.title}</h3>
                    <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
                      <span className="capitalize">{work.status.toLowerCase().replace("_", " ")}</span>
                      {work.template && (
                        <>
                          <span>•</span>
                          <span className="text-blue-600">{work.template.name}</span>
                        </>
                      )}
                      <span>•</span>
                      <span>{work.updatedAt.toLocaleDateString("pt-BR")}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <Link
                    href={`/editor/${work.id}`}
                    className="flex-1 bg-blue-600 text-white text-center py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700"
                  >
                    Editar
                  </Link>
                  <Link
                    href={`/editor/${work.id}/export`}
                    className="flex-1 border border-gray-300 text-gray-700 text-center py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-50"
                  >
                    Exportar
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}