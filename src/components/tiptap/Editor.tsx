"use client"

import { useEditor, EditorContent } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import { AbntCore } from "@/components/tiptap/extensions/abnt-core"
import { AbntHeading } from "@/components/tiptap/extensions/abnt-heading"
import { ShortQuote, LongQuote } from "@/components/tiptap/extensions/abnt-citation"
import { ReferenceEntry } from "@/components/tiptap/extensions/abnt-reference"
import { AbntTable, AbntFigure } from "@/components/tiptap/extensions/abnt-figure-table"
import { Toolbar } from "@/components/tiptap/Toolbar"
import { ValidationPanel } from "@/components/tiptap/validation/ValidationPanel"
import { useAbntValidation } from "@/hooks/useAbntValidation"

interface EditorProps {
  initialContent: any
  onSave: (content: any) => void
  workId?: string
}

export function Editor({ initialContent, onSave, workId }: EditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: false }),
      AbntCore,
      AbntHeading,
      ShortQuote,
      LongQuote,
      ReferenceEntry,
      AbntTable,
      AbntFigure,
    ],
    content: initialContent,
    editorProps: {
      attributes: {
        class: "prose prose-gray max-w-none focus:outline-none min-h-[600px] p-8 bg-white",
      },
    },
    onUpdate: ({ editor }) => {
      onSave(editor.getJSON())
    },
  })

  const { issues, runValidation } = useAbntValidation(editor)

  if (!editor) return <div>Carregando editor...</div>

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <Toolbar editor={editor} />
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-auto">
          <EditorContent editor={editor} />
        </div>
        <ValidationPanel issues={issues} onRunValidation={runValidation} />
      </div>
    </div>
  )
}