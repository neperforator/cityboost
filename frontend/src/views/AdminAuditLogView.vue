<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { adminAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { useUsers } from '@/composables/useUsers'
import Pagination from '@/components/Pagination.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'

import { ClockIcon, FunnelIcon } from '@heroicons/vue/24/outline'
import { NoSymbolIcon, CheckBadgeIcon, ShieldCheckIcon, ArrowPathIcon, WrenchScrewdriverIcon } from '@heroicons/vue/24/solid'

const toast = useToast()
const { getUserDisplay } = useUsers()

const logs = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const page = ref(1)
const pageSize = 30
const actionFilter = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const actions = [
  { value: '', label: 'Все действия', icon: FunnelIcon },
  { value: 'ban', label: 'Блокировка', icon: NoSymbolIcon },
  { value: 'unban', label: 'Разблокировка', icon: CheckBadgeIcon },
  { value: 'change_role', label: 'Смена роли', icon: ShieldCheckIcon },
  { value: 'change_ticket_status', label: 'Статус заявки', icon: ArrowPathIcon },
  { value: 'assign_ticket', label: 'Назначение', icon: WrenchScrewdriverIcon },
]

const actionLabels: Record<string, string> = {
  ban: 'Блокировка',
  unban: 'Разблокировка',
  change_role: 'Смена роли',
  change_ticket_status: 'Смена статуса заявки',
  assign_ticket: 'Назначение заявки',
}

async function loadLogs() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (actionFilter.value) params.action = actionFilter.value
    const data = await adminAPI.getAuditLogs(params)
    logs.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    loading.value = false
  }
}

function setFilter(action: string) {
  actionFilter.value = action
  page.value = 1
  loadLogs()
}

function goPage(p: number) {
  page.value = p
  loadLogs()
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '…' : s
}

onMounted(() => {
  loadLogs()
})
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
    <header class="border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">Администрирование</p>
      <h1 class="mt-2 font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">Аудит-лог</h1>
      <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">Всего записей: {{ total }}</p>
    </header>

    <div class="mt-6 overflow-x-auto scrollbar-none">
      <div class="flex min-w-max items-stretch border-2 border-line dark:border-line-dark">
        <button
          v-for="a in actions"
          :key="a.value"
          @click="setFilter(a.value)"
          class="flex items-center gap-1.5 border-r-2 border-line px-3 py-2.5 text-sm font-medium transition-colors last:border-r-0 dark:border-line-dark"
          :class="actionFilter === a.value
            ? 'bg-primary-500 text-white'
            : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
        >
          <component :is="a.icon" class="h-3.5 w-3.5" />
          {{ a.label }}
        </button>
      </div>
    </div>

    <Transition name="page" mode="out-in">
      <div v-if="loading" key="loading" class="panel mt-5 overflow-hidden">
        <SkeletonTable :rows="8" :columns="5" />
      </div>

      <div v-else-if="logs.length === 0" key="empty" class="panel mt-5 p-10 text-center">
        <ClockIcon class="mx-auto h-8 w-8 text-ink-soft dark:text-ink-dark-soft" />
        <p class="mt-3 text-sm text-ink-soft dark:text-ink-dark-soft">Нет записей аудит-лога</p>
      </div>

      <div v-else key="table" class="mt-5">
        <div class="panel overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b-2 border-line bg-surface-muted dark:border-line-dark dark:bg-surface-dark-muted">
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Дата</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Действие</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Администратор</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Цель</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Детали</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in logs" :key="log.id" class="border-b-2 border-line transition-colors last:border-b-0 hover:bg-surface-muted dark:border-line-dark dark:hover:bg-surface-dark-muted">
                  <td class="whitespace-nowrap px-4 py-3.5 text-xs text-ink-soft dark:text-ink-dark-soft">{{ formatDate(log.created_at) }}</td>
                  <td class="px-4 py-3.5">
                    <span class="font-medium text-ink dark:text-ink-dark">{{ actionLabels[log.action] || log.action }}</span>
                  </td>
                  <td class="px-4 py-3.5 text-ink-soft dark:text-ink-dark-soft">{{ log.admin_name || getUserDisplay(log.admin_id) }}</td>
                  <td class="px-4 py-3.5 text-xs">
                    <template v-if="log.target_type === 'user'">
                      <span class="font-medium text-ink dark:text-ink-dark">{{ log.target_name || getUserDisplay(log.target_id) }}</span>
                    </template>
                    <template v-else-if="log.target_type === 'ticket'">
                      <router-link :to="`/admin/tickets/${log.target_id}`" class="font-medium text-primary-700 hover:underline dark:text-primary-300">
                        {{ log.target_name ? `Заявка «${truncate(log.target_name, 40)}»` : 'Заявка' }}
                      </router-link>
                    </template>
                    <span v-else class="text-ink-soft dark:text-ink-dark-soft">{{ log.target_type }}</span>
                  </td>
                  <td class="max-w-xs truncate px-4 py-3.5 text-xs text-ink-soft dark:text-ink-dark-soft">{{ log.details || '—' }}</td>
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
          @change="goPage"
        />
      </div>
    </Transition>
  </div>
</template>
