import { Extension } from '@tiptap/core'

export const AbntCore = Extension.create({
  name: 'abntCore',
  addGlobalAttributes() {
    return [{
      types: ['paragraph', 'heading', 'textStyle'],
      attributes: {
        abntRole: {
          default: 'body',
          parseHTML: element => element.getAttribute('data-abnt-role') || 'body',
          renderHTML: attributes => ({
            'data-abnt-role': attributes.abntRole
          })
        }
      }
    }]
  }
})