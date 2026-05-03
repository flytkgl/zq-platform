<script lang="ts" setup>
import type {
  ApiSelectOption,
  ZqApiSelectEmits,
  ZqApiSelectProps,
} from './types';

import { computed, onMounted, ref, useAttrs, watch } from 'vue';

import { Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElEmpty,
  ElInput,
  ElOption,
  ElSelect,
  ElSkeleton,
  ElSkeletonItem,
  ElTag,
} from 'element-plus';

import { ZqDialog } from '#/components/zq-dialog';

defineOptions({
  name: 'ZqApiSelect',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  placeholder: () => $t('ui.placeholder.select') || 'Please select',
  disabled: false,
  clearable: true,
  filterable: true,
  valueField: 'id',
  labelField: 'name',
  extraField: undefined,
  dialogTitle: () => $t('ui.placeholder.select') || 'Please select',
  dialogWidth: '45%',
  pageSize: 20,
});

const emit = defineEmits<ZqApiSelectEmits>();

interface Props extends ZqApiSelectProps {}

const attrs = useAttrs();

const modalVisible = ref(false);
const options = ref<ApiSelectOption[]>([]);
const selectedValues = ref<Set<string>>(
  new Set(
    Array.isArray(props.modelValue)
      ? props.modelValue
      : props.modelValue
        ? [props.modelValue]
        : [],
  ),
);
const tempSelectedValues = ref<Set<string>>(new Set());
const loading = ref(false);
const searchText = ref('');
const currentPage = ref(1);
const totalItems = ref(0);
const isLoadingMore = ref(false);
const hasLoadedData = ref(false);
const hasLoadedFullList = ref(false);

// 计算显示值
const displayValue = computed({
  get() {
    if (selectedValues.value.size === 0) return undefined;
    if (props.multiple) {
      return [...selectedValues.value];
    }
    return [...selectedValues.value][0];
  },
  set(_value) {
    // ElSelect 会改变这个值，但我们不需要处理
  },
});

// 获取已选项的信息
const selectedOptionsWithInfo = computed(() => {
  const result: ApiSelectOption[] = [];
  const seenValues = new Set<string>();

  for (const value of selectedValues.value) {
    if (seenValues.has(value)) continue;

    const option = options.value.find((o) => o.value === value);
    if (option) {
      seenValues.add(value);
      result.push(option);
    }
  }
  return result;
});

// 获取临时选择项的信息
const tempSelectedOptionsWithInfo = computed(() => {
  const result: ApiSelectOption[] = [];
  const seenValues = new Set<string>();

  for (const value of tempSelectedValues.value) {
    if (seenValues.has(value)) continue;

    const option = options.value.find((o) => o.value === value);
    if (option) {
      seenValues.add(value);
      result.push(option);
    }
  }
  return result;
});

// 将原始数据转换为选项
const convertToOption = (item: any): ApiSelectOption => {
  return {
    value: String(item[props.valueField]),
    label: String(item[props.labelField] || ''),
    extra: props.extraField ? String(item[props.extraField] || '') : undefined,
    raw: item,
  };
};

// 加载数据（分页）
const loadData = async (page: number = 1, append: boolean = false) => {
  try {
    if (page === 1) {
      loading.value = true;
    } else {
      isLoadingMore.value = true;
    }

    const result = await props.api({
      page,
      pageSize: props.pageSize,
      keyword: searchText.value || undefined,
    });

    if (result) {
      const existingValues = new Set(options.value.map((o) => o.value));
      const newOptions = (result.items || [])
        .map(convertToOption)
        .filter((o) => !existingValues.has(o.value));

      options.value = append
        ? [...options.value, ...newOptions]
        : [...options.value, ...newOptions];

      totalItems.value = result.total || 0;
      currentPage.value = page;
      hasLoadedData.value = true;
      hasLoadedFullList.value = true;
    }

    loading.value = false;
    isLoadingMore.value = false;
  } catch (error) {
    console.error('Failed to load data:', error);
    loading.value = false;
    isLoadingMore.value = false;
  }
};

