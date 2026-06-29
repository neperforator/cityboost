import type { Meta, StoryFn } from '@storybook/vue3'
import ToastContainer from '@/components/ToastContainer.vue'
import { useToast } from '@/composables/useToast'

export default {
  title: 'Components/ToastContainer',
  component: ToastContainer,
} as Meta

const Template: StoryFn = () => ({
  components: { ToastContainer },
  setup() {
    const toast = useToast()
    return { toast }
  },
  template: `
    <div class="min-h-[200px]">
      <ToastContainer />
      <div class="flex gap-2 p-4">
        <button @click="toast.success('Заявка создана!')" class="px-3 py-2 rounded bg-emerald-500 text-white text-sm">Success</button>
        <button @click="toast.error('Ошибка загрузки')" class="px-3 py-2 rounded bg-red-500 text-white text-sm">Error</button>
        <button @click="toast.info('Новое уведомление')" class="px-3 py-2 rounded bg-indigo-500 text-white text-sm">Info</button>
        <button @click="toast.warning('Внимание!')" class="px-3 py-2 rounded bg-amber-500 text-white text-sm">Warning</button>
      </div>
    </div>
  `,
})

export const Default = Template.bind({})
