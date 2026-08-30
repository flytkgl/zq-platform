<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';

import { ElButton, ElMessage, ElScrollbar, ElSwitch } from 'element-plus';

import {
  deleteFormWriteBackRuleApi,
  duplicateFormWriteBackRuleApi,
  getFormWriteBackRuleApi,
  updateFormWriteBackRuleApi,
  getFormWriteBackRulesApi,
  type FormWriteBackRuleListItem,
} from '#/api/online-dev/form-manager';

const props = defineProps<{
  formId?: string;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  create: [];
  edit: [id: string];
  refresh: [];
}>();

const loading = ref(false);
const rules = ref<FormWriteBackRuleListItem[]>([]);
const selectedId = ref<string>();

async function loadRules() {
  if (!props.formId) {
    rules.value = [];
    return;
  }
  loading.value = true;
  try {
    rules.value = await getFormWriteBackRulesApi(props.formId);
    if (
      selectedId.value &&
      !rules.value.some((item) => item.id === selectedId.value)
    ) {
      selectedId.value = undefined;
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '加载回写规则失败');
  } finally {
    loading.value = false;
  }
}

function createRule() {
  selectedId.value = undefined;
  emit('create');
}

function editRule(id: string) {
  selectedId.value = id;
  emit('edit', id);
}

async function toggleRule(
  rule: FormWriteBackRuleListItem,
  value: boolean | string | number,
) {
  if (!props.formId) return;
  const enabled = value === true;
  try {
    const detail = await getFormWriteBackRuleApi(props.formId, rule.id);
    await updateFormWriteBackRuleApi(props.formId, rule.id, {
      ...detail,
      enabled,
    });
    rule.enabled = enabled;
  } catch (error: any) {
    rule.enabled = !enabled;
    ElMessage.error(error?.message || '更新规则状态失败');
  }
}

async function deleteRule(rule: FormWriteBackRuleListItem) {
  if (!props.formId) return;
  try {
    await deleteFormWriteBackRuleApi(props.formId, rule.id);
    ElMessage.success('回写规则已删除');
    if (selectedId.value === rule.id) selectedId.value = undefined;
    await loadRules();
    emit('refresh');
  } catch (error: any) {
    ElMessage.error(error?.message || '删除回写规则失败');
  }
}

async function duplicateRule(rule: FormWriteBackRuleListItem) {
  if (!props.formId) return;
  try {
    const copied = await duplicateFormWriteBackRuleApi(props.formId, rule.id);
    await loadRules();
    editRule(copied.id!);
    ElMessage.success('回写规则已复制');
  } catch (error: any) {
    ElMessage.error(error?.message || '复制回写规则失败');
  }
}

watch(() => props.formId, loadRules, { immediate: true });
onMounted(loadRules);

defineExpose({ loadRules });
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="flex items-center justify-between border-b p-2">
      <span class="text-xs font-medium">回写规则</span>
      <ElButton
        size="small"
        type="primary"
        :disabled="readonly || !formId"
        @click="createRule"
      >
        新增
      </ElButton>
    </div>
    <div
      class="grid grid-cols-[minmax(0,1fr)_56px] border-b px-2 py-2 text-xs text-[var(--el-text-color-secondary)]"
    >
      <span>规则名称</span>
      <span>启用状态</span>
    </div>
    <ElScrollbar v-loading="loading" class="min-h-0 flex-1">
      <div
        v-for="rule in rules"
        :key="rule.id"
        class="group grid cursor-pointer grid-cols-[minmax(0,1fr)_56px] items-center border-b px-2 py-2 text-xs hover:bg-[var(--el-fill-color-light)]"
        :class="
          selectedId === rule.id
            ? 'bg-[var(--el-color-primary-light-9)] text-[var(--el-color-primary)]'
            : ''
        "
        @click="editRule(rule.id)"
      >
        <span class="truncate pr-1" :title="rule.name">{{ rule.name }}</span>
        <ElSwitch
          :model-value="rule.enabled"
          size="small"
          :disabled="readonly"
          @click.stop
          @update:model-value="toggleRule(rule, $event)"
        />
        <div class="col-span-2 hidden gap-1 pt-1 group-hover:flex">
          <ElButton
            link
            size="small"
            :disabled="readonly"
            @click.stop="duplicateRule(rule)"
            >复制</ElButton
          >
          <ElButton
            link
            size="small"
            type="danger"
            :disabled="readonly"
            @click.stop="deleteRule(rule)"
            >删除</ElButton
          >
        </div>
      </div>
      <div
        v-if="!loading && rules.length === 0"
        class="p-6 text-center text-xs text-[var(--el-text-color-placeholder)]"
      >
        暂无回写规则
      </div>
    </ElScrollbar>
  </div>
</template>
