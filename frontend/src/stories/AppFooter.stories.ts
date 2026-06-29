import type { Meta, StoryFn } from '@storybook/vue3'
import AppFooter from '@/components/AppFooter.vue'

export default {
  title: 'Components/AppFooter',
  component: AppFooter,
} as Meta

const Template: StoryFn = () => ({
  components: { AppFooter },
  template: '<AppFooter />',
})

export const Default = Template.bind({})
