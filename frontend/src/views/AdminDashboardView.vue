<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { adminAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { useUsers } from '@/composables/useUsers'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'
import Pagination from '@/components/Pagination.vue'
import { ShieldCheckIcon, InboxStackIcon, NewspaperIcon, WrenchScrewdriverIcon, CheckBadgeIcon } from '@heroicons/vue/24/outline'

const PAGE_SIZE = 15

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()
const { getUserDisplay } = useUsers()

const tickets = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const statusFilter = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

// Global stats from server
const stats = ref({
  total: 0,
  new: 0,
  in_work: 0,
  done: 0,
  closed: 0,
})

const statCards = computed(() => [
  { key: '', label: 'Всего', count: stats.value.total, icon: InboxStackIcon, color: 'text-primary-600 dark:text-primary-400', ring: 'ring-primary-500' },
  { key: 'NEW', label: 'Новые', count: stats.value.new, icon: NewspaperIcon, color: 'text-blue-600 dark:text-blue-400', ring: 'ring-blue-500' },
  { key: 'IN_WORK', label: 'В работе', count: stats.value.in_work, icon: WrenchScrewdriverIcon, color: 'text-amber-600 dark:text-amber-400', ring: 'ring-amber-500' },
  { key: 'DONE', label: 'Выполнены', count: stats.value.done, icon: CheckBadgeIcon, color: 'text-emerald-600 dark:text-emerald-400', ring: 'ring-emerald-500' },
])

async function loadStats() {
  try {
    stats.value = await adminAPI.getStats()
  } catch {
    // fallback
  }
}

async function loadTickets() {
  loading.value = true
  try {
    const data = await adminAPI.listTickets({
      page: page.value,
      page_size: PAGE_SIZE,
      status: statusFilter.value || undefined,
    })
    tickets.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    loading.value = false
  }
}

function onPageChange(newPage: number) {
  page.value = newPage
  loadTickets()
}

function setFilter(status: string) {
  statusFilter.value = status
  page.value = 1
  loadTickets()
}

function viewTicket(id: string) {
  router.push(`/admin/tickets/${id}`)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  loadStats()
  loadTickets()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
    <!-- Page header -->
    <div class="page-header">
      <h1 class="page-title flex items-center gap-2">
        <ShieldCheckIcon class="w-7 h-7 text-primary-600 dark:text-primary-400" />
        Админ-панель
      </h1>
      <p class="page-subtitle">Управление заявками</p>
    </div>

    <!-- Stats (global) -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
      <button
        v-for="s in statCards"
        :key="s.key"
        @click="setFilter(s.key)"
        class="stat-card hover:shadow-md transition-shadow cursor-pointer"
        :class="statusFilter === s.key ? `ring-2 ${s.ring}` : ''"
      >
        <div class="stat-icon bg-primary-50 dark:bg-primary-900/30">
          <component :is="s.icon" class="w-6 h-6" :class="s.color" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ s.count }}</p>
          <p class="stat-label">{{ s.label }}</p>
        </div>
      </button>
    </div>

    <!-- Content with transition -->
    <Transition name="page" mode="out-in">
      <!-- Loading skeleton -->
      <div v-if="loading" key="loading" class="card overflow-hidden">
        <SkeletonTable :rows="6" :columns="6" />
      </div>

      <!-- Empty state -->
      <div v-else-if="tickets.length === 0" key="empty" class="card p-12 text-center">
        <div class="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
          <InboxStackIcon class="w-8 h-8 text-gray-400" />
        </div>
        <p class="text-gray-500 dark:text-gray-400 mb-4">Нет заявок с выбранным статусом</p>
        <button @click="setFilter('')" class="btn-secondary">Показать все</button>
      </div>

      <!-- Table -->
      <div v-else key="table">
        <div class="card overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                  <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Заголовок</th>
                  <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Пользователь</th>
                  <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Статус</th>
                  <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Дата</th>
                  <th class="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Действия</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                <tr v-for="t in tickets" :key="t.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors cursor-pointer" @click="viewTicket(t.id)">
                  <td class="px-4 py-3 font-medium text-gray-900 dark:text-white max-w-xs truncate">{{ t.title }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{{ t.user_name || getUserDisplay(t.user_id) }}</td>
                  <td class="px-4 py-3"><StatusBadge :status="t.status" /></td>
                  <td class="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">{{ formatDate(t.created_at) }}</td>
                  <td class="px-4 py-3 text-right">
                    <button @click.stop="viewTicket(t.id)" class="btn-primary btn-sm">Детали</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <Pagination
          v-if="totalPages > 1"
          :page="page"
          :total-pages="totalPages"
          :total="total"
          @change="onPageChange"
        />
      </div>
    </Transition>
  </div>
</template>
