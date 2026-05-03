<script lang="ts" setup>
import type { FormulaInputEmits, FormulaInputProps } from './types';

import { computed, ref, watch } from 'vue';

import { ElInput, ElTooltip } from 'element-plus';

defineOptions({
  name: 'FormulaInput',
});

const props = withDefaults(defineProps<FormulaInputProps>(), {
  precision: 2,
  disabled: true,
  placeholder: '自动计算',
  showFormula: true,
});

const emit = defineEmits<FormulaInputEmits>();

const AGGREGATE_REGEX = /(?:(SUM|AVG|MAX|MIN|COUNT)\{([^}]+)\})/g;
const DATEDIFF_REGEX =
  /DATEDIFF\{\s*([^,}]+)\s*,\s*([^,}]+)\s*(?:,\s*(days|hours|minutes)\s*)?\}/g;
const SIMPLE_FIELD_REGEX = /\B\{([^}]+)\}/g;

const parseDateValue = (value: any): Date | null => {
  if (!value) return null;
  if (value instanceof Date) return value;
  if (typeof value === 'string' || typeof value === 'number') {
    const d = new Date(value);
    if (!Number.isNaN(d.getTime())) return d;
  }
  return null;
};

const computeDateDiff = (
  endField: string,
  startField: string,
  unit: string,
  data: Record<string, any>,
): null | number => {
  const endVal = parseDateValue(data[endField.trim()]);
  const startVal = parseDateValue(data[startField.trim()]);
  if (!endVal || !startVal) return null;
  const diffMs = endVal.getTime() - startVal.getTime();
  switch (unit) {
    case 'hours': {
      return diffMs / (1000 * 60 * 60);
    }
    case 'minutes': {
      return diffMs / (1000 * 60);
    }
    case 'days':
    default: {
      return diffMs / (1000 * 60 * 60 * 24);
    }
  }
};

const computeAggregate = (
  fn: string,
  subTableField: string,
  childField: string,
  data: Record<string, any>,
): null | number => {
  const rows = data[subTableField];
  if (!Array.isArray(rows) || rows.length === 0) {
    return fn === 'COUNT' ? 0 : null;
  }
  const values: number[] = [];
  for (const row of rows) {
    const v = row[childField];
    const num = typeof v === 'number' ? v : Number.parseFloat(v);
    if (!Number.isNaN(num)) {
      values.push(num);
    }
  }
  if (fn === 'COUNT') return values.length;
  if (values.length === 0) return null;
  switch (fn) {
    case 'AVG': {
      return values.reduce((a, b) => a + b, 0) / values.length;
    }
    case 'MAX': {
      return Math.max(...values);
    }
    case 'MIN': {
      return Math.min(...values);
    }
    case 'SUM': {
      return values.reduce((a, b) => a + b, 0);
    }
    default: {
      return null;
    }
  }
};

const parseFormula = (formula: string): string[] => {
  const regex = /\B\{([^}]+)\}/g;
  const fields: string[] = [];
  let match;

  while ((match = regex.exec(formula)) !== null) {
    if (match[1]) {
      fields.push(match[1]);
    }
  }

  return fields;
};

const evaluateFormula = (
  formula: string,
  data: Record<string, any>,
): null | number => {
  if (!formula || !data) return null;

  try {
    let expression = formula;

    // DATEDIFF{end, start, unit} -> 数值
    expression = expression.replaceAll(
      new RegExp(DATEDIFF_REGEX.source, 'g'),
      (_match, endField, startField, unit) => {
        const result = computeDateDiff(
          endField,
          startField,
          unit || 'days',
          data,
        );
        return result === null ? 'NaN' : result.toString();
      },
    );

    // SUM{subTable.field} -> 数值
    expression = expression.replaceAll(
      new RegExp(AGGREGATE_REGEX.source, 'g'),
      (_match, fn, path) => {
        const dotIdx = path.indexOf('.');
        if (dotIdx === -1) return 'NaN';
        const subTableField = path.slice(0, dotIdx);
        const childField = path.slice(dotIdx + 1);
        const result = computeAggregate(fn, subTableField, childField, data);
        return result === null ? 'NaN' : result.toString();
      },
    );

    // {field} -> 数值
    expression = expression.replaceAll(
      new RegExp(SIMPLE_FIELD_REGEX.source, 'g'),
      (_match, field) => {
        const value = data[field];
        const numValue =
          typeof value === 'number' ? value : Number.parseFloat(value);
        return Number.isNaN(numValue) ? 'NaN' : numValue.toString();
      },
    );

    if (expression.includes('NaN')) return null;

    expression = expression.replaceAll(/[^0-9+\-*/().]/g, '');

    if (!expression) return null;

    const result = new Function(`return ${expression}`)();

    if (
      typeof result === 'number' &&
      !Number.isNaN(result) &&
      Number.isFinite(result)
    ) {
      return result;
    }

    return null;
  } catch {
    console.warn('Formula evaluation failed:', formula);
    return null;
  }
};

