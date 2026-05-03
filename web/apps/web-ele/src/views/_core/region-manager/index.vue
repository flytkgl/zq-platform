<script setup lang="ts">
import type { CardListItem, CardListOptions } from '#/components/card-list';

import { ref } from 'vue';

import { Page } from '@vben/common-ui';

import { CardList } from '#/components/card-list';

import AreaManager from './modules/area-manager.vue';
import CityManager from './modules/city-manager.vue';
import ProvinceManager from './modules/province-manager.vue';
import StreetManager from './modules/street-manager.vue';
import VillageManager from './modules/village-manager.vue';

defineOptions({
  name: 'RegionManager',
});

// 菜单项类型
interface RegionMenuItem extends CardListItem {
  id: string;
  name: string;
  key: 'area' | 'city' | 'province' | 'street' | 'village';
}

// 菜单项数据
const menuItems = ref<RegionMenuItem[]>([
  {
    id: 'province',
    name: '省份管理',
    key: 'province',
  },
  {
    id: 'city',
    name: '城市管理',
    key: 'city',
  },
  {
    id: 'area',
    name: '区县管理',
    key: 'area',
  },
  {
    id: 'street',
    name: '街道管理',
    key: 'street',
  },
  {
    id: 'village',
    name: '村庄管理',
    key: 'village',
  },
]);

const selectedMenuId = ref<string>('province');

// CardList 配置
const cardListOptions: CardListOptions<RegionMenuItem> = {
  searchFields: [{ field: 'name' }],
  titleField: 'name',
  displayMode: 'center',
};

/**
 * 处理菜单选择
 */
function handleMenuSelect(id: string | undefined) {
  selectedMenuId.value = id || 'province';
}
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 左侧菜单 -->
      <div class="w-48">
        <CardList
          :items="menuItems"
          :selected-id="selectedMenuId"
          :options="cardListOptions"
          :loading="false"
          class="region-menu"
          @select="handleMenuSelect"
        >
          <template #item="{ item }">
            <div class="text-sm font-medium">{{ item.name }}</div>
          </template>
        </CardList>
      </div>

      <!-- 右侧内容 -->
      <div class="flex-1">
        <!-- 省份管理 -->
        <template v-if="selectedMenuId === 'province'">
          <ProvinceManager />
        </template>

        <!-- 城市管理 -->
        <template v-else-if="selectedMenuId === 'city'">
          <CityManager />
        </template>

        <!-- 区县管理 -->
        <template v-else-if="selectedMenuId === 'area'">
          <AreaManager />
        </template>

        <!-- 街道管理 -->
        <template v-else-if="selectedMenuId === 'street'">
          <StreetManager />
        </template>

        <!-- 村庄管理 -->
        <template v-else-if="selectedMenuId === 'village'">
          <VillageManager />
        </template>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.region-menu :deep(.el-card__body) {
  padding: 16px;
}

/* 隐藏搜索和添加按钮 */
.region-menu :deep(.mb-4.flex) {
  display: none;
}
</style>
