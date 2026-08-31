<script setup lang="ts">
import type { TableConfig } from '#/views/online-dev/form-manager/modules/data-source-config.vue';
import type {
  FormWriteBackRule,
  PublishedFormSimple,
  WriteBackEvent,
} from '#/api/online-dev/form-manager';
import type { ShallowRef } from 'vue';

import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';

import {
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElSelect,
  ElSwitch,
} from 'element-plus';

import {
  createFormWriteBackRuleApi,
  getFormDetailApi,
  getFormWriteBackRuleApi,
  getPublishedFormsSimpleApi,
  updateFormWriteBackRuleApi,
} from '#/api/online-dev/form-manager';

import WriteBackFieldSelect from './WriteBackFieldSelect.vue';

interface WriteBackField {
  name: string;
  comment?: string;
  label?: string;
  type?: string;
}

interface ExpressionToken {
  label: string;
  expression: string;
}

const props = defineProps<{
  formId?: string;
  sourceFormName?: string;
  tableConfigs: TableConfig[];
  ruleId?: string;
  readonly?: boolean;
}>();

const emit = defineEmits<{ saved: []; cancel: [] }>();

const eventOptions: Array<{ label: string; value: WriteBackEvent }> = [
  { label: '新增前', value: 'before_create' },
  { label: '新增后', value: 'after_create' },
  { label: '保存前', value: 'before_update' },
  { label: '保存后', value: 'after_update' },
  { label: '删除前', value: 'before_delete' },
  { label: '删除后', value: 'after_delete' },
  { label: '审核前', value: 'before_approve' },
  { label: '审核后', value: 'after_approve' },
  { label: '反审前', value: 'before_unapprove' },
  { label: '反审后', value: 'after_unapprove' },
];
const forms = ref<PublishedFormSimple[]>([]);
const targetTables = ref<
  Array<{ key: string; label: string; fields: WriteBackField[] }>
>(
  [],
);
const saving = ref(false);
const loading = ref(false);
const customName = ref(false);
const expressionInputRef = ref<{
  textarea?: ShallowRef<HTMLTextAreaElement | undefined>;
}>();
const expressionSelection = ref({ start: 0, end: 0 });

const emptyRule = (): FormWriteBackRule => ({
  target_form_id: '',
  name: '',
  is_name_auto: true,
  enabled: true,
  source_table_key: 'main',
  target_table_key: 'main',
  target_field: '',
  trigger_events: [],
  value_mode: 'custom',
  custom_expression: '',
  writeback_operator: 'add',
  execute_conditions: [],
  value_filter_conditions: [],
  match_conditions: [],
  missing_target_policy: 'error',
  remark: '',
});
const rule = reactive<FormWriteBackRule>(emptyRule());

const sourceTables = computed(() =>
  props.tableConfigs.map((item: any) => ({
    key: item.type === 'main' ? 'main' : item.tableName,
    label:
      item.type === 'main'
        ? `${item.tableName}（主表）`
        : item.alias || item.tableName,
    fields: (item.fields || []) as WriteBackField[],
  })),
);
const sourceTable = computed(() =>
  sourceTables.value.find((item) => item.key === rule.source_table_key),
);
const targetTable = computed(() =>
  targetTables.value.find((item) => item.key === rule.target_table_key),
);
const sourceFields = computed<WriteBackField[]>(
  () => sourceTable.value?.fields || [],
);
const targetFields = computed<WriteBackField[]>(
  () => targetTable.value?.fields || [],
);
const numericSourceFields = computed(() =>
  sourceFields.value.filter((field) => isNumericField(field)),
);
const autoName = computed(() => {
  const labels = rule.trigger_events
    .map(
      (event) =>
        eventOptions.find((item) => item.value === event)?.label || event,
    )
    .join(',');
  return `[${labels}]更新表[${targetTable.value?.label || '目标表'}]的[${targetFields.value.find((item: any) => item.name === rule.target_field)?.comment || rule.target_field || '目标字段'}]字段`;
});
const displayName = computed({
  get: () => (rule.is_name_auto ? autoName.value : rule.name),
  set: (value: string) => {
    rule.name = value;
  },
});

function fieldsOf(table: any) {
  return (table?.fields || []).filter((field: WriteBackField) => field.name);
}

function getFieldLabel(field: WriteBackField) {
  return field.comment?.trim() || field.label?.trim() || field.name;
}

function getFieldType(field: WriteBackField) {
  return field.type?.trim().toLowerCase() || '';
}