// 收集公式中引用的所有依赖值（用于 watch 触发）
const collectDeps = (): any[] => {
  if (!props.formula || !props.formData) return [];
  const deps: any[] = [];
  const data = props.formData;
  let match;
  // DATEDIFF 引用
  const dateDiffRe = new RegExp(DATEDIFF_REGEX.source, 'g');
  while ((match = dateDiffRe.exec(props.formula)) !== null) {
    deps.push(data[(match[1] || '').trim()]);
    deps.push(data[(match[2] || '').trim()]);
  }
  // 聚合引用
  const aggRe = new RegExp(AGGREGATE_REGEX.source, 'g');
  while ((match = aggRe.exec(props.formula)) !== null) {
    const path = match[2] || '';
    const dotIdx = path.indexOf('.');
    if (dotIdx !== -1) {
      deps.push(JSON.stringify(data[path.slice(0, dotIdx)]));
    }
  }
  // 普通字段引用
  const simpleRe = new RegExp(SIMPLE_FIELD_REGEX.source, 'g');
  while ((match = simpleRe.exec(props.formula)) !== null) {
    deps.push(data[match[1] || '']);
  }
  return deps;
};

const calculatedValue = ref<null | number>(null);

const recalculate = () => {
  if (!props.formula || !props.formData) {
    calculatedValue.value = null;
    return;
  }
  const result = evaluateFormula(props.formula, props.formData);
  calculatedValue.value =
    result === null ? null : Number(result.toFixed(props.precision));
};

// 显式收集依赖并深度监听，确保子表单行内属性变化时重新计算
watch(
  () => collectDeps(),
  () => recalculate(),
  { immediate: true, deep: true },
);

const displayValue = computed(() => {
  if (calculatedValue.value !== null) {
    return calculatedValue.value.toFixed(props.precision);
  }
  return '';
});

const formulaDisplay = computed(() => {
  if (!props.formula) return '';

  let display = props.formula;

  // DATEDIFF 显示
  display = display.replaceAll(
    new RegExp(DATEDIFF_REGEX.source, 'g'),
    (_match, endField, startField, unit) => {
      const endVal = props.formData?.[endField.trim()];
      const startVal = props.formData?.[startField.trim()];
      const endStr = endVal ? `[${endVal}]` : endField.trim();
      const startStr = startVal ? `[${startVal}]` : startField.trim();
      return `DATEDIFF{${endStr}, ${startStr}, ${unit || 'days'}}`;
    },
  );

  // 普通字段显示
  const fields = parseFormula(display);
  for (const field of fields) {
    const value = props.formData?.[field];
    if (value !== undefined && value !== null && value !== '') {
      display = display.replace(`{${field}}`, `[${value}]`);
    }
  }

  return display;
});

watch(
  calculatedValue,
  (newVal) => {
    if (newVal !== null && newVal !== props.modelValue) {
      emit('update:modelValue', newVal);
      emit('change', newVal);
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="formula-input-wrapper">
    <ElInput
      :model-value="displayValue"
      :placeholder="placeholder"
      :disabled="true"
      readonly
      class="formula-input"
    >
      <template #suffix>
        <ElTooltip
          v-if="showFormula && formula"
          :content="`公式: ${formulaDisplay}`"
          placement="top"
        >
          <span
            class="cursor-help text-xs text-[var(--el-text-color-placeholder)]"
            >fx</span>
        </ElTooltip>
      </template>
    </ElInput>
  </div>
</template>

<style scoped>
.formula-input :deep(.el-input__inner) {
  cursor: default;
}
</style>
