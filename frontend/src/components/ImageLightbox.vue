<script setup lang="ts">
import { ref, watch } from 'vue'
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

const visible = ref(false)
const currentIndex = ref(0)
const images = ref<string[]>([])
const loaded = ref(false)

function open(srcs: string[], index = 0) {
  images.value = srcs
  currentIndex.value = index
  loaded.value = false
  visible.value = true
}

function close() {
  visible.value = false
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    loaded.value = false
  }
}

function next() {
  if (currentIndex.value < images.value.length - 1) {
    currentIndex.value++
    loaded.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (!visible.value) return
  if (e.key === 'Escape') close()
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
}

function onBgClick(e: MouseEvent) {
  if ((e.target as HTMLElement).id === 'lightbox-bg') close()
}

watch(visible, (v) => {
  if (v) {
    document.addEventListener('keydown', onKeydown)
    document.body.style.overflow = 'hidden'
  } else {
    document.removeEventListener('keydown', onKeydown)
    document.body.style.overflow = ''
  }
})

defineExpose({ open })
</script>

<template>
  <Teleport to="body">
    <Transition name="lightbox">
      <div
        v-if="visible"
        id="lightbox-bg"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
        @click="onBgClick"
      >
        <!-- Close button -->
        <button
          @click="close"
          aria-label="Закрыть"
          class="absolute top-4 right-4 z-10 w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          <XMarkIcon class="w-6 h-6" />
        </button>

        <!-- Counter -->
        <div v-if="images.length > 1" class="absolute top-4 left-4 z-10 px-3 py-1.5 rounded-full bg-white/10 text-white text-sm font-medium">
          {{ currentIndex + 1 }} / {{ images.length }}
        </div>

        <!-- Prev -->
        <button
          v-if="images.length > 1 && currentIndex > 0"
          @click="prev"
          aria-label="Предыдущее фото"
          class="absolute left-4 top-1/2 -translate-y-1/2 z-10 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          <ChevronLeftIcon class="w-7 h-7" />
        </button>

        <!-- Next -->
        <button
          v-if="images.length > 1 && currentIndex < images.length - 1"
          @click="next"
          aria-label="Следующее фото"
          class="absolute right-4 top-1/2 -translate-y-1/2 z-10 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          <ChevronRightIcon class="w-7 h-7" />
        </button>

        <!-- Image -->
        <div class="max-w-[90vw] max-h-[90vh] flex items-center justify-center p-4">
          <Transition name="fade" mode="out-in">
            <img
              :key="currentIndex"
              :src="images[currentIndex]"
              class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl select-none"
              :class="{ 'opacity-0': !loaded }"
              @load="loaded = true"
              @click.stop
              alt=""
            />
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.25s ease;
}
.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
