import type { Meta, StoryFn } from '@storybook/vue3'
import StatusBadge from '@/components/StatusBadge.vue'

export default {
  title: 'Components/StatusBadge',
  component: StatusBadge,
  argTypes: {
    status: {
      control: 'select',
      options: ['NEW', 'IN_WORK', 'DONE', 'CLOSED'],
    },
    size: {
      control: 'select',
      options: ['normal', 'lg'],
    },
  },
} as Meta

const Template: StoryFn = (args) => ({
  components: { StatusBadge },
  setup: () => ({ args }),
  template: '<StatusBadge v-bind="args" />',
})

export const New = Template.bind({})
New.args = { status: 'NEW' }

export const InWork = Template.bind({})
InWork.args = { status: 'IN_WORK' }

export const Done = Template.bind({})
Done.args = { status: 'DONE' }

export const Closed = Template.bind({})
Closed.args = { status: 'CLOSED' }

export const Large = Template.bind({})
Large.args = { status: 'NEW', size: 'lg' }
