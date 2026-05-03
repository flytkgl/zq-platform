<script setup lang="ts">
import { ref, watch } from 'vue';

import { Plus } from '@vben/icons';
import { $t } from '@vben/locales';
import { Delete } from '@element-plus/icons-vue';
import {
  ElButton,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
} from 'element-plus';

interface ConditionRule {
  field: string;
  operator: string;
  value: any;
  valueType?: 'string' | 'number' | 'boolean';
}

interface Props {
  modelValue?: string;
  fields: Array<{ label: string; value: string; type?: string }>;
  mode?: 'simple' | 'advanced';
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  mode: 'simple',
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const currentMode = ref<'simple' | 'advanced'>(props.mode);
const logic = ref<'AND' | 'OR'>('AND');
const rules = ref<ConditionRule[]>([]);
const advancedExpression = ref('');
const isUpdatingFromInternal = ref(false); // 标记是否是内部更新，防止循环

const operators = [
  { label: $t('form-design.attribute.conditionBuilder.operators.equals'), value: '===' },
  { label: $t('form-design.attribute.conditionBuilder.operators.notEquals'), value: '!==' },
  { label: $t('form-design.attribute.conditionBuilder.operators.greaterThan'), value: '>' },
  { label: $t('form-design.attribute.conditionBuilder.operators.greaterThanOrEqual'), value: '>=' },
  { label: $t('form-design.attribute.conditionBuilder.operators.lessThan'), value: '<' },
  { label: $t('form-design.attribute.conditionBuilder.operators.lessThanOrEqual'), value: '<=' },
  { label: $t('form-design.attribute.conditionBuilder.operators.contains'), value: 'includes' },
  { label: $t('form-design.attribute.conditionBuilder.operators.notContains'), value: '!includes' },
  { label: $t('form-design.attribute.conditionBuilder.operators.isEmpty'), value: 'empty' },
  { label: $t('form-design.attribute.conditionBuilder.operators.isNotEmpty'), value: '!empty' },
];

const booleanOptions = [
  { label: $t('common.yes'), value: true },
  { label: $t('common.no'), value: false },
];

// 初始化
watch(
  () => props.modelValue,
  (val) => {
    // 如果是内部更新触发的，跳过解析，避免覆盖用户输入
    if (isUpdatingFromInternal.value) {
      isUpdatingFromInternal.value = false;
      return;
    }

    if (!val) {
      // 如果没有值且是简单模式，初始化一个空规则
      if (currentMode.value === 'simple' && rules.value.length === 0) {
        rules.value = [{
          field: '',
          operator: '===',
          value: '',
        }];
      } else {
        rules.value = [];
      }
      advancedExpression.value = '';
      return;
    }

    // 尝试解析表达式
    advancedExpression.value = val;

    // 简单表达式解析（仅支持单个条件或简单的 && / || 组合）
    if (currentMode.value === 'simple') {
      parseExpression(val);
    }
  },
  { immediate: true },
);

// 解析表达式为规则（简单解析）
function parseExpression(expr: string) {
  if (!expr) {
    rules.value = [];
    return;
  }

  // 检测逻辑运算符
  if (expr.includes(' && ')) {
    logic.value = 'AND';
  } else if (expr.includes(' || ')) {
    logic.value = 'OR';
  }

  // 简单解析（仅支持基本格式）
  const parts = expr.split(logic.value === 'AND' ? ' && ' : ' || ');
  rules.value = parts
    .map((part) => {
      const trimmed = part.trim();
      // 匹配 model.field operator value 格式
      const match = trimmed.match(
        /model\.(\w+)\s*(===|!==|>=|<=|>|<)\s*(.+)/,
      );
      if (match && match[1] && match[2] && match[3]) {
        let value: any = match[3].trim();
        
        // 转换布尔值
        if (value === 'true') {
          value = true;
        } else if (value === 'false') {
          value = false;
        }
        // 去除引号（字符串）
        else if (
          (value.startsWith("'") && value.endsWith("'")) ||
          (value.startsWith('"') && value.endsWith('"'))
        ) {
          value = value.slice(1, -1);
        }
        // 转换数字
        else if (!Number.isNaN(Number(value))) {
          value = Number(value);
        }
        
        return {
          field: match[1],
          operator: match[2],
          value,
        };
      }
      return null;
    })
    .filter(Boolean) as ConditionRule[];

  if (rules.value.length === 0) {
    rules.value = [{ field: '', operator: '===', value: '' }];
  }
}

// 生成表达式
function generateExpression() {
  if (currentMode.value === 'advanced') {
    return advancedExpression.value;
  }

  if (rules.value.length === 0) {
    return '';
  }

  // 过滤出完整的规则（有字段、操作符，且需要值的情况下有值）
  const completeRules = rules.value.filter((rule) => {
    if (!rule.field || !rule.operator) return false;
    // 为空/不为空操作符不需要值
    if (['empty', '!empty'].includes(rule.operator)) return true;
    // 其他操作符需要值（注意：false、0 都是有效值）
    if (rule.value === null || rule.value === undefined || rule.value === '') {
      return false;
    }
    return true;
  });

  // 如果没有完整的规则，但有部分规则，不更新（保持原值）
  if (completeRules.length === 0 && rules.value.length > 0) {
    return props.modelValue || '';
  }

  const expressions = completeRules
    .map((rule) => {
      const fieldRef = `model.${rule.field}`;

      // 处理特殊操作符
      if (rule.operator === 'empty') {
        return `!${fieldRef} || ${fieldRef} === ''`;
      }
      if (rule.operator === '!empty') {
        return `${fieldRef} && ${fieldRef} !== ''`;
      }
      if (rule.operator === 'includes') {
        const val =
          typeof rule.value === 'string' ? `'${rule.value}'` : rule.value;
        return `${fieldRef} && ${fieldRef}.includes(${val})`;
      }
      if (rule.operator === '!includes') {
        const val =
          typeof rule.value === 'string' ? `'${rule.value}'` : rule.value;
        return `${fieldRef} && !${fieldRef}.includes(${val})`;
      }

      // 普通比较
      let val = rule.value;
      if (typeof val === 'string') {
        val = `'${val}'`;
      } else if (typeof val === 'boolean') {
        val = val.toString();
      }

      return `${fieldRef} ${rule.operator} ${val}`;
    });

  if (expressions.length === 0) {
    return '';
  }

  const connector = logic.value === 'AND' ? ' && ' : ' || ';
  return expressions.join(connector);
}

// 添加规则
function addRule() {
  rules.value.push({
    field: '',
    operator: '===',
    value: '',
  });
}

// 删除规则
function removeRule(index: number) {
  rules.value.splice(index, 1);
  updateExpression();
}

// 更新表达式
function updateExpression() {
  const expr = generateExpression();
  isUpdatingFromInternal.value = true;
  emit('update:modelValue', expr);
}

// 切换模式
function toggleMode() {
  if (currentMode.value === 'simple') {
    currentMode.value = 'advanced';
    advancedExpression.value = generateExpression();
  } else {
    currentMode.value = 'simple';
    parseExpression(advancedExpression.value);
  }
}

// 获取字段类型
function getFieldType(fieldName: string): string {
  const field = props.fields.find((f) => f.value === fieldName);
  if (!field?.type) return 'string';
  
  const componentType = field.type;
  
  // 根据组件类型映射到数据类型
  if (componentType === 'input-number' || componentType === 'slider' || componentType === 'rate') {
    return 'number';
  }
  if (componentType === 'switch') {
    return 'boolean';
  }
  
  return 'string';
}

// 监听规则变化 - 使用防抖避免频繁更新
let updateTimer: ReturnType<typeof setTimeout> | null = null;
watch([rules, logic], () => {
  if (updateTimer) {
    clearTimeout(updateTimer);
  }
  // 延迟更新，避免输入过程中频繁触发
  updateTimer = setTimeout(() => {
    updateExpression();
  }, 300);
}, { deep: true });

watch(advancedExpression, (val) => {
  if (currentMode.value === 'advanced') {
    isUpdatingFromInternal.value = true;
    emit('update:modelValue', val);
  }
});

// 获取值输入类型
const getValueInputType = (rule: ConditionRule) => {
  if (['empty', '!empty'].includes(rule.operator)) {
    return 'none';
  }
  const fieldType = getFieldType(rule.field);
  if (
    fieldType.includes('int') ||
    fieldType.includes('number') ||
    fieldType.includes('decimal')
  ) {
    return 'number';
  }
  if (fieldType.includes('bool')) {
    return 'boolean';
  }
  return 'string';
};
</script>

<template>
  <div class="condition-builder">
    <!-- 模式切换 -->
    <div class="mb-2 flex items-center justify-between pb-2 text-[11px] text-[var(--el-text-color-regular)]">
      <span>
        {{ currentMode === 'simple' ? $t('form-design.attribute.conditionBuilder.visualMode') : $t('form-design.attribute.conditionBuilder.advancedMode') }}
      </span>
      <ElButton
        type="primary"
        link
        style="font-size: smaller"
        @click="toggleMode"
      >
        {{ currentMode === 'simple' ? $t('form-design.attribute.conditionBuilder.switchToAdvanced') : $t('form-design.attribute.conditionBuilder.switchToVisual') }}
      </ElButton>
    </div>

