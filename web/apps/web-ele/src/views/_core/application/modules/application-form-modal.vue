<script lang="ts" setup>
import type {
  ApplicationCreateInput,
  ApplicationListItem,
  ApplicationUpdateInput,
  AppType,
} from '#/api/core/application';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElCol,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElRow,
  ElSelect,
} from 'element-plus';

import {
  checkApplicationUniqueApi,
  createApplicationApi,
  updateApplicationApi,
} from '#/api/core/application';
import ZqDialog from '#/components/zq-dialog/zq-dialog.vue';
import { ZqIconPicker } from '#/components/zq-form/zq-icon-picker';
import ZqMenuSelector from '#/components/zq-form/zq-menu-selector/zq-menu-selector.vue';

defineOptions({ name: 'ApplicationFormModal' });

const props = defineProps<{
  application?: ApplicationListItem | null;
}>();

const emit = defineEmits<{
  success: [];
}>();

const visible = defineModel<boolean>({ default: false });

// Dialog 引用
const dialogRef = ref();

// 表单数据
const formData = ref<{
  app_type: AppType;
  code: string;
  description: string;
  icon: string;
  name: string;
  system_menu_ids: string[];
}>({
  name: '',
  code: '',
  description: '',
  icon: '',
  app_type: 'mixed',
  system_menu_ids: [],
});

// 表单引用
const formRef = ref();

// 是否编辑模式
const isEdit = computed(() => !!props.application);

// 弹窗标题
const title = computed(() =>
  isEdit.value ? $t('application.editApp') : $t('application.createApp'),
);

// 应用类型选项
const appTypeOptions = computed<Array<{ label: string; value: AppType }>>(
  () => [
    { label: $t('application.appTypes.mixed'), value: 'mixed' },
    // { label: $t('application.appTypes.form'), value: 'form' },
    { label: $t('application.appTypes.workflow'), value: 'workflow' },
    { label: $t('application.appTypes.ai'), value: 'ai' },
    // { label: $t('application.appTypes.dashboard'), value: 'dashboard' },
    // { label: $t('application.appTypes.screen'), value: 'screen' },
  ],
);

// 表单验证规则
const rules = computed(() => ({
  name: [
    {
      required: true,
      message: $t('application.validation.nameRequired'),
      trigger: 'blur',
    },
    {
      min: 2,
      max: 100,
      message: $t('application.validation.nameLength'),
      trigger: 'blur',
    },
  ],
  code: [
    {
      required: true,
      message: $t('application.validation.codeRequired'),
      trigger: 'blur',
    },
    {
      pattern: /^[a-z][\w-]*$/i,
      message: $t('application.validation.codePattern'),
      trigger: 'blur',
    },
    {
      min: 2,
      max: 100,
      message: $t('application.validation.codeLength'),
      trigger: 'blur',
    },
  ],
  app_type: [
    {
      required: true,
      message: $t('application.validation.typeRequired'),
      trigger: 'change',
    },
  ],
}));

// 监听弹窗打开，初始化表单数据
watch(visible, (val) => {
  if (val) {
    formData.value = props.application
      ? {
          name: props.application.name,
          code: props.application.code,
          description: props.application.description || '',
          icon: props.application.icon || '',
          app_type: props.application.app_type as AppType,
          system_menu_ids: (props.application as any).system_menu_ids || [],
        }
      : {
          name: '',
          code: '',
          description: '',
          icon: '',
          app_type: 'mixed',
          system_menu_ids: [],
        };
  }
});

// 检查编码唯一性
async function checkCodeUnique(code: string): Promise<boolean> {
  try {
    const res = await checkApplicationUniqueApi(
      'code',
      code,
      props.application?.id,
    );
    return res.data?.unique ?? true;
  } catch {
    return true;
  }
}

// 检查名称唯一性
async function checkNameUnique(name: string): Promise<boolean> {
  try {
    const res = await checkApplicationUniqueApi(
      'name',
      name,
      props.application?.id,
    );
    return res.data?.unique ?? true;
  } catch {
    return true;
  }
}