function isNumericField(field: WriteBackField) {
  return /int|number|decimal|numeric|float|double|real|money/.test(
    getFieldType(field),
  );
}

function createFieldToken(scope: 'newData' | 'oldData', field: WriteBackField) {
  return {
    label: `${getFieldLabel(field)} · ${field.name}`,
    expression: `${scope}.${field.name}`,
  } satisfies ExpressionToken;
}

const newDataTokens = computed<ExpressionToken[]>(() =>
  sourceFields.value.map((field) => createFieldToken('newData', field)),
);
const oldDataTokens = computed<ExpressionToken[]>(() =>
  sourceFields.value.map((field) => createFieldToken('oldData', field)),
);

function createAggregateTokens(scope: 'newRows' | 'oldRows') {
  return [
    {
      label: '记录数',
      expression: `count(${scope})`,
    },
    ...numericSourceFields.value.flatMap((field) =>
      ['sum', 'max', 'min', 'avg'].map((fn) => ({
        label: `${fn} · ${getFieldLabel(field)} · ${field.name}`,
        expression: `${fn}(${scope}.${field.name})`,
      })),
    ),
  ] satisfies ExpressionToken[];
}

const newRowsTokens = computed(() => createAggregateTokens('newRows'));
const oldRowsTokens = computed(() => createAggregateTokens('oldRows'));

function normalizeTables(form: any) {
  const configs = Array.isArray(form.form_config?.tableConfigs)
    ? form.form_config.tableConfigs
    : [];
  const mainConfig = configs.find((item: any) => item.type === 'main');
  const mainFields = fieldsOf(mainConfig).length
    ? fieldsOf(mainConfig)
    : (form.fields || []).map((field: any) => ({
        name: field.field,
        comment: field.label || field.field,
        type: field.type || 'VARCHAR',
      }));
  const subTableNames = [
    ...(form.sub_tables || []).map((item: any) => item.table_name),
    ...configs
      .filter((item: any) => item.type === 'sub')
      .map((item: any) => item.tableName),
  ].filter(
    (value: any, index: number, values: any[]) =>
      value && values.indexOf(value) === index,
  );
  targetTables.value = [
    {
      key: 'main',
      label: `${mainConfig?.tableName || form.main_table || 'main'}（主表）`,
      fields: mainFields,
    },
    ...subTableNames.map((tableName: string) => {
      const relation = (form.sub_tables || []).find(
        (item: any) => item.table_name === tableName,
      );
      const config = configs.find(
        (item: any) => item.type === 'sub' && item.tableName === tableName,
      );
      return {
        key: tableName,
        label: relation?.alias || config?.alias || tableName,
        fields: fieldsOf(config),
      };
    }),
  ];
  if (!targetTables.value.some((item) => item.key === rule.target_table_key))
    rule.target_table_key = 'main';
  syncTargetField();
}

function syncTargetField() {
  // 目标表单详情是异步加载的，列表尚未加载完成时不能把已保存的字段误清空。
  if (!targetTables.value.length) return;
  if (
    !targetFields.value.some((item: any) => item.name === rule.target_field)
  ) {
    rule.target_field = '';
  }
}

async function loadTargetForm() {
  if (!rule.target_form_id) {
    targetTables.value = [];
    return;
  }
  try {
    normalizeTables(await getFormDetailApi(rule.target_form_id));
  } catch (error: any) {
    ElMessage.error(error?.message || '加载目标表单失败');
  }
}

async function loadRule() {
  Object.assign(rule, emptyRule());
  if (!props.formId || !props.ruleId) return;
  loading.value = true;
  try {
    const saved = await getFormWriteBackRuleApi(props.formId, props.ruleId);
    Object.assign(rule, saved);
    customName.value = !saved.is_name_auto;
    await loadTargetForm();
  } catch (error: any) {
    ElMessage.error(error?.message || '加载回写规则失败');
  } finally {
    loading.value = false;
  }
}

async function loadForms() {
  try {
    // 表单设计器需要选择其他应用下的目标表单；后端仍会校验同库约束。
    forms.value = await getPublishedFormsSimpleApi(undefined, true);
  } catch {
    /* 表单下拉在保存时由后端再次校验 */
  }
}