    <!-- 简单模式 -->
    <div v-if="currentMode === 'simple'" class="space-y-3">
      <!-- 逻辑关系 -->
      <div v-if="rules.length > 1" class="flex items-center gap-2">
        <span class="text-[var(--el-text-color-secondary)]">
          {{ $t('form-design.attribute.conditionBuilder.satisfyCondition') }}
        </span>
        <ElSelect v-model="logic" size="small" style="width: 100px">
          <ElOption :label="$t('form-design.attribute.conditionBuilder.all')" value="AND" />
          <ElOption :label="$t('form-design.attribute.conditionBuilder.any')" value="OR" />
        </ElSelect>
      </div>

      <!-- 规则列表 -->
      <div
        v-for="(rule, index) in rules"
        :key="index"
        class="flex items-start gap-2"
      >
        <!-- 字段选择 -->
        <ElSelect
          v-model="rule.field"
          :placeholder="$t('form-design.attribute.conditionBuilder.selectField')"
          filterable
          size="small"
          style="width: 85px"

        >
          <ElOption
            v-for="field in fields"
            :key="field.value"
            :label="field.label"
            :value="field.value"
          />
        </ElSelect>

        <!-- 操作符 -->
        <ElSelect
          v-model="rule.operator"
          :placeholder="$t('form-design.attribute.conditionBuilder.operator')"
          size="small"
          class="flex-1"

