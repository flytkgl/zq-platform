<script lang="ts" setup>
import type {
  TableSelectorColumn,
  TableSelectorEmits,
  TableSelectorProps,
} from './types';

import { computed, ref, watch } from 'vue';

import { Table2 } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCheckbox,
  ElInput,
  ElOption,
  ElPagination,
  ElRadio,
  ElSelect,
  ElTable,
  ElTableColumn,
} from 'element-plus';

import { requestClient } from '#/api/request';
import { ZqDialog } from '#/components/zq-dialog';

defineOptions({
  name: 'TableSelector',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  placeholder: () => $t('form-design.attribute.clickToSelect'),
  disabled: false,
  clearable: true,
  dialogTitle: () => $t('form-design.attribute.selectData'),
  dialogWidth: '800px',
  columns: () => [],
  labelField: 'label',
  valueField: 'value',
  dataSourceType: 'static',
  searchFields: () => [],
  collapseTags: false,
  options: () => [],
});

const emit = defineEmits<TableSelectorEmits>();

interface Props extends TableSelectorProps {
  dataSourceType?: 'api' | 'dataSource' | 'dict' | 'formData' | 'static';
  dictCode?: string;
  dataSourceCode?: string;
  formCode?: string;
  apiUrl?: string;
  apiMethod?: 'GET' | 'POST';
  searchFields?: string[];
  collapseTags?: boolean;
  options?: Array<Record<string, any>>;
}