function addMatch() {
  rule.match_conditions.push({
    source_field: sourceFields.value[0]?.name,
    target_field: targetFields.value[0]?.name || '',
  });
}
function removeMatch(index: number) {
  rule.match_conditions.splice(index, 1);
}
function addCondition(
  target: 'execute_conditions' | 'value_filter_conditions',
) {
  rule[target].push({
    field: sourceFields.value[0]?.name || '',
    operator: 'eq',
    value: '',
  });
}
function removeCondition(
  target: 'execute_conditions' | 'value_filter_conditions',
  index: number,
) {
  rule[target].splice(index, 1);
}
function captureExpressionSelection() {
  const textarea = expressionInputRef.value?.textarea?.value;
  if (!textarea) return;
  expressionSelection.value = {
    start: textarea.selectionStart ?? rule.custom_expression.length,
    end: textarea.selectionEnd ?? rule.custom_expression.length,
  };
}

function insertExpression(token: ExpressionToken) {
  const expression = rule.custom_expression || '';
  const textarea = expressionInputRef.value?.textarea?.value;
  const hasSelection =
    textarea && document.activeElement === textarea
      ? expressionSelection.value
      : { start: expression.length, end: expression.length };
  const before = expression.slice(0, hasSelection.start);
  const after = expression.slice(hasSelection.end);
  const prefix = before && !/\s$/.test(before) ? ' ' : '';
  const suffix = after && !/^\s/.test(after) ? ' ' : '';
  const inserted = `${prefix}${token.expression}${suffix}`;
  const cursor = before.length + inserted.length - suffix.length;

  rule.custom_expression = `${before}${inserted}${after}`;
  expressionSelection.value = { start: cursor, end: cursor };

  nextTick(() => {
    const input = expressionInputRef.value?.textarea?.value;
    if (!input || props.readonly) return;
    input.focus();
    input.setSelectionRange(cursor, cursor);
  });
}

function previewExpression(expression: string) {
  const sample = expression
    .replace(/\bcount\((?:newRows|oldRows)\)/g, '2')
    .replace(
      /\b(?:sum|max|min|avg)\((?:newRows|oldRows)\.[A-Za-z_]\w*\)/g,
      (token) =>
        token.includes('sum')
          ? '30'
          : token.includes('avg')
            ? '15'
            : token.includes('min')
              ? '10'
              : '20',
    )
    .replace(/\bnewData\.[A-Za-z_]\w*/g, '10')
    .replace(/\boldData\.[A-Za-z_]\w*/g, '5');
  return `示例代入：${sample}`;
}

const expressionPreview = computed(() =>
  rule.value_mode === 'custom' && rule.custom_expression
    ? previewExpression(rule.custom_expression)
    : '',
);

function validateExpression() {
  if (!rule.custom_expression?.trim()) {
    ElMessage.warning('请输入自定义表达式');
    return false;
  }
  if (!rule.trigger_events.length) {
    ElMessage.warning('至少选择一个触发动作');
    return false;
  }
  if (
    !rule.source_table_key ||
    !rule.target_form_id ||
    !rule.target_table_key ||
    !rule.target_field
  ) {
    ElMessage.warning('请完整配置源表、目标表单、目标表和目标字段');
    return false;
  }
  return true;
}

async function save() {
  if (props.readonly || !validateExpression() || !props.formId) return;
  saving.value = true;
  try {
    rule.is_name_auto = !customName.value;
    if (rule.is_name_auto) rule.name = autoName.value;
    if (props.ruleId)
      await updateFormWriteBackRuleApi(props.formId, props.ruleId, { ...rule });
    else await createFormWriteBackRuleApi(props.formId, { ...rule });
    ElMessage.success('回写规则保存成功');
    emit('saved');
  } catch (error: any) {
    ElMessage.error(error?.message || '保存回写规则失败');
  } finally {
    saving.value = false;
  }
}

watch(() => rule.target_form_id, loadTargetForm);
watch(() => rule.target_table_key, syncTargetField);
watch(
  () => rule.source_table_key,
  () => {
    const firstField = sourceFields.value[0]?.name || '';
    for (const condition of [
      ...rule.execute_conditions,
      ...rule.value_filter_conditions,
    ]) {
      if (
        !sourceFields.value.some((field: any) => field.name === condition.field)
      ) {
        condition.field = firstField;
      }
    }
    for (const condition of rule.match_conditions) {
      if (
        condition.source_field &&
        !sourceFields.value.some(
          (field: any) => field.name === condition.source_field,
        )
      ) {
        condition.source_field = firstField;
      }
    }
  },
);
watch(
  () => customName.value,
  (enabled) => {
    rule.is_name_auto = !enabled;
    if (!enabled) rule.name = autoName.value;
  },
);
watch(
  () => autoName.value,
  (value) => {
    if (rule.is_name_auto) rule.name = value;
  },
);
watch(() => [props.ruleId, props.formId], loadRule, { immediate: true });
onMounted(loadForms);
</script>

