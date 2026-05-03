<script setup lang="ts">
import type { DashboardWidget } from '../../store/dashboardDesignStore';

import { computed } from 'vue';

import { $t } from '@vben/locales';

import { ElEmpty, ElTable, ElTableColumn } from 'element-plus';

const props = defineProps<{
  widget: DashboardWidget;
}>();

const columns = computed(() => props.widget.props.columns || []);
const tableData = computed(() => props.widget.props.data || []);

// 表格高度配置
const tableHeight = computed(() => {
  if (props.widget.props.maxHeight) return undefined;
  return props.widget.props.height || '100%';
});

// 状态颜色映射
const getStatusClass = (status: string) => {
  const statusMap: Record<string, string> = {
    [$t('dashboard-design.widgets.dataTable.status.normal')]: 'status-success',
    [$t('dashboard-design.widgets.dataTable.status.warning')]: 'status-warning',
    [$t('dashboard-design.widgets.dataTable.status.error')]: 'status-danger',
    [$t('dashboard-design.widgets.dataTable.status.success')]: 'status-success',
    [$t('dashboard-design.widgets.dataTable.status.failed')]: 'status-danger',
    [$t('dashboard-design.widgets.dataTable.status.processing')]: 'status-info',
  };
  return statusMap[status] || '';
};

// 统计类型国际化标签
const summaryTypeLabels = computed(() => ({
  sum: $t('dashboard-design.widgets.dataTable.summary.sum'),
  avg: $t('dashboard-design.widgets.dataTable.summary.avg'),
  count: $t('dashboard-design.widgets.dataTable.summary.count'),
  max: $t('dashboard-design.widgets.dataTable.summary.max'),
  min: $t('dashboard-design.widgets.dataTable.summary.min'),
}));

// 表尾统计方法
const getSummaryMethod = (param: { columns: any[]; data: any[] }) => {
  const { columns: tableCols, data } = param;
  const sums: string[] = [];
  const summaryColumns = props.widget.props.summaryColumns || [];
  const summaryType = props.widget.props.summaryType || 'sum';
  const precision = props.widget.props.summaryPrecision ?? 2;

  tableCols.forEach((column, index) => {
    // 第一列显示统计类型名称
    if (index === 0) {
      sums[index] =
        summaryTypeLabels.value[
          summaryType as keyof typeof summaryTypeLabels.value
        ] || summaryType;
      return;
    }

    // 查找该列的统计配置
    const summaryConfig = summaryColumns.find(
      (sc: any) => sc.field === column.property,
    );

    if (!summaryConfig || !summaryConfig.enabled) {
      sums[index] = '';
      return;
    }

    // 获取该列的所有数值
    const values = data.map((item) => Number(item[column.property]));
    const validValues = values.filter((value) => !Number.isNaN(value));

    if (validValues.length === 0) {
      sums[index] = '-';
      return;
    }

    let result: number;
    switch (summaryType) {
      case 'avg': {
        result =
          validValues.reduce((acc, val) => acc + val, 0) / validValues.length;
        break;
      }
      case 'count': {
        result = validValues.length;
        break;
      }
      case 'max': {
        result = Math.max(...validValues);
        break;
      }
      case 'min': {
        result = Math.min(...validValues);
        break;
      }
      case 'sum': {
        result = validValues.reduce((acc, val) => acc + val, 0);
        break;
      }
      default: {
        result = validValues.reduce((acc, val) => acc + val, 0);
      }
    }

    sums[index] = result.toFixed(precision);
  });

  return sums;
};