const dialogVisible = ref(false);
const loading = ref(false);
const tableRef = ref();
const tableData = ref<any[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const searchKeyword = ref('');

// 选中的值
const selectedValues = ref<Set<string>>(new Set());
// 选中项的信息映射
const selectedItemsMap = ref<Map<string, any>>(new Map());
// 标签加载状态
const labelsLoading = ref(false);

// 初始化选中值
watch(
  () => props.modelValue,
  async (val) => {
    if (val) {
      const values = Array.isArray(val) ? val : [val];
      selectedValues.value = new Set(values.map(String));

      // 如果有初始值但 selectedItemsMap 中没有对应的标签信息，需要加载
      const missingValues = values.filter(
        (v) => !selectedItemsMap.value.has(String(v)),
      );
      if (missingValues.length > 0) {
        labelsLoading.value = true;
        await loadInitialLabels(missingValues);
        labelsLoading.value = false;

        // 加载完成后，触发 select-item 事件，供关联字段组件使用
        emitSelectItem();
      }
    } else {
      selectedValues.value = new Set();
    }
  },
  { immediate: true },
);

// 触发 select-item 事件
const emitSelectItem = () => {
  const items = [...selectedValues.value]
    .map((v) => selectedItemsMap.value.get(v))
    .filter(Boolean);
  if (props.multiple) {
    emit('select-item', items.length > 0 ? items : undefined);
  } else {
    emit('select-item', items[0] || undefined);
  }
};

// 加载初始值对应的标签信息
const loadInitialLabels = async (values: any[]) => {
  try {
    const stringValues = values.map(String);

    // 静态数据 - 直接从 options 中查找
    if (
      props.dataSourceType === 'static' ||
      (!props.dataSourceType && props.options && props.options.length > 0)
    ) {
      const staticData = props.options || [];
      for (const item of staticData) {
        const value = String(item[props.valueField]);
        if (stringValues.includes(value)) {
          selectedItemsMap.value.set(value, item);
        }
      }
    } else if (props.dataSourceType === 'formData' && props.formCode) {
      // 通过 ID 列表精确查询，不受分页影响
      const ids = stringValues.join(',');
      const response = await requestClient.get(
        `/api/online_dev/form-data/${props.formCode}/list`,
        {
          params: {
            [`${props.valueField}__in`]: ids,
            pageSize: stringValues.length,
          },
        },
      );
      const data = response?.items || [];
      for (const item of data) {
        const value = String(item[props.valueField]);
        selectedItemsMap.value.set(value, item);
      }
    } else if (props.dataSourceType === 'dict' && props.dictCode) {
      // 字典数据通常数据量不大，整体加载后过滤
      const response = await requestClient.get(
        `/api/core/dict_item/by/dict_code/${props.dictCode}`,
      );
      const data = response || [];
      for (const item of data) {
        const value = String(item[props.valueField]);
        if (stringValues.includes(value)) {
          selectedItemsMap.value.set(value, item);
        }
      }
    } else if (props.dataSourceType === 'dataSource' && props.dataSourceCode) {
      // 数据源通常数据量不大，整体加载后过滤
      const response = await requestClient.get(
        `/api/core/data-source/execute/${props.dataSourceCode}`,
      );
      const data = Array.isArray(response)
        ? response
        : response?.list || response?.data || [];
      for (const item of data) {
        const value = String(item[props.valueField]);
        if (stringValues.includes(value)) {
          selectedItemsMap.value.set(value, item);
        }
      }
    }
  } catch (error) {
    console.error('加载初始标签失败:', error);
  }
};

// 显示的标签列表
const displayTags = computed(() => {
  const result: Array<{ label: string; value: string }> = [];
  for (const value of selectedValues.value) {
    const item = selectedItemsMap.value.get(value);
    result.push({
      value,
      label: item ? item[props.labelField] : value,
    });
  }
  return result;
});

// el-select 的显示值
const selectDisplayValue = computed(() => {
  const values = [...selectedValues.value];
  return props.multiple ? values : values[0];
});

// 是否显示分页（formData 和 api 类型始终显示，其他类型在数据超过一页时显示）
const showPagination = computed(() => {
  if (props.dataSourceType === 'formData' || props.dataSourceType === 'api') {
    return true;
  }
  return total.value > pageSize.value;
});

// 打开弹窗
const openDialog = () => {
  if (props.disabled) return;
  dialogVisible.value = true;
  loadData();
};

// 加载数据
const loadData = async () => {
  loading.value = true;
  try {
    let data: any[] = [];
    let totalCount = 0;

    // 静态数据
    if (
      props.dataSourceType === 'static' ||
      (!props.dataSourceType && props.options && props.options.length > 0)
    ) {
      let staticData = props.options || [];
      // 搜索过滤
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase();
        staticData = staticData.filter((item) => {
          const label = String(item[props.labelField] || '').toLowerCase();
          const value = String(item[props.valueField] || '').toLowerCase();
          return label.includes(keyword) || value.includes(keyword);
        });
      }
      data = staticData;
      totalCount = staticData.length;
    } else if (props.dataSourceType === 'formData' && props.formCode) {
      const params: Record<string, any> = {
        page: currentPage.value,
        pageSize: pageSize.value,
      };
      // 使用配置的搜索字段，如果没有配置则使用 labelField
      // 注意：后端目前不支持 OR 查询，所以只使用第一个搜索字段
      if (searchKeyword.value) {
        const searchField =
          props.searchFields && props.searchFields.length > 0
            ? props.searchFields[0]
            : props.labelField;
        params[`${searchField}__like`] = searchKeyword.value;
      }
      const response = await requestClient.get(
        `/api/online_dev/form-data/${props.formCode}/list`,
        { params },
      );
      data = response?.items || [];
      totalCount = response?.total || 0;
    } else if (props.dataSourceType === 'dict' && props.dictCode) {
      const response = await requestClient.get(
        `/api/core/dict_item/by/dict_code/${props.dictCode}`,
      );
      data = response || [];
      totalCount = data.length;
    } else if (props.dataSourceType === 'dataSource' && props.dataSourceCode) {
      const response = await requestClient.get(
        `/api/core/data-source/execute/${props.dataSourceCode}`,
      );
      data = Array.isArray(response)
        ? response
        : response?.list || response?.data || [];
      totalCount = data.length;
    } else if (props.dataSourceType === 'api' && props.apiUrl) {
      const response =
        props.apiMethod === 'POST'
          ? await requestClient.post(props.apiUrl, {
              page: currentPage.value,
              pageSize: pageSize.value,
              keyword: searchKeyword.value,
            })
          : await requestClient.get(props.apiUrl, {
              params: {
                page: currentPage.value,
                pageSize: pageSize.value,
                keyword: searchKeyword.value,
              },
            });
      data = response?.items || response?.list || response?.data || [];
      totalCount = response?.total || data.length;
    }

    tableData.value = data;
    total.value = totalCount;

    // 更新选中项的信息
    for (const item of data) {
      const value = item[props.valueField];
      if (selectedValues.value.has(String(value))) {
        selectedItemsMap.value.set(String(value), item);
      }
    }
  } catch (error) {
    console.error('加载数据失败:', error);
    tableData.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadData();
};

// 分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadData();
};

