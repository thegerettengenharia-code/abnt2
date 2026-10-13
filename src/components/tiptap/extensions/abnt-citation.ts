import { Node } from '@tiptap/core'

export const ShortQuote = Node.create({
  name: 'shortQuote',
  group: 'inline',
  content: 'inline*',
  inline: true,
  addAttributes() {
    return {
      author: { default: '' },
      year: { default: '' },
      page: { default: '' }
    }
  },
  parseHTML() {
    return [{ tag: 'span[data-short-quote]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['span', {
      'data-short-quote': '',
      'data-author': HTMLAttributes.author,
      'data-year': HTMLAttributes.year,
      'data-page': HTMLAttributes.page,
      class: 'abnt-short-quote'
    }, 0]
  }
})

export const LongQuote = Node.create({
  name: 'longQuote',
  group: 'block',
  content: 'inline*',
  addAttributes() {
    return {
      author: { default: '' },
      year: { default: '' },
      page: { default: '' }
    }
  },
  parseHTML() {
    return [{ tag: 'blockquote[data-long-quote]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['blockquote', {
      'data-long-quote': '',
      class: 'abnt-long-quote'
    }, 0]
  }
})