        >
          <ElOption
            v-for="op in operators"
            :key="op.value"
            :label="op.label"
            :value="op.value"
          />
        </ElSelect>

        <!-- 值输入 -->
        <template v-if="getValueInputType(rule) === 'number'">
          <ElInputNumber
            v-model="rule.value"
            :placeholder="$t('form-design.attribute.conditionBuilder.value')"
            size="small"
            controls-position="right"
            class="flex-1"
          />
        </template>
        <template v-else-if="getValueInputType(rule) === 'boolean'">
          <ElSelect
            v-model="rule.value"
            :placeholder="$t('form-design.attribute.conditionBuilder.value')"
            size="small"
            class="flex-1"
          >
            <ElOption
              v-for="opt in booleanOptions"
              :key="String(opt.value)"
              :label="opt.label"
              :value="opt.value"
            />
          </ElSelect>
        </template>
        <template v-else-if="getValueInputType(rule) === 'string'">
          <ElInput
            v-model="rule.value"
            :placeholder="$t('form-design.attribute.conditionBuilder.value')"
            size="small"
            class="flex-1"
          />
        </template>

        <!-- 删除按钮 -->
        <ElButton
          link
          type="danger"
          size="small"
          :icon="Delete"
          @click="removeRule(index)"
        />
      </div>

      <!-- 添加规则按钮 -->
      <ElButton link type="primary" size="small" :icon="Plus" @click="addRule">
        {{ $t('form-design.attribute.conditionBuilder.addCondition') }}
      </ElButton>

      <!-- 预览表达式 -->
      <div
        v-if="rules.length > 0"
        class="mt-3 rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
      >
        <div class="mb-1 font-bold">{{ $t('form-design.attribute.conditionBuilder.generatedExpression') }}</div>
        <code class="break-all">{{ generateExpression() || $t('form-design.attribute.conditionBuilder.empty') }}</code>
      </div>
    </div>

    <!-- 高级模式 -->
    <div v-else>
      <ElInput
        v-model="advancedExpression"
        type="textarea"
        :rows="4"
        :placeholder="$t('form-design.attribute.conditionPlaceholder')"
      />
      <div class="mt-2 text-xs text-[var(--el-text-color-secondary)]">
        {{ $t('form-design.attribute.conditionTip') }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.condition-builder {
  width: 100%;
}
</style>