const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  loadData();
};

// 行点击选择
const handleRowClick = (row: any) => {
  const value = String(row[props.valueField]);

  if (props.multiple) {
    if (selectedValues.value.has(value)) {
      selectedValues.value.delete(value);
      selectedItemsMap.value.delete(value);
    } else {
      selectedValues.value.add(value);
      selectedItemsMap.value.set(value, row);
    }
    selectedValues.value = new Set(selectedValues.value);
  } else {
    selectedValues.value = new Set([value]);
    selectedItemsMap.value.clear();
    selectedItemsMap.value.set(value, row);
  }
};

// 判断行是否选中
const isRowSelected = (row: any) => {
  const value = String(row[props.valueField]);
  return selectedValues.value.has(value);
};

// 获取行的值
const getRowValue = (row: any) => {
  return String(row[props.valueField]);
};

// 单选变化
const handleRadioChange = (row: any) => {
  const value = String(row[props.valueField]);
  selectedValues.value = new Set([value]);
  selectedItemsMap.value.clear();
  selectedItemsMap.value.set(value, row);
};

// 多选变化
const handleCheckboxChange = (row: any, checked: boolean | number | string) => {
  const value = String(row[props.valueField]);
  if (checked) {
    selectedValues.value.add(value);
    selectedItemsMap.value.set(value, row);
  } else {
    selectedValues.value.delete(value);
    selectedItemsMap.value.delete(value);
  }
  selectedValues.value = new Set(selectedValues.value);
};

// 全选/取消全选
const handleSelectAll = (checked: boolean | number | string) => {
  if (checked) {
    for (const row of tableData.value) {
      const value = String(row[props.valueField]);
      selectedValues.value.add(value);
      selectedItemsMap.value.set(value, row);
    }
  } else {
    for (const row of tableData.value) {
      const value = String(row[props.valueField]);
      selectedValues.value.delete(value);
      selectedItemsMap.value.delete(value);
    }
  }
  selectedValues.value = new Set(selectedValues.value);
};

// 是否全选
const isAllSelected = computed(() => {
  if (tableData.value.length === 0) return false;
  return tableData.value.every((row) => isRowSelected(row));
});

// 是否部分选中
const isIndeterminate = computed(() => {
  if (tableData.value.length === 0) return false;
  const selectedCount = tableData.value.filter((row) =>
    isRowSelected(row),
  ).length;
  return selectedCount > 0 && selectedCount < tableData.value.length;
});

// 确认选择
const handleConfirm = () => {
  const values = [...selectedValues.value];
  const result = props.multiple ? values : values[0];
  emit('update:modelValue', result);
  emit('change', result);
  emit('blur');

  // 发出选中项的完整数据
  const selectedItems = values
    .map((v) => selectedItemsMap.value.get(v))
    .filter(Boolean);
  const itemResult = props.multiple ? selectedItems : selectedItems[0];
  emit('select-item', itemResult);

  dialogVisible.value = false;
};

// 清空选择
const handleClear = () => {
  selectedValues.value = new Set();
  selectedItemsMap.value.clear();
  emit('update:modelValue', props.multiple ? [] : undefined);
  emit('change', props.multiple ? [] : undefined);
};

// 移除单个标签
const handleRemoveTag = (value: string) => {
  selectedValues.value.delete(value);
  selectedItemsMap.value.delete(value);
  selectedValues.value = new Set(selectedValues.value);

  const values = [...selectedValues.value];
  const result = props.multiple ? values : values[0];
  emit('update:modelValue', result);
  emit('change', result);
};

// 获取显示的列
const displayColumns = computed<TableSelectorColumn[]>(() => {
  if (props.columns && props.columns.length > 0) {
    return props.columns;
  }
  // 默认显示 labelField 和 valueField
  return [
    { field: props.labelField, label: $t('form-design.attribute.nodeLabel') },
    { field: props.valueField, label: $t('form-design.attribute.nodeValue') },
  ];
});
</script>

