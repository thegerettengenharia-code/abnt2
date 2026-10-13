import { Heading, HeadingOptions } from '@tiptap/extension-heading'

export const AbntHeading = Heading.extend<HeadingOptions>({
  name: 'abntHeading',
  addOptions() {
    return {
      levels: [1, 2, 3, 4],
      HTMLAttributes: {}
    }
  },
  addAttributes() {
    return {
      level: {
        default: 1,
        rendered: false
      },
      isUnnumbered: {
        default: false,
        parseHTML: element => element.hasAttribute('data-unnumbered'),
        renderHTML: attributes => {
          if (attributes.isUnnumbered) return { 'data-unnumbered': '' }
          return {}
        }
      }
    }
  }
})