// 根据 ID 加载特定数据（用于回显）
const loadDataByIds = async (ids: string[]) => {
  if (!ids || ids.length === 0 || !props.apiByIds) return;

  try {
    loading.value = true;

    const result = await props.apiByIds(ids);

    if (result && result.length > 0) {
      const existingValues = new Set(options.value.map((o) => o.value));
      const newOptions = result
        .map(convertToOption)
        .filter((o) => !existingValues.has(o.value));
      options.value = [...options.value, ...newOptions];
      hasLoadedData.value = true;
    }

    loading.value = false;
  } catch (error) {
    console.error('Failed to load data by ids:', error);
    loading.value = false;
  }
};

// 判断是否还有更多数据
const hasMoreData = computed(() => {
  return options.value.length < totalItems.value;
});

// 防抖搜索定时器
let searchTimer: null | ReturnType<typeof setTimeout> = null;

// 监听搜索文本变化
watch(searchText, () => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }

  searchTimer = setTimeout(() => {
    currentPage.value = 1;
    loadData(1, false);
  }, 300);
});

// 处理选择
const handleSelect = (value: string) => {
  if (props.multiple) {
    if (tempSelectedValues.value.has(value)) {
      tempSelectedValues.value.delete(value);
    } else {
      tempSelectedValues.value.add(value);
    }
  } else {
    // 单选模式：只更新临时选择，不自动确认
    tempSelectedValues.value.clear();
    tempSelectedValues.value.add(value);
  }
};

// 打开弹窗
const openModal = async () => {
  if (props.disabled) return;
  modalVisible.value = true;
};

// 弹窗打开后加载数据
const handleModalOpened = async () => {
  tempSelectedValues.value = new Set(selectedValues.value);

  if (!hasLoadedFullList.value) {
    await loadData(1, false);
  }
};

// 触底加载更多
const handleScroll = ({ scrollTop }: { scrollTop: number }) => {
  const scrollbarRef = document.querySelector(
    '.zq-api-selector-list .el-scrollbar__wrap',
  );
  if (!scrollbarRef) return;

  const scrollHeight = scrollbarRef.scrollHeight;
  const clientHeight = scrollbarRef.clientHeight;

  if (
    scrollTop + clientHeight >= scrollHeight - 50 &&
    hasMoreData.value &&
    !isLoadingMore.value &&
    !loading.value
  ) {
    loadData(currentPage.value + 1, true);
  }
};

// 确认选择
const handleConfirm = () => {
  selectedValues.value = new Set(tempSelectedValues.value);

  const value = props.multiple
    ? [...selectedValues.value]
    : selectedValues.value.size > 0
      ? [...selectedValues.value][0]
      : '';

  emit('update:modelValue', value);
  emit('change', value);
  modalVisible.value = false;
};

// 清除选择
const handleClear = (e?: MouseEvent) => {
  if (e) {
    e.stopPropagation();
  }
  tempSelectedValues.value.clear();
  selectedValues.value.clear();
  const emptyValue = props.multiple ? [] : '';
  emit('update:modelValue', emptyValue);
  emit('change', emptyValue);
};

// 删除单个选中项
const handleRemoveTag = (value: string) => {
  selectedValues.value.delete(value);
  const newValue = props.multiple ? [...selectedValues.value] : '';
  emit('update:modelValue', newValue);
  emit('change', newValue);
};

