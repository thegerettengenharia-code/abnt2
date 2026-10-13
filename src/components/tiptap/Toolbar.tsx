"use client"

import { Editor } from "@tiptap/react"

interface ToolbarProps {
  editor: Editor | null
}

export function Toolbar({ editor }: ToolbarProps) {
  if (!editor) return null

  const addHeading = (level: 1 | 2 | 3) => {
    editor.chain().focus().toggleHeading({ level }).run()
  }

  const addUnnumberedHeading = (level: 1 | 2 | 3) => {
    editor.chain().focus().toggleHeading({ level }).run()
    // Add unnumbered attribute via transaction
    const { state, dispatch } = editor.view
    const { selection } = state
    const tr = state.tr
    tr.setNodeMarkup(selection.$from.pos, undefined, { ...selection.$from.node().attrs, isUnnumbered: true })
    dispatch(tr)
  }

  const insertShortQuote = () => {
    editor.chain().focus().insertContent({
      type: "shortQuote",
      attrs: { author: "", year: "", page: "" },
      content: [{ type: "text", text: '"Citação curta (AUTOR, 2023)"' }],
    }).run()
  }

  const insertLongQuote = () => {
    editor.chain().focus().insertContent({
      type: "longQuote",
      attrs: { author: "", year: "", page: "" },
      content: [{ type: "paragraph", content: [{ type: "text", text: "Citação longa com mais de 3 linhas..." }] }],
    }).run()
  }

  const insertReference = () => {
    editor.chain().focus().insertContent({
      type: "referenceEntry",
      attrs: { referenceId: "", type: "book", authors: [], year: "", title: "", doi: "" },
      content: [{ type: "text", text: "Referência bibliográfica (ano em negrito)..." }],
    }).run()
  }

  const insertTable = () => {
    editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  }

  const insertFigure = () => {
    editor.chain().focus().insertContent({
      type: "abntFigure",
      attrs: { number: 0, title: "", source: "", type: "figure" },
      content: [
        { type: "image", attrs: { src: "/placeholder.svg", alt: "Figura" } },
        { type: "paragraph", attrs: { abntRole: "caption" }, content: [{ type: "text", text: "Figura 1 – Título da figura" }] },
        { type: "paragraph", attrs: { abntRole: "source" }, content: [{ type: "text", text: "Fonte: ..." }] },
      ],
    }).run()
  }

  return (
    <div className="border-b border-gray-200 bg-white p-3 flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1 border-r border-gray-200 pr-3 mr-3">
        <select
          defaultValue="Times New Roman"
          onChange={(e) => console.log("Font family:", e.target.value)}
          className="px-2 py-1 text-sm border border-gray-300 rounded"
        >
          <option value="Times New Roman">Times New Roman</option>
          <option value="Arial">Arial</option>
        </select>
        <select
          defaultValue={12}
          onChange={(e) => console.log("Font size:", e.target.value)}
          className="px-2 py-1 text-sm border border-gray-300 rounded ml-1"
        >
          <option value={10}>10</option>
          <option value={11}>11</option>
          <option value={12}>12</option>
          <option value={14}>14</option>
        </select>
      </div>

      <div className="flex items-center gap-1 border-r border-gray-200 pr-3 mr-3">
        <button onClick={() => editor.chain().focus().toggleBold().run()} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"><strong>B</strong></button>
        <button onClick={() => editor.chain().focus().toggleItalic().run()} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"><em>I</em></button>
        <button onClick={() => editor.chain().focus().toggleStrike().run()} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"><s>S</s></button>
      </div>

      <div className="flex items-center gap-1 border-r border-gray-200 pr-3 mr-3">
        <button onClick={() => addHeading(1)} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100">H1</button>
        <button onClick={() => addHeading(2)} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100">H2</button>
        <button onClick={() => addHeading(3)} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100">H3</button>
        <button onClick={() => addUnnumberedHeading(1)} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 text-blue-600" title="Sem numeração">H1⁰</button>
      </div>

      <div className="flex items-center gap-1 border-r border-gray-200 pr-3 mr-3">
        <button onClick={insertShortQuote} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100" title="Citação curta (≤3 linhas)">"</button>
        <button onClick={insertLongQuote} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100" title="Citação longa (>3 linhas)">≡</button>
        <button onClick={insertReference} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100" title="Referência bibliográfica">[1]</button>
      </div>

      <div className="flex items-center gap-1 border-r border-gray-200 pr-3 mr-3">
        <button onClick={insertTable} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100" title="Inserir tabela">📊</button>
        <button onClick={insertFigure} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100" title="Inserir figura/quadro">🖼</button>
      </div>

      <div className="flex items-center gap-1 border-r border-gray-200 pr-3 mr-3">
        <button onClick={() => editor.chain().focus().toggleBulletList().run()} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100">•</button>
        <button onClick={() => editor.chain().focus().toggleOrderedList().run()} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100">1.</button>
        <button onClick={() => editor.chain().focus().liftListItem("listItem").run()} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100" title="Diminuir recuo">⌥</button>
        <button onClick={() => editor.chain().focus().sinkListItem("listItem").run()} className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100" title="Aumentar recuo">⌥</button>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Salvar
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50"
        >
          Validar ABNT
        </button>
      </div>
    </div>
  )
}