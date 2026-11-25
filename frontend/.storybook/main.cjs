const { mergeConfig } = require('vite')
const { resolve } = require('path')

module.exports = {
  stories: ['../src/**/*.stories.@(ts|vue)'],
  framework: {
    name: '@storybook/vue3-vite',
    options: {},
  },
  async viteFinal(config) {
    return mergeConfig(config, {
      resolve: {
        alias: {
          '@': resolve(__dirname, '../src'),
        },
      },
    })
  },
}
