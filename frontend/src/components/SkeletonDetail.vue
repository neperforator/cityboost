<template>
  <div class="mx-auto max-w-3xl">
    <div class="skeleton mb-6 h-4 w-24" />
    <div class="panel mb-6 space-y-4 p-6">
      <div class="flex justify-between gap-4">
        <div class="flex-1 space-y-3">
          <div class="skeleton h-7 w-3/4" />
          <div class="skeleton h-4 w-1/3" />
        </div>
        <div class="skeleton h-7 w-24 shrink-0" />
      </div>
      <div class="skeleton mt-4 h-4 w-1/4" />
      <div class="space-y-2">
        <div class="skeleton h-3 w-full" />
        <div class="skeleton h-3 w-full" />
        <div class="skeleton h-3 w-2/3" />
      </div>
    </div>
    <div class="panel p-6">
      <div class="skeleton mb-4 h-5 w-32" />
      <div v-for="i in 2" :key="i" class="mb-3 flex gap-3 rounded-sm bg-surface-muted p-4 dark:bg-surface-dark-muted">
        <div class="skeleton h-9 w-9 shrink-0 rounded-full" />
        <div class="flex-1 space-y-2">
          <div class="skeleton h-3 w-32" />
          <div class="skeleton h-3 w-full" />
          <div class="skeleton h-3 w-4/5" />
        </div>
      </div>
    </div>
  </div>
</template>