<template>
  <div class="table-selector">
    <!-- 使用 el-select 作为显示区域 -->
    <ElSelect
      :model-value="labelsLoading ? undefined : selectDisplayValue"
      :placeholder="labelsLoading ? $t('common.loading') : placeholder"
      :disabled="disabled"
      :clearable="clearable"
      :multiple="multiple"
      :collapse-tags="multiple && collapseTags"
      :collapse-tags-tooltip="multiple && collapseTags"
      :loading="labelsLoading"
      :suffix-icon="Table2"
      class="w-full"
      popper-class="table-selector-popper-hidden"
      @click="openDialog"
      @clear="handleClear"
      @remove-tag="handleRemoveTag"
    >
      <ElOption
        v-for="tag in displayTags"
        :key="tag.value"
        :label="tag.label"
        :value="tag.value"
      />
    </ElSelect>

    <!-- 选择弹窗 -->
    <ZqDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :width="dialogWidth"
      @confirm="handleConfirm"
    >
      <div class="table-selector-content flex h-[600px] flex-col">
        <!-- 搜索栏 -->
        <div class="mb-4 flex shrink-0 items-center gap-2">
          <ElInput
            v-model="searchKeyword"
            :placeholder="$t('form-design.search')"
            clearable
            class="w-64"
            @keyup.enter="handleSearch"
            @change="handleSearch"
          />
          <ElButton type="primary" @click="handleSearch">
            {{ $t('common.search') }}
          </ElButton>
        </div>

        <!-- 数据表格 -->
        <div class="min-h-0 flex-1">
          <ElTable
            ref="tableRef"
            v-loading="loading"
            :data="tableData"
            border
            stripe
            height="100%"
            :row-class-name="
              ({ row }: any) => (isRowSelected(row) ? 'selected-row' : '')
            "
            style="width: 100%"
            @row-click="handleRowClick"
          >
            <!-- 单选列 -->
            <ElTableColumn v-if="!multiple" width="55" align="center">
              <template #default="{ row }">
                <ElRadio
                  :model-value="isRowSelected(row) ? getRowValue(row) : ''"
                  :value="getRowValue(row)"
                  @click.stop
                  @change="handleRadioChange(row)"
                >
                  <span></span>
                </ElRadio>
              </template>
            </ElTableColumn>
            <!-- 多选列 -->
            <ElTableColumn v-else width="55" align="center">
              <template #header>
                <ElCheckbox
                  :model-value="isAllSelected"
                  :indeterminate="isIndeterminate"
                  @change="handleSelectAll"
                />
              </template>
              <template #default="{ row }">
                <ElCheckbox
                  :model-value="isRowSelected(row)"
                  @click.stop
                  @change="handleCheckboxChange(row, $event)"
                />
              </template>
            </ElTableColumn>
            <!-- 数据列 -->
            <ElTableColumn
              v-for="col in displayColumns"
              :key="col.field"
              :prop="col.field"
              :label="col.label"
              :width="col.width"
            />
          </ElTable>
        </div>
      </div>

      <!-- Footer -->
      <template #footer>
        <div class="flex w-full items-center">
          <!-- 分页 - 左侧 -->
          <div class="flex-shrink-0">
            <ElPagination
              v-if="showPagination"
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              small
              @current-change="handlePageChange"
              @size-change="handleSizeChange"
            />
          </div>
          <!-- 已选提示 - 中间 -->
          <div class="flex flex-1 justify-center">
            <span
              v-if="selectedValues.size > 0"
              class="text-sm text-[var(--el-text-color-secondary)]"
            >
              {{
                $t('form-design.attribute.selectedCount', {
                  count: selectedValues.size,
                })
              }}
            </span>
          </div>
          <!-- 按钮 - 右侧 -->
          <div class="flex flex-shrink-0 gap-2">
            <ElButton @click="dialogVisible = false">
              {{ $t('common.cancel') }}
            </ElButton>
            <ElButton type="primary" @click="handleConfirm">
              {{ $t('common.confirm') }}
            </ElButton>
          </div>
        </div>
      </template>
    </ZqDialog>
  </div>
</template>

<style scoped>
.table-selector {
  width: 100%;
}

.table-selector-content :deep(.selected-row) {
  background-color: var(--el-color-primary-light-9) !important;
}

.table-selector-content :deep(.el-table__row) {
  cursor: pointer;
}
</style>

<style>
/* 隐藏 table-selector 的下拉弹窗 */
.table-selector-popper-hidden {
  display: none !important;
}
</style>