// 更新内部值
const updateInternalValue = () => {
  selectedValues.value.clear();
  tempSelectedValues.value.clear();
  if (Array.isArray(props.modelValue)) {
    props.modelValue.forEach((v) => selectedValues.value.add(v));
  } else if (props.modelValue) {
    selectedValues.value.add(props.modelValue);
  }
  if (modalVisible.value) {
    tempSelectedValues.value = new Set(selectedValues.value);
  }
};

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  async (newValue) => {
    updateInternalValue();

    if (
      ((Array.isArray(newValue) && newValue.length > 0) ||
        (typeof newValue === 'string' && newValue)) &&
      !hasLoadedData.value &&
      props.apiByIds
    ) {
      const ids = Array.isArray(newValue) ? newValue : [newValue];
      await loadDataByIds(ids);
    }
  },
  { immediate: true },
);

// 组件挂载时加载初始数据
onMounted(async () => {
  if (
    ((Array.isArray(props.modelValue) && props.modelValue.length > 0) ||
      (typeof props.modelValue === 'string' && props.modelValue)) &&
    props.apiByIds
  ) {
    const ids = Array.isArray(props.modelValue)
      ? props.modelValue
      : [props.modelValue];
    await loadDataByIds(ids);
  }
});

defineExpose({
  openModal,
});
</script>

<template>
  <div class="zq-api-select">
    <!-- 选择框 -->
    <div class="zq-api-select-input" :class="{ disabled }">
      <ElSelect
        v-bind="attrs"
        v-model="displayValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :clearable="clearable && selectedValues.size > 0"
        :multiple="multiple"
        readonly
        @click="openModal"
        @clear="() => handleClear()"
        @remove-tag="handleRemoveTag"
      >
        <ElOption
          v-for="item in selectedOptionsWithInfo"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </ElSelect>
    </div>

    <!-- Modal -->
    <ZqDialog
      v-model="modalVisible"
      :title="dialogTitle"
      :width="dialogWidth"
      class="zq-api-select-modal"
      :show-footer="true"
      @opened="handleModalOpened"
      @confirm="handleConfirm"
    >
      <div class="zq-api-select-content">
        <!-- 顶部：已选项（左侧）+ 搜索框（右侧） -->
        <div class="zq-api-select-header-row">
          <div class="header-middle">
            <div
              v-if="tempSelectedOptionsWithInfo.length > 0"
              class="selected-tags"
            >
              <ElTag
                v-for="item of tempSelectedOptionsWithInfo"
                :key="item.value"
                closable
                type="info"
                size="small"
                @close="
                  () => {
                    tempSelectedValues.delete(item.value);
                  }
                "
              >
                {{ item.label }}
              </ElTag>
            </div>
            <span v-else class="empty-text">-</span>
          </div>

          <!-- 已选数量和清空按钮 -->
          <div class="header-actions">
            <span class="selected-count">
              {{ tempSelectedValues.size }}
              {{ $t('common.selected') || 'selected' }}
            </span>
            <el-button
              v-if="tempSelectedValues.size > 0"
              link
              type="danger"
              size="small"
              @click="() => tempSelectedValues.clear()"
            >
              {{ $t('common.clear') || 'Clear' }}
            </el-button>
          </div>

          <!-- 搜索框（右侧） -->
          <div v-if="filterable" class="header-search">
            <ElInput
              v-model="searchText"
              :placeholder="$t('common.search') || 'Search'"
              clearable
              :prefix-icon="Search"
            />
          </div>
        </div>

        <!-- 列表 -->
        <el-scrollbar class="zq-api-select-list" @scroll="handleScroll">
          <ElSkeleton :loading="loading" animated :count="8">
            <template #template>
              <div class="zq-api-select-list-content">
                <div v-for="i in 8" :key="i" class="skeleton-item">
                  <ElSkeletonItem
                    variant="text"
                    style="width: 100%; height: 40px; margin: 8px 0"
                  />
                </div>
              </div>
            </template>
            <template #default>
              <div class="zq-api-select-list-content">
                <ElEmpty
                  v-if="options.length === 0 && !loading"
                  :description="$t('common.noData') || 'No Data'"
                />
                <div v-else class="option-list">
                  <div
                    v-for="option in options"
                    :key="option.value"
                    class="option-item"
                    :class="[
                      tempSelectedValues.has(option.value)
                        ? 'bg-primary/15 dark:bg-accent text-primary'
                        : 'hover:bg-[var(--el-fill-color-light)]',
                    ]"
                    @click="handleSelect(option.value)"
                  >
                    <!-- 标签 -->
                    <div class="option-label">{{ option.label }}</div>

                    <!-- 额外信息 -->
                    <div v-if="option.extra" class="option-extra">
                      {{ option.extra }}
                    </div>
                  </div>

                  <!-- 加载更多提示 -->
                  <div v-if="isLoadingMore" class="loading-more">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 100%; height: 40px"
                    />
                  </div>

                  <!-- 没有更多数据提示 -->
                  <div
                    v-if="!hasMoreData && options.length > 0"
                    class="no-more-data"
                  >
                    {{ $t('common.noMoreData') || 'No more data' }}
                  </div>
                </div>
              </div>
            </template>
          </ElSkeleton>
        </el-scrollbar>
      </div>
    </ZqDialog>
  </div>
