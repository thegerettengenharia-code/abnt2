import { Node } from '@tiptap/core'
import { Table, TableRow, TableCell, TableHeader } from '@tiptap/extension-table'

export const AbntTable = Table.extend({
  name: 'abntTable',
  addAttributes() {
    return {
      ...this.parent?.(),
      number: { default: 0 },
      title: { default: '' },
      source: { default: '' }
    }
  }
})

export const AbntTableRow = TableRow
export const AbntTableCell = TableCell
export const AbntTableHeader = TableHeader

export const AbntFigure = Node.create({
  name: 'abntFigure',
  group: 'block',
  content: '(image caption?)',
  addAttributes() {
    return {
      number: { default: 0 },
      title: { default: '' },
      source: { default: '' },
      type: { default: 'figure' }
    }
  },
  parseHTML() {
    return [{ tag: 'figure[data-abnt-figure]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['figure', {
      'data-abnt-figure': '',
      class: 'abnt-figure'
    }, 0]
  }
})