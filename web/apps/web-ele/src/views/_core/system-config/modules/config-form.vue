<script lang="ts" setup>
import { computed, ref, watch } from 'vue';

import { EyeOff, Info } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElSelect,
  ElSwitch,
  ElTooltip,
} from 'element-plus';

import { updateGroupConfigApi } from '#/api/core/system-config';

defineOptions({ name: 'SystemConfigForm' });

const props = defineProps<{
  configData: Record<string, any>;
  group: string;
  loading: boolean;
}>();

const emit = defineEmits<{
  saved: [];
}>();

const SECRET_KEYS = new Set([
  'aliyun_access_key_secret',
  'app_key',
  'app_secret',
  'client_secret',
  'smtp_password',
  'tencent_secret_key',
  'webhook_secret',
]);

const BOOLEAN_KEYS = new Set(['smtp_use_tls']);

const SELECT_OPTIONS: Record<
  string,
  Array<{ label: string; value: string }>
> = {
  provider: [
    { label: $t('system-config.fields.providerAliyun'), value: 'aliyun' },
    { label: $t('system-config.fields.providerTencent'), value: 'tencent' },
  ],
};

const formData = ref<Record<string, any>>({});
const saving = ref(false);

const fields = computed(() => {
  return Object.keys(props.configData);
});

const visibleFields = computed(() => {
  if (props.group !== 'notify_sms') return fields.value;
  const provider = formData.value.provider || '';
  const hidePrefix =
    provider === 'aliyun'
      ? 'tencent_'
      : (provider === 'tencent'
        ? 'aliyun_'
        : '');
  if (!hidePrefix) return fields.value;
  return fields.value.filter((key) => !key.startsWith(hidePrefix));
});

function isSelect(key: string): boolean {
  return key in SELECT_OPTIONS;
}

function isSecret(key: string): boolean {
  return SECRET_KEYS.has(key);
}

function isBoolean(key: string): boolean {
  return BOOLEAN_KEYS.has(key);
}

function isMasked(value: any): boolean {
  return typeof value === 'string' && value.includes('***');
}

function getFieldLabel(key: string): string {
  return $t(`system-config.fields.${key}`) || key;
}

function loadFormData() {
  const data: Record<string, any> = {};
  for (const key of Object.keys(props.configData)) {
    const val = props.configData[key];
    data[key] = isBoolean(key) ? val === 'true' || val === true : (val ?? '');
  }
  formData.value = data;
}

watch(
  () => [props.group, props.configData],
  () => {
    loadFormData();
  },
  { immediate: true, deep: true },
);

async function save() {
  saving.value = true;
  try {
    const configs: Record<string, null | string> = {};
    for (const key of fields.value) {
      const val = formData.value[key];
      if (isBoolean(key)) {
        configs[key] = String(val);
      } else if (isSecret(key) && isMasked(val)) {
        configs[key] = val;
      } else {
        configs[key] = val === '' ? null : String(val);
      }
    }
    await updateGroupConfigApi(props.group, { configs });
    ElMessage.success($t('system-config.saveSuccess'));
    emit('saved');
  } catch {
    ElMessage.error($t('system-config.saveError'));
  } finally {
    saving.value = false;
  }
}

defineExpose({ save });
</script>

<template>
  <div v-loading="loading" class="p-6">
    <ElForm label-position="top" class="max-w-[600px]">
      <template v-for="key in visibleFields" :key="key">
        <!-- Select field -->
        <ElFormItem v-if="isSelect(key)" :label="getFieldLabel(key)">
          <ElSelect
            v-model="formData[key]"
            :placeholder="getFieldLabel(key)"
            clearable
          >
            <ElOption
              v-for="opt in SELECT_OPTIONS[key]"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </ElSelect>
        </ElFormItem>

        <!-- Boolean field -->
        <ElFormItem v-else-if="isBoolean(key)" :label="getFieldLabel(key)">
          <ElSwitch v-model="formData[key]" />
        </ElFormItem>

        <!-- Secret field -->
        <ElFormItem v-else-if="isSecret(key)" :label="getFieldLabel(key)">
          <ElInput
            v-model="formData[key]"
            show-password
            :placeholder="getFieldLabel(key)"
            clearable
          >
            <template #suffix>
              <ElTooltip
                v-if="isMasked(formData[key])"
                :content="$t('system-config.secretTip')"
                placement="top"
              >
                <EyeOff
                  class="size-4 cursor-help"
                  style="color: var(--el-text-color-placeholder)"
                />
              </ElTooltip>
            </template>
          </ElInput>
        </ElFormItem>

        <!-- Normal field -->
        <ElFormItem v-else :label="getFieldLabel(key)">
          <ElInput
            v-model="formData[key]"
            :placeholder="getFieldLabel(key)"
            clearable
          />
        </ElFormItem>
      </template>

      <div
        v-if="fields.length === 0"
        class="flex items-center gap-2 py-8"
        style="color: var(--el-text-color-secondary)"
      >
        <Info class="size-4" />
        <span>{{ $t('common.noData') || 'No data' }}</span>
      </div>
    </ElForm>
  </div>
</template>