// 合并单元格方法
const getSpanMethod = ({ row, column, rowIndex, columnIndex }: any) => {
  const mergeConfig = props.widget.props.mergeConfig;
  if (!mergeConfig || !mergeConfig.enabled) return;

  const mergeRules = mergeConfig.rules || [];

  for (const rule of mergeRules) {
    if (rule.type === 'row' && rule.field === column.property) {
      // 行合并：相同值的相邻行合并
      const data = tableData.value;
      const currentValue = row[rule.field];

      // 检查是否是合并组的第一行
      if (rowIndex === 0 || data[rowIndex - 1][rule.field] !== currentValue) {
        let rowspan = 1;
        for (let i = rowIndex + 1; i < data.length; i++) {
          if (data[i][rule.field] === currentValue) {
            rowspan++;
          } else {
            break;
          }
        }
        return { rowspan, colspan: 1 };
      } else {
        // 被合并的行
        return { rowspan: 0, colspan: 0 };
      }
    }

    if (rule.type === 'column' && rowIndex === rule.rowIndex) {
      // 列合并
      if (columnIndex === rule.startCol) {
        return { rowspan: 1, colspan: rule.colspan || 1 };
      } else if (
        columnIndex > rule.startCol &&
        columnIndex < rule.startCol + (rule.colspan || 1)
      ) {
        return { rowspan: 0, colspan: 0 };
      }
    }
  }
};
</script>

<template>
  <div class="data-table-widget flex h-full w-full flex-col p-3">
    <div
      v-if="widget.props.title"
      class="text-muted-foreground mb-2 text-sm font-medium"
    >
      {{ widget.props.title }}
    </div>

    <div class="table-container">
      <ElTable
        :data="tableData"
        :stripe="widget.props.stripe !== false"
        :border="widget.props.border"
        :size="widget.props.size || 'default'"
        :height="tableHeight"
        :max-height="widget.props.maxHeight"
        :highlight-current-row="widget.props.highlightCurrentRow"
        :show-header="widget.props.showHeader !== false"
        :empty-text="widget.props.emptyText || $t('common.noData')"
        :show-summary="widget.props.showSummary"
        :summary-method="
          widget.props.showSummary ? getSummaryMethod : undefined
        "
        :span-method="
          widget.props.mergeConfig?.enabled ? getSpanMethod : undefined
        "
        :header-cell-style="{
          textAlign: widget.props.headerAlign || 'left',
          ...(widget.props.headerBgColor?.includes('gradient')
            ? { background: widget.props.headerBgColor }
            : {
                backgroundColor:
                  widget.props.headerBgColor || 'var(--el-fill-color-light)',
              }),
        }"
        :cell-style="{
          textAlign: widget.props.cellAlign || 'left',
        }"
        v-loading="widget.props.loading"
      >
        <ElTableColumn
          v-if="widget.props.showIndex"
          type="index"
          label="#"
          width="50"
        />
        <ElTableColumn
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :width="col.width"
          :min-width="col.minWidth"
          :align="col.align || widget.props.cellAlign || 'left'"
          :header-align="col.headerAlign || widget.props.headerAlign || 'left'"
          :fixed="col.fixed"
          :sortable="col.sortable"
          :show-overflow-tooltip="col.showOverflowTooltip !== false"
        >
          <template #default="{ row }">
            <span
              v-if="col.prop === 'status'"
              :class="getStatusClass(row[col.prop])"
            >
              {{ row[col.prop] }}
            </span>
            <span v-else>{{ row[col.prop] }}</span>
          </template>
        </ElTableColumn>
        <template #empty>
          <ElEmpty
            :description="widget.props.emptyText || $t('common.noData')"
            :image-size="80"
          />
        </template>
      </ElTable>
    </div>
  </div>
</template>

<style scoped>
.data-table-widget {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.table-container {
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow: hidden;
}

.data-table-widget :deep(.el-table) {
  width: 100% !important;
  --el-table-header-bg-color: var(--el-fill-color-light);
}

.data-table-widget :deep(.el-table__inner-wrapper) {
  width: 100%;
}

.data-table-widget :deep(.el-table__header-wrapper),
.data-table-widget :deep(.el-table__body-wrapper) {
  width: 100%;
}

.status-success {
  color: var(--el-color-success);
}

.status-warning {
  color: var(--el-color-warning);
}

.status-danger {
  color: var(--el-color-danger);
}

.status-info {
  color: var(--el-color-info);
}
</style>
