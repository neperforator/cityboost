<template>
  <footer class="mt-auto border-t-2 border-line bg-surface px-5 py-5 dark:border-line-dark dark:bg-surface-dark">
    <div class="mx-auto flex max-w-5xl flex-col gap-2 text-xs text-ink-soft dark:text-ink-dark-soft sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-2">
        <span class="h-2 w-2 rounded-full bg-accent-500" />
        <span class="font-semibold text-ink dark:text-ink-dark">CityBoost</span>
        <span>городская служба заявок</span>
      </div>
      <p>© {{ new Date().getFullYear() }} CityBoost. <br /> Все права защищены.</p>
    </div>
  </footer>
</template>