<template>
  <div v-loading="loading" class="h-full overflow-y-auto p-5">
    <div class="mb-4 flex items-center justify-between border-b pb-3">
      <h3 class="text-base font-medium">
        {{ ruleId ? '编辑回写规则' : '新增回写规则' }}
      </h3>
      <div class="flex gap-2">
        <ElButton @click="emit('cancel')">取消</ElButton
        ><ElButton
          type="primary"
          :loading="saving"
          :disabled="readonly"
          @click="save"
          >保存</ElButton
        >
      </div>
    </div>
    <ElForm label-position="top" class="grid grid-cols-2 gap-x-5">
      <ElFormItem label="规则名称" class="col-span-2">
        <div class="flex w-full items-center gap-3">
          <ElInput
            v-model="displayName"
            :disabled="rule.is_name_auto || readonly"
          />
          <ElCheckbox v-model="customName" :disabled="readonly"
            >自定义名称</ElCheckbox
          >
          <ElSwitch v-model="rule.enabled" :disabled="readonly" />
          <span class="whitespace-nowrap text-xs">启用</span>
        </div>
      </ElFormItem>
      <ElFormItem label="触发动作" class="col-span-2">
        <ElCheckboxGroup v-model="rule.trigger_events"
          ><ElCheckbox
            v-for="item in eventOptions"
            :key="item.value"
            :label="item.value"
            :disabled="readonly"
            >{{ item.label }}</ElCheckbox
          ></ElCheckboxGroup
        >
        <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
          所有选中的动作共用当前这一套条件、表达式和回写方式。
        </div>
      </ElFormItem>
      <ElFormItem label="源表单"
        ><ElInput
          :model-value="sourceFormName || '当前表单'"
          disabled
          class="w-full"
        />
      </ElFormItem>
      <ElFormItem label="源表"
        ><ElSelect
          v-model="rule.source_table_key"
          class="w-full"
          :disabled="readonly"
          ><ElOption
            v-for="item in sourceTables"
            :key="item.key"
            :label="item.label"
            :value="item.key" /></ElSelect
      ></ElFormItem>
      <ElFormItem label="目标表单"
        ><ElSelect
          v-model="rule.target_form_id"
          filterable
          class="w-full"
          :disabled="readonly"
          ><ElOption
            v-for="form in forms.filter((item) => item.id !== formId)"
            :key="form.id"
            :label="form.name"
            :value="form.id" /></ElSelect
      ></ElFormItem>
      <ElFormItem label="目标表"
        ><ElSelect
          v-model="rule.target_table_key"
          class="w-full"
          :disabled="readonly"
          ><ElOption
            v-for="item in targetTables"
            :key="item.key"
            :label="item.label"
            :value="item.key" /></ElSelect
      ></ElFormItem>
      <ElFormItem label="目标字段"
        ><WriteBackFieldSelect
          v-model="rule.target_field"
          :fields="targetFields"
          :disabled="readonly"
          clearable
        />
      ></ElFormItem>
      <ElFormItem label="取值方式"
        ><ElSelect v-model="rule.value_mode" class="w-full" disabled
          ><ElOption label="自定义" value="custom" /></ElSelect
      ></ElFormItem>
      <ElFormItem label="回写方式"
        ><ElSelect
          v-model="rule.writeback_operator"
          class="w-full"
          :disabled="readonly"
          ><ElOption label="等于" value="set" /><ElOption
            label="加"
            value="add" /><ElOption label="减" value="subtract" /></ElSelect
      ></ElFormItem>
      <ElFormItem label="自定义表达式" class="col-span-2"
        ><div class="expression-editor w-full space-y-3">
          <ElInput
            ref="expressionInputRef"
            v-model="rule.custom_expression"
            type="textarea"
            :rows="4"
            :disabled="readonly"
            placeholder="例如：newData.quantity - oldData.quantity"
            @click="captureExpressionSelection"
            @focus="captureExpressionSelection"
            @keyup="captureExpressionSelection"
            @select="captureExpressionSelection"
            @input="captureExpressionSelection"
          />

          <div
            class="rounded border border-[var(--el-border-color-light)] bg-[var(--el-fill-color-lighter)] p-3"
          >
            <div class="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1">
              <span class="text-sm font-medium text-[var(--el-text-color-primary)]"
                >快捷插入</span
              >
              <span class="text-xs text-[var(--el-text-color-secondary)]"
                >点击字段即可插入完整表达式，支持在光标位置插入。</span
              >
            </div>

            <div class="space-y-3">
              <div>
                <div class="mb-1 text-xs font-medium text-[var(--el-text-color-regular)]">
                  单条数据字段
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <ElButton
                    v-for="token in newDataTokens"
                    :key="token.expression"
                    text
                    size="small"
                    class="!m-0 !h-auto !justify-start !px-2 !py-1"
                    :title="token.expression"
                    :disabled="readonly"
                    @click="insertExpression(token)"
                  >
                    <span class="mr-1 truncate">{{ token.label }}</span>
                    <code class="text-xs text-[var(--el-color-primary)]">newData</code>
                  </ElButton>
                  <span
                    v-if="!newDataTokens.length"
                    class="text-xs text-[var(--el-text-color-placeholder)]"
                    >暂无可用字段</span
                  >
                </div>
              </div>

              <div>
                <div class="mb-1 text-xs font-medium text-[var(--el-text-color-regular)]">
                  原始数据字段
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <ElButton
                    v-for="token in oldDataTokens"
                    :key="token.expression"
                    text
                    size="small"
                    class="!m-0 !h-auto !justify-start !px-2 !py-1"
                    :title="token.expression"
                    :disabled="readonly"
                    @click="insertExpression(token)"
                  >
                    <span class="mr-1 truncate">{{ token.label }}</span>
                    <code class="text-xs text-[var(--el-color-primary)]">oldData</code>
                  </ElButton>
                  <span
                    v-if="!oldDataTokens.length"
                    class="text-xs text-[var(--el-text-color-placeholder)]"
                    >暂无可用字段</span
                  >
                </div>
              </div>

              <div class="grid gap-3 md:grid-cols-2">
                <div>
                  <div class="mb-1 text-xs font-medium text-[var(--el-text-color-regular)]">
                    新增明细汇总
                  </div>
                  <div class="flex flex-wrap gap-1.5">
                    <ElButton
                      v-for="token in newRowsTokens"
                      :key="token.expression"
                      text
                      size="small"
                      class="!m-0 !h-auto !justify-start !px-2 !py-1"
                      :title="token.expression"
                      :disabled="readonly"
                      @click="insertExpression(token)"
                    >
                      {{ token.label }}
                    </ElButton>
                  </div>
                </div>
                <div>
                  <div class="mb-1 text-xs font-medium text-[var(--el-text-color-regular)]">
                    历史明细汇总
                  </div>
                  <div class="flex flex-wrap gap-1.5">
                    <ElButton
                      v-for="token in oldRowsTokens"
                      :key="token.expression"
                      text
                      size="small"
                      class="!m-0 !h-auto !justify-start !px-2 !py-1"
                      :title="token.expression"
                      :disabled="readonly"
                      @click="insertExpression(token)"
                    >
                      {{ token.label }}
                    </ElButton>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            class="flex items-start gap-2 rounded border border-[var(--el-color-info-light-5)] bg-[var(--el-color-info-light-9)] px-3 py-2 text-xs leading-5 text-[var(--el-text-color-secondary)]"
          >
            <span class="shrink-0 font-medium text-[var(--el-color-info)]">说明</span>
            <span
              >支持字段访问、数字运算和 count/sum/max/min/avg；仅聚合数值字段，保存时后端会进行安全 AST 校验。</span
            >
          </div>

          <div
            class="rounded border border-[var(--el-border-color-light)] bg-[var(--el-fill-color-light)] px-3 py-2 text-xs text-[var(--el-text-color-secondary)]"
          >
            <div class="mb-1 font-medium text-[var(--el-text-color-regular)]">
              表达式预览
            </div>
            <code v-if="expressionPreview" class="block break-all whitespace-pre-wrap leading-5"
              >{{ expressionPreview }}（示例字段按新值 10、旧值 5 代入）</code
            >
            <span v-else class="text-[var(--el-text-color-placeholder)]"
              >输入表达式后显示示例结果</span
            >
          </div>
        </div>
      </ElFormItem>
      <ElFormItem label="关联条件" class="col-span-2"
        ><div class="w-full rounded border p-3">
          <div
            v-for="(condition, index) in rule.match_conditions"
            :key="index"
            class="condition-row grid grid-cols-[minmax(220px,1fr)_120px_minmax(220px,1fr)_48px] items-center gap-2"
          >
            <WriteBackFieldSelect
              v-model="condition.source_field"
              :fields="sourceFields"
              :disabled="readonly"
            />
            <span class="pt-2">=</span
            ><WriteBackFieldSelect
              v-model="condition.target_field"
              :fields="targetFields"
              :disabled="readonly"
            />
            <ElButton
              link
              type="danger"
              :disabled="readonly"
              @click="removeMatch(index)"
              >删除</ElButton
            >
          </div>
          <ElButton link type="primary" :disabled="readonly" @click="addMatch"
            >+ 添加关联条件</ElButton
          >
        </div></ElFormItem
      >
      <ElFormItem label="执行条件" class="col-span-2"
        ><div class="w-full rounded border p-3">
          <div
            v-for="(condition, index) in rule.execute_conditions"
            :key="index"
            class="condition-row grid grid-cols-[minmax(220px,1fr)_120px_minmax(220px,1fr)_48px] items-center gap-2"
          >
            <WriteBackFieldSelect
              v-model="condition.field"
              :fields="sourceFields"
              :disabled="readonly"
            />
            <ElSelect
              v-model="condition.operator"
              class="w-full min-w-0"
              :disabled="readonly"
              ><ElOption label="等于" value="eq" /><ElOption
                label="不等于"
                value="ne" /><ElOption label="大于" value="gt" /><ElOption
                label="大于等于"
                value="gte" /><ElOption label="小于" value="lt" /><ElOption
                label="小于等于"
                value="lte" /><ElOption
                label="不为空"
                value="not_empty" /></ElSelect
            ><ElInput
              v-model="condition.value"
              class="w-full min-w-0"
              :disabled="readonly"
              placeholder="条件值"
            /><ElButton
              link
              type="danger"
              :disabled="readonly"
              @click="removeCondition('execute_conditions', index)"
              >删除</ElButton
            >
          </div>
          <ElButton
            link
            type="primary"
            :disabled="readonly"
            @click="addCondition('execute_conditions')"
            >+ 添加条件</ElButton
          >
        </div></ElFormItem
      >
      <ElFormItem label="汇总过滤条件" class="col-span-2"
        ><div class="w-full rounded border p-3">
          <div
            v-for="(condition, index) in rule.value_filter_conditions"
            :key="index"
            class="condition-row grid grid-cols-[minmax(220px,1fr)_120px_minmax(220px,1fr)_48px] items-center gap-2"
          >
            <WriteBackFieldSelect
              v-model="condition.field"
              :fields="sourceFields"
              :disabled="readonly"
            />
            <ElSelect
              v-model="condition.operator"
              class="w-full min-w-0"
              :disabled="readonly"
              ><ElOption label="等于" value="eq" /><ElOption
                label="不等于"
                value="ne" /><ElOption label="大于" value="gt" /><ElOption
                label="大于等于"
                value="gte" /><ElOption label="小于" value="lt" /><ElOption
                label="小于等于"
                value="lte" /><ElOption
                label="不为空"
                value="not_empty" /></ElSelect
            ><ElInput
              v-model="condition.value"
              class="w-full min-w-0"
              :disabled="readonly"
              placeholder="过滤值"
            /><ElButton
              link
              type="danger"
              :disabled="readonly"
              @click="removeCondition('value_filter_conditions', index)"
              >删除</ElButton
            >
          </div>
          <ElButton
            link
            type="primary"
            :disabled="readonly"
            @click="addCondition('value_filter_conditions')"
            >+ 添加条件</ElButton
          >
        </div></ElFormItem
      >
      <ElFormItem label="目标不存在处理方式"
        ><ElSelect v-model="rule.missing_target_policy" disabled class="w-full"
          ><ElOption label="报错并回滚" value="error" /></ElSelect
      ></ElFormItem>
      <ElFormItem label="备注"
        ><ElInput v-model="rule.remark" :disabled="readonly"
      /></ElFormItem>
    </ElForm>
  </div>
</template>

<style scoped>
.condition-row > :deep(.el-select),
.condition-row > :deep(.el-input) {
  min-width: 0;
  width: 100%;
}

@media (max-width: 900px) {
  .condition-row {
    grid-template-columns: minmax(140px, 1fr) 108px minmax(140px, 1fr) 44px;
  }
}
</style>