// 提交表单
async function handleConfirm() {
  try {
    await formRef.value?.validate();
  } catch {
    return;
  }

  dialogRef.value?.setConfirmLoading(true);
  try {
    // 检查编码唯一性
    const codeUnique = await checkCodeUnique(formData.value.code);
    if (!codeUnique) {
      ElMessage.error('应用编码已存在');
      dialogRef.value?.setConfirmLoading(false);
      return;
    }

    // 检查名称唯一性
    const nameUnique = await checkNameUnique(formData.value.name);
    if (!nameUnique) {
      ElMessage.error('应用名称已存在');
      dialogRef.value?.setConfirmLoading(false);
      return;
    }

    if (isEdit.value && props.application) {
      const updateData: ApplicationUpdateInput = {
        name: formData.value.name,
        code: formData.value.code,
        description: formData.value.description,
        icon: formData.value.icon,
        app_type: formData.value.app_type,
        system_menu_ids: formData.value.system_menu_ids,
      };
      await updateApplicationApi(props.application.id, updateData);
      ElMessage.success('更新成功');
    } else {
      const createData: ApplicationCreateInput = {
        name: formData.value.name,
        code: formData.value.code,
        description: formData.value.description,
        icon: formData.value.icon,
        app_type: formData.value.app_type,
        system_menu_ids: formData.value.system_menu_ids,
      };
      await createApplicationApi(createData);
      ElMessage.success('创建成功');
    }

    visible.value = false;
    emit('success');
  } catch {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败');
  } finally {
    dialogRef.value?.setConfirmLoading(false);
  }
}

// 取消
function handleCancel() {
  formRef.value?.resetFields();
  visible.value = false;
}
</script>

<template>
  <ZqDialog
    ref="dialogRef"
    v-model="visible"
    :title="title"
    width="640px"
    :confirm-text="isEdit ? $t('application.save') : $t('application.create')"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      label-position="top"
    >
      <ElRow :gutter="16">
        <ElCol :span="24">
          <ElFormItem :label="$t('application.appName')" prop="name">
            <ElInput
              v-model="formData.name"
              :placeholder="$t('application.appNamePlaceholder')"
              maxlength="100"
              show-word-limit
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="24">
          <ElFormItem :label="$t('application.appCode')" prop="code">
            <ElInput
              v-model="formData.code"
              :placeholder="$t('application.appCodePlaceholder')"
              maxlength="100"
              show-word-limit
              :disabled="isEdit"
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="24">
          <ElFormItem :label="$t('application.appType')" prop="app_type">
            <ElSelect
              v-model="formData.app_type"
              :placeholder="$t('application.appTypePlaceholder')"
              style="width: 100%"
            >
              <ElOption
                v-for="opt in appTypeOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </ElSelect>
          </ElFormItem>
        </ElCol>
        <ElCol :span="24">
          <ElFormItem
            :label="$t('application.appDescription')"
            prop="description"
          >
            <ElInput
              v-model="formData.description"
              type="textarea"
              :placeholder="$t('application.appDescriptionPlaceholder')"
              :rows="3"
              maxlength="500"
              show-word-limit
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="24">
          <ElFormItem :label="$t('application.appIcon')" prop="icon">
            <ZqIconPicker
              v-model="formData.icon"
              prefix="lucide"
              :auto-fetch-api="false"
              class="w-full"
            />
          </ElFormItem>
        </ElCol>
        <ElCol :span="24">
          <ElFormItem
            :label="$t('application.systemMenu')"
            prop="system_menu_ids"
          >
            <ZqMenuSelector
              v-model="formData.system_menu_ids"
              :multiple="true"
              :system-only="true"
              :placeholder="$t('application.systemMenuPlaceholder')"
              :dialog-title="$t('application.selectSystemMenu')"
              dialog-width="500px"
            />
          </ElFormItem>
        </ElCol>
      </ElRow>
    </ElForm>
  </ZqDialog>
</template>