</template>

<style lang="scss" scoped>
.zq-api-select {
  width: 100%;

  &-input {
    cursor: pointer;

    &.disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    :deep(.el-input) {
      &.is-disabled {
        background-color: var(--background-deep, #f5f7fa);
      }
    }
  }

  &-content {
    display: flex;
    flex-direction: column;
    gap: 0;
    height: 500px;
    padding: 0;
    overflow: hidden;
    background-color: hsl(var(--background));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    box-shadow: 0 1px 3px hsl(var(--border) / 12%);
  }

  &-header-row {
    display: flex;
    flex-shrink: 0;
    gap: 12px;
    align-items: center;
    padding: 12px 16px;
    background: linear-gradient(
      90deg,
      hsl(var(--background)) 0%,
      hsl(var(--background-deep) / 30%) 100%
    );
    border-bottom: 1px solid hsl(var(--border));

    .header-middle {
      display: flex;
      flex: 1;
      gap: 8px;
      align-items: center;
      min-width: 80px;
      max-height: 40px;
      overflow-y: auto;

      .selected-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;

        :deep(.el-tag) {
          height: 24px;
          font-size: 12px;
          line-height: 22px;
        }
      }

      .empty-text {
        font-size: 12px;
        color: hsl(var(--muted-foreground));
        white-space: nowrap;
      }
    }

    .header-actions {
      display: flex;
      flex-shrink: 0;
      gap: 8px;
      align-items: center;

      .selected-count {
        font-size: 12px;
        color: hsl(var(--muted-foreground));
        white-space: nowrap;
      }
    }

    .header-search {
      flex-shrink: 0;
      width: 160px;

      :deep(.el-input) {
        font-size: 14px;
      }
    }
  }

  &-list {
    flex: 1;
    overflow-y: auto;
    border-top: none;
  }

  &-list-content {
    display: flex;
    flex: 1;
    flex-direction: column;
    width: 100%;
    padding: 8px 10px;

    .option-list {
      display: flex;
      flex-direction: column;
    }

    .option-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 42px;
      padding: 0 12px;
      margin: 1px 0;
      cursor: pointer;
      border-radius: 8px;
      transition: all 0.2s ease;

      .option-label {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 14px;
        white-space: nowrap;
        transition: color 0.2s ease;
      }

      .option-extra {
        flex-shrink: 0;
        padding: 2px 8px;
        margin-left: 8px;
        font-size: 12px;
        color: hsl(var(--muted-foreground));
        white-space: nowrap;
        background: hsl(var(--background-deep) / 50%);
        border-radius: 4px;
      }
    }
  }
}

.skeleton-item {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 8px 12px;
}

.no-more-data {
  padding: 12px;
  font-size: 12px;
  color: hsl(var(--muted-foreground));
  text-align: center;
}
</style>
