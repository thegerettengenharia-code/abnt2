import { Node } from '@tiptap/core'

export const ReferenceEntry = Node.create({
  name: 'referenceEntry',
  group: 'block',
  content: 'inline*',
  addAttributes() {
    return {
      referenceId: { default: '' },
      type: { default: 'book' },
      authors: { default: [] },
      year: { default: '' },
      title: { default: '' },
      doi: { default: '' }
    }
  },
  parseHTML() {
    return [{ tag: 'p[data-reference-entry]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['p', {
      'data-reference-entry': '',
      'data-reference-id': HTMLAttributes.referenceId,
      class: 'abnt-reference-entry'
    }, 0]
  }
})