"use client"

import { AbntIssue } from "@/hooks/useAbntValidation"

interface ValidationPanelProps {
  issues: AbntIssue[]
  onRunValidation: () => void
}

const categoryLabels: Record<string, string> = {
  structure: "Estrutura (NBR 14724)",
  formatting: "Formatação Geral",
  citations: "Citações (NBR 10520)",
  references: "Referências (NBR 6023)",
  visual: "Elementos Visuais (NBR 6022)",
  cover: "Capa/Folha de Rosto",
}

const categoryColors: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  error: { bg: "bg-red-50", border: "border-red-200", text: "text-red-800", dot: "bg-red-500" },
  warning: { bg: "bg-yellow-50", border: "border-yellow-200", text: "text-yellow-800", dot: "bg-yellow-500" },
  info: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-800", dot: "bg-blue-500" },
}

export function ValidationPanel({ issues, onRunValidation }: ValidationPanelProps) {
  const grouped = issues.reduce((acc, issue) => {
    if (!acc[issue.category]) acc[issue.category] = []
    acc[issue.category].push(issue)
    return acc
  }, {} as Record<string, AbntIssue[]>)

  const categories = Object.keys(grouped).sort()

  if (issues.length === 0) {
    return (
      <aside className="w-80 border-l border-gray-200 bg-gray-50 p-4 overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Validação ABNT</h3>
          <button onClick={onRunValidation} className="text-xs text-blue-600 hover:text-blue-800">Revalidar</button>
        </div>
        <div className="text-center py-8 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="mt-2">Tudo certo! Nenhum problema detectado.</p>
        </div>
      </aside>
    )
  }

  return (
    <aside className="w-80 border-l border-gray-200 bg-gray-50 p-4 overflow-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Validação ABNT</h3>
        <button onClick={onRunValidation} disabled={issues.length === 0} className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50">
          Revalidar
        </button>
      </div>

      <div className="space-y-4">
        {categories.map((cat) => {
          const catIssues = grouped[cat]
          const errorCount = catIssues.filter((i) => i.type === "error").length
          const warningCount = catIssues.filter((i) => i.type === "warning").length
          const infoCount = catIssues.filter((i) => i.type === "info").length

          return (
            <details key={cat} className="group" open>
              <summary className="flex items-center justify-between cursor-pointer select-none p-2 rounded-lg hover:bg-gray-100">
                <span className="font-medium text-gray-900">{categoryLabels[cat] || cat}</span>
                <div className="flex items-center gap-2">
                  {errorCount > 0 && <span className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded-full">{errorCount}</span>}
                  {warningCount > 0 && <span className="bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded-full">{warningCount}</span>}
                  {infoCount > 0 && <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">{infoCount}</span>}
                </div>
              </summary>
              <div className="mt-2 space-y-2 pl-4 border-l border-gray-200">
                {catIssues.map((issue, idx) => {
                  const colors = categoryColors[issue.type]
                  return (
                    <div key={idx} className={`${colors.bg} ${colors.border} border rounded-lg p-3`}>
                      <div className="flex items-start gap-2">
                        <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${colors.dot}`} />
                        <div className="flex-1 min-w-0">
                          <p className={`${colors.text} text-sm`}>{issue.message}</p>
                          {issue.autoFixable && (
                            <button className="mt-1 text-xs text-blue-600 hover:text-blue-800 underline">
                              Aplicar correção automática
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </details>
          )
        })}
      </div>
    </aside>
  )
}