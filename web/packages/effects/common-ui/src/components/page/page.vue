<script setup lang="ts">
import type { StyleValue } from 'vue';

import type { PageProps } from './types';

import { computed, nextTick, onMounted, ref, useTemplateRef } from 'vue';

import { CSS_VARIABLE_LAYOUT_CONTENT_HEIGHT } from '@vben-core/shared/constants';
import { cn } from '@vben-core/shared/utils';

defineOptions({
  name: 'Page',
});

const { autoContentHeight = false, heightOffset = 24, showMargin = true } =
  defineProps<PageProps>();

const headerHeight = ref(0);
const footerHeight = ref(0);
const shouldAutoHeight = ref(false);

const headerRef = useTemplateRef<HTMLDivElement>('headerRef');
const footerRef = useTemplateRef<HTMLDivElement>('footerRef');

const contentStyle = computed<StyleValue>(() => {
  if (autoContentHeight) {
    return {
      height: `calc(var(${CSS_VARIABLE_LAYOUT_CONTENT_HEIGHT}) - ${headerHeight.value}px - ${footerHeight.value}px - ${typeof heightOffset === 'number' ? `${heightOffset}px` : heightOffset})`,
      overflowY: shouldAutoHeight.value ? 'auto' : 'unset',
    };
  }
  return {};
});

async function calcContentHeight() {
  if (!autoContentHeight) {
    return;
  }
  await nextTick();
  headerHeight.value = headerRef.value?.offsetHeight || 0;
  footerHeight.value = footerRef.value?.offsetHeight + 24 || 0;
  setTimeout(() => {
    shouldAutoHeight.value = true;
  }, 30);
}

onMounted(() => {
  calcContentHeight();
});
</script>

<template>
  <div :class="cn('relative flex min-h-full flex-col', showMargin && 'mx-3 mt-3')">
    <div
      v-if="
        description ||
        $slots.description ||
        title ||
        $slots.title ||
        $slots.extra
      "
      ref="headerRef"
      :class="
        cn(
          'bg-card relative mb-3 flex items-end rounded-[8px] px-6 py-3',
          headerClass,
        )
      "
    >
      <div class="flex-auto">
        <slot name="title">
          <div v-if="title" class="mb-2 flex text-lg font-semibold">
            {{ title }}
          </div>
        </slot>

        <slot name="description">
          <p v-if="description" class="text-muted-foreground">
            {{ description }}
          </p>
        </slot>
      </div>

      <div v-if="$slots.extra">
        <slot name="extra"></slot>
      </div>
    </div>

    <div :class="cn('h-full page-content-scroll', contentClass)" :style="contentStyle" class="rounded-[8px]">
      <slot></slot>
    </div>
    <div
      v-if="$slots.footer"
      ref="footerRef"
      :class="
        cn(
          'bg-card align-center my-3 flex rounded-[8px] px-6 py-3',
          footerClass,
        )
      "
    >
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<style scoped>
/* 参考 el-scrollbar 的滚动条样式 - 鼠标悬停时才显示 */
.page-content-scroll {
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}

.page-content-scroll:hover {
  scrollbar-color: var(--el-scrollbar-bg-color, rgba(144, 147, 153, 0.3)) transparent;
}

.page-content-scroll::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.page-content-scroll::-webkit-scrollbar-thumb {
  background-color: transparent;
  border-radius: 10px;
  transition: background-color 0.3s;
}

.page-content-scroll:hover::-webkit-scrollbar-thumb {
  background-color: var(--el-scrollbar-bg-color, rgba(144, 147, 153, 0.3));
}

.page-content-scroll::-webkit-scrollbar-thumb:hover {
  background-color: var(--el-scrollbar-hover-bg-color, rgba(144, 147, 153, 0.5));
}

.page-content-scroll::-webkit-scrollbar-track {
  background-color: transparent;
  border-radius: 10px;
}
</style>
