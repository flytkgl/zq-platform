<script setup lang="ts">
import { computed, ref, watch, watchEffect } from 'vue';

import { Grip, IconifyIcon, listIcons } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElEmpty, ElInput, ElPagination, ElScrollbar } from 'element-plus';

import { ZqDialog } from '#/components/zq-dialog';

import { fetchIconsData } from './icons';

interface Props {
  pageSize?: number;
  /** 图标集的名字 */
  prefix?: string;
  /** 是否自动请求API以获得图标集的数据.提供prefix时有效 */
  autoFetchApi?: boolean;
  /** 图标列表 */
  icons?: string[];
  /** 图标样式 */
  iconClass?: string;
  /** 弹窗标题 */
  dialogTitle?: string;
  /** 弹窗宽度 */
  dialogWidth?: number | string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 占位符 */
  placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
  prefix: 'ant-design',
  pageSize: 54,
  icons: () => [],
  iconClass: 'size-4',
  autoFetchApi: true,
  dialogTitle: undefined,
  dialogWidth: '600px',
  disabled: false,
  placeholder: undefined,
});

const emit = defineEmits<{
  change: [string];
}>();

const modelValue = defineModel({ default: '', type: String });

const dialogVisible = ref(false);
const currentSelect = ref('');
const currentPage = ref(1);
const keyword = ref('');
const innerIcons = ref<string[]>([]);
const searchKeyword = ref('');

let searchTimer: null | ReturnType<typeof setTimeout> = null;

watch(searchKeyword, (val) => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    keyword.value = val;
    currentPage.value = 1;
  }, 300);
});

watch(
  () => props.prefix,
  async (prefix) => {
    if (prefix && prefix !== 'svg' && props.autoFetchApi) {
      innerIcons.value = await fetchIconsData(prefix);
    }
  },
  { immediate: true },
);

const currentList = computed(() => {
  try {
    if (props.icons.length > 0) {
      return props.icons;
    }
    if (props.prefix) {
      if (props.prefix !== 'svg' && props.autoFetchApi) {
        return innerIcons.value;
      }
      return listIcons('', props.prefix);
    }
    return props.icons;
  } catch {
    return [];
  }
});

const filteredList = computed(() => {
  if (!keyword.value) return currentList.value;
  return currentList.value.filter((item) => item.includes(keyword.value));
});

const total = computed(() => filteredList.value.length);

const paginationList = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize;
  return filteredList.value.slice(start, start + props.pageSize);
});

watchEffect(() => {
  currentSelect.value = modelValue.value;
});

watch(
  () => currentSelect.value,
  (v) => {
    emit('change', v);
  },
);

function openDialog() {
  if (props.disabled) return;
  dialogVisible.value = true;
}

function handleClick(icon: string) {
  currentSelect.value = icon;
}

function handleConfirm() {
  modelValue.value = currentSelect.value;
  dialogVisible.value = false;
}

function handleDialogOpen() {
  currentSelect.value = modelValue.value;
  keyword.value = '';
  searchKeyword.value = '';
  currentPage.value = 1;
}

function handlePageChange(page: number) {
  currentPage.value = page;
}

const computedTitle = computed(
  () => props.dialogTitle ?? $t('ui.iconPicker.placeholder'),
);

defineExpose({ openDialog });
</script>

<template>
  <div class="zq-icon-picker" :class="{ 'is-disabled': disabled }">
    <!-- 触发器：带图标预览的输入框 -->
    <div class="zq-icon-picker-trigger" @click="openDialog">
      <ElInput
        :model-value="currentSelect"
        :placeholder="placeholder ?? $t('ui.iconPicker.placeholder')"
        :disabled="disabled"
        readonly
        class="zq-icon-picker-el-input"
      >
        <template #prefix>
          <IconifyIcon
            v-if="currentSelect"
            :icon="currentSelect"
            class="h-4 w-4"
          />
          <component
            :is="Grip"
            v-else
            class="h-4 w-4 text-[var(--el-text-color-placeholder)]"
          />
        </template>
      </ElInput>
    </div>

    <!-- 弹窗 -->
    <ZqDialog
      v-model="dialogVisible"
      :title="computedTitle"
      :width="dialogWidth"
      :show-footer="true"
      :confirm-text="$t('common.confirm')"
      :cancel-text="$t('common.cancel')"
      :destroy-on-close="false"
      :show-fullscreen-button="false"
      @opened="handleDialogOpen"
      @confirm="handleConfirm"
    >
      <div class="zq-icon-picker-dialog-content">
        <!-- 搜索栏 -->
        <div class="zq-icon-picker-search">
          <ElInput
            v-model="searchKeyword"
            :placeholder="$t('ui.iconPicker.search')"
            clearable
            class="w-full"
          />
        </div>

        <!-- 图标网格 -->
        <template v-if="paginationList.length > 0">
          <ElScrollbar class="zq-icon-picker-scrollbar">
            <div class="zq-icon-picker-grid">
              <button
                v-for="(item, index) in paginationList"
                :key="index"
                class="zq-icon-picker-grid-item"
                :class="{ 'is-active': currentSelect === item }"
                :title="item"
                type="button"
                @click="handleClick(item)"
              >
                <IconifyIcon :icon="item" class="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </ElScrollbar>

          <!-- 分页 -->
          <div v-if="total > pageSize" class="zq-icon-picker-pagination">
            <ElPagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              small
              @current-change="handlePageChange"
            />
          </div>
        </template>

        <!-- 空状态 -->
        <template v-else>
          <ElEmpty :description="$t('common.noData')" class="py-8" />
        </template>
      </div>
    </ZqDialog>
  </div>
</template>

<style lang="scss" scoped>
.zq-icon-picker {
  width: 100%;

  &.is-disabled {
    cursor: not-allowed;
    opacity: 0.6;

    .zq-icon-picker-trigger {
      pointer-events: none;
    }
  }

  &-trigger {
    width: 100%;
    cursor: pointer;
  }

  &-el-input {
    :deep(.el-input__wrapper) {
      cursor: pointer;
    }

    :deep(.el-input__inner) {
      cursor: pointer;
    }
  }

  &-dialog-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &-search {
    padding: 0 2px;
  }

  &-scrollbar {
    max-height: 360px;
  }

  &-grid {
    display: grid;
    grid-template-columns: repeat(9, 1fr);
    gap: 4px;
    padding: 4px 2px;
  }

  &-grid-item {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    aspect-ratio: 1;
    padding: 8px;
    cursor: pointer;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    transition: all 0.15s ease;
    color: var(--el-text-color-regular);

    &:hover {
      background-color: var(--el-fill-color-light);
      color: var(--el-color-primary);
      border-color: var(--el-color-primary-light-7);
    }

    &.is-active {
      background-color: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      border-color: var(--el-color-primary-light-5);
    }
  }

  &-pagination {
    display: flex;
    justify-content: center;
    padding-top: 4px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}
</style>
