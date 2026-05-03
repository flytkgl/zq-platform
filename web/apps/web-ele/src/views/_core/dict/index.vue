<script lang="ts" setup>
import { ref } from 'vue';

import { FuPage } from '#/components/fu-page';

import DictItemList from './modules/dict-item-list.vue';
import DictList from './modules/dict-list.vue';

defineOptions({ name: 'SystemDict' });

const currentDictId = ref<string>();

/**
 * 字典选择事件
 */
function onDictSelect(dictId: string | undefined) {
  currentDictId.value = dictId;
}
</script>

<template>
  <FuPage
    auto-content-height
    :left-padding="false"
    :right-padding="false"
    :left-width="250"
  >
    <template #left>
      <div class="h-full px-4 py-4">
        <DictList @select="onDictSelect" />
      </div>
    </template>
    <template #right>
      <div class="h-full px-2 py-2">
        <DictItemList :dict-id="currentDictId" />
      </div>
    </template>
  </FuPage>
</template>
