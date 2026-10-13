"use client"

import { useEffect, useState, useCallback } from "react"
import { Editor } from "@tiptap/react"

export interface AbntIssue {
  type: "error" | "warning" | "info"
  category: "structure" | "formatting" | "citations" | "references" | "visual" | "cover"
  message: string
  position?: { from: number; to: number }
  autoFixable: boolean
}

interface ValidationReport {
  estrutura?: { encontrados: string[]; faltando: string[]; ordem_incorreta: string[]; pendencias: string[] }
  citacoes?: { curtas_sem_aspas: string[]; longas_com_aspas: string[]; autor_formato: string[]; footnotes_ok: boolean; pendencias: string[] }
  referencias?: { fora_ordem: string[]; sem_entrelinha: boolean; sem_negrito_ano: boolean; sem_doi: string[]; citadas_nao_referenciadas: string[]; referenciadas_nao_citadas: string[]; autor_formato: string[]; pendencias: string[] }
  elementos_visuais?: { caption_posicao: string[]; numeracao_faltando: string[]; fonte_faltando: string[]; cross_ref_ordem: string[]; pendencias: string[] }
  capa?: { tem_capa: boolean; tem_folha_rosto: boolean; campos_faltando: string[]; divergencias: string[] }
  cross_check?: { orphans_citacoes: string[]; orphans_referencias: string[] }
}

export function useAbntValidation(editor: Editor | null) {
  const [issues, setIssues] = useState<AbntIssue[]>([])
  const [loading, setLoading] = useState(false)

  const runValidation = useCallback(async () => {
    if (!editor) return
    setLoading(true)
    try {
      const json = editor.getJSON()
      const res = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: json }),
      })
      if (res.ok) {
        const report: ValidationReport = await res.json()
        setIssues(flattenReport(report))
      }
    } catch (err) {
      console.error("Validation error:", err)
    } finally {
      setLoading(false)
    }
  }, [editor])

  useEffect(() => {
    if (!editor) return
    const debounced = setTimeout(() => runValidation(), 1000)
    const handleTransaction = () => {
      clearTimeout(debounced)
      setTimeout(runValidation, 1000)
    }
    editor.on("transaction", handleTransaction)
    return () => {
      editor.off("transaction", handleTransaction)
    }
  }, [editor, runValidation])

  return { issues, loading, runValidation }
}

function flattenReport(report: ValidationReport): AbntIssue[] {
  const issues: AbntIssue[] = []

  if (report.estrutura) {
    report.estrutura.faltando.forEach((msg) =>
      issues.push({ type: "error", category: "structure", message: `Elemento obrigatório ausente: ${msg}`, autoFixable: false })
    )
    report.estrutura.ordem_incorreta.forEach(([esperado, encontrado]) =>
      issues.push({ type: "warning", category: "structure", message: `Ordem incorreta: esperado "${esperado}", encontrado "${encontrado}"`, autoFixable: false })
    )
    report.estrutura.pendencias.forEach((msg) =>
      issues.push({ type: "info", category: "structure", message: msg, autoFixable: false })
    )
  }

  if (report.citacoes) {
    report.citacoes.curtas_sem_aspas.forEach((msg) =>
      issues.push({ type: "error", category: "citations", message: `Citação curta sem aspas: ${msg}`, autoFixable: true })
    )
    report.citacoes.longas_com_aspas.forEach((msg) =>
      issues.push({ type: "error", category: "citations", message: `Citação longa com aspas: ${msg}`, autoFixable: true })
    )
    report.citacoes.autor_formato.forEach((msg) =>
      issues.push({ type: "warning", category: "citations", message: msg, autoFixable: false })
    )
    report.citacoes.pendencias.forEach((msg) =>
      issues.push({ type: "info", category: "citations", message: msg, autoFixable: false })
    )
  }

  if (report.referencias) {
    report.referencias.fora_ordem.forEach((msg) =>
      issues.push({ type: "warning", category: "references", message: `Referência fora de ordem: ${msg}`, autoFixable: true })
    )
    if (report.referencias.sem_entrelinha)
      issues.push({ type: "error", category: "references", message: "Referências sem entrelinha pendente (1,25 cm)", autoFixable: true })
    if (report.referencias.sem_negrito_ano)
      issues.push({ type: "error", category: "references", message: "Anos das referências sem negrito", autoFixable: true })
    report.referencias.sem_doi.forEach((msg) =>
      issues.push({ type: "warning", category: "references", message: `Referência sem DOI: ${msg}`, autoFixable: false })
    )
    report.referencias.citadas_nao_referenciadas.forEach((msg) =>
      issues.push({ type: "error", category: "references", message: `Citada mas não referenciada: ${msg}`, autoFixable: false })
    )
    report.referencias.referenciadas_nao_citadas.forEach((msg) =>
      issues.push({ type: "warning", category: "references", message: `Referenciada mas não citada: ${msg}`, autoFixable: false })
    )
    report.referencias.autor_formato.forEach((msg) =>
      issues.push({ type: "warning", category: "references", message: msg, autoFixable: false })
    )
    report.referencias.pendencias.forEach((msg) =>
      issues.push({ type: "info", category: "references", message: msg, autoFixable: false })
    )
  }

  if (report.elementos_visuais) {
    report.elementos_visuais.caption_posicao.forEach((msg) =>
      issues.push({ type: "warning", category: "visual", message: msg, autoFixable: true })
    )
    report.elementos_visuais.numeracao_faltando.forEach((msg) =>
      issues.push({ type: "error", category: "visual", message: msg, autoFixable: true })
    )
    report.elementos_visuais.fonte_faltando.forEach((msg) =>
      issues.push({ type: "warning", category: "visual", message: msg, autoFixable: false })
    )
    report.elementos_visuais.cross_ref_ordem.forEach((msg) =>
      issues.push({ type: "warning", category: "visual", message: msg, autoFixable: false })
    )
    report.elementos_visuais.pendencias.forEach((msg) =>
      issues.push({ type: "info", category: "visual", message: msg, autoFixable: false })
    )
  }

  if (report.capa) {
    report.capa.campos_faltando.forEach((msg) =>
      issues.push({ type: "warning", category: "cover", message: `Capa: campo ausente: ${msg}`, autoFixable: true })
    )
    report.capa.divergencias.forEach((msg) =>
      issues.push({ type: "info", category: "cover", message: msg, autoFixable: false })
    )
  }

  if (report.cross_check) {
    report.cross_check.orphans_citacoes.forEach((msg) =>
      issues.push({ type: "error", category: "citations", message: `Citação sem referência: ${msg}`, autoFixable: false })
    )
    report.cross_check.orphans_referencias.forEach((msg) =>
      issues.push({ type: "warning", category: "references", message: `Referência sem citação: ${msg}`, autoFixable: false })
    )
  }

  return issues
}