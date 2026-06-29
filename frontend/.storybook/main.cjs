const { mergeConfig } = require('vite')
const vue = require('@vitejs/plugin-vue')
const { resolve } = require('path')

module.exports = {
  stories: ['../src/**/*.stories.@(ts|vue)'],
  addons: ['@storybook/addon-essentials'],
  framework: {
    name: '@storybook/vue3-vite',
    options: {},
  },
  async viteFinal(config) {
    return mergeConfig(config, {
      plugins: [vue()],
      resolve: {
        alias: {
          '@': resolve(__dirname, '../src'),
        },
      },
    })
  },
}
