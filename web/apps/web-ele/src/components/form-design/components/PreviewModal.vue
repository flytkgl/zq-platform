<script setup lang="ts">
import { $t } from '@vben/locales';
import { reactive, ref, watch } from 'vue';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElMessage,
  ElScrollbar,
} from 'element-plus';

import PreviewItem from './PreviewItem.vue';

const props = defineProps<{
  conf: any;
}>();

const visible = ref(false);
const formData = reactive<any>({});
const formRef = ref();

// 递归初始化数据
function initFormData(items: any[]) {
  items.forEach((item: any) => {
    if (item.type === 'grid') {
      item.columns.forEach((col: any) => {
        initFormData(col.children);
      });
    } else {
      // 初始化数据
      if (item.type === 'checkbox') {
        formData[item.field] = [];
      } else if (['input-number', 'rate', 'slider'].includes(item.type)) {
        formData[item.field] = 0;
      } else if (item.type === 'switch') {
        formData[item.field] = false;
      } else if (item.type === 'sub-table') {
        formData[item.field] = [];
        // 处理最小行数
        const min = item.props.minRows || 0;
        if (min > 0) {
          for (let i = 0; i < min; i++) {
            const newRow: any = { _id: `${Date.now()}_${Math.random()}` };
            if (item.children) {
              item.children.forEach((col: any) => {
                newRow[col.field] = null;
              });
            }
            formData[item.field].push(newRow);
          }
        }
      } else {
        formData[item.field] = null;
      }
    }
  });
}

// 初始化数据
watch(
  () => props.conf,
  (newConf) => {
    if (!newConf || !newConf.items) return;

    // 重置
    for (const key in formData) delete formData[key];

    initFormData(newConf.items);
  },
  { deep: true },
);

const open = () => {
  visible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
    ElMessage.success($t('form-design.message.validateSuccess'));
    console.log($t('form-design.preview.submitData'), formData);
  } catch {
    ElMessage.error($t('form-design.message.validateError'));
  }
};

defineExpose({ open });
</script>

<template>
  <ElDialog
    v-model="visible"
    :title="$t('form-design.previewLabel')"
    width="800px"
    destroy-on-close
    append-to-body
    align-center
  >
    <ElScrollbar max-height="60vh">
      <div
        :style="{
          padding: `${conf.formPaddingTop ?? conf.formPadding ?? 20}px ${conf.formPaddingRight ?? conf.formPadding ?? 20}px ${conf.formPaddingBottom ?? conf.formPadding ?? 20}px ${conf.formPaddingLeft ?? conf.formPadding ?? 20}px`,
          margin: `${conf.formMarginTop ?? conf.formMargin ?? 0}px ${conf.formMarginRight ?? conf.formMargin ?? 0}px ${conf.formMarginBottom ?? conf.formMargin ?? 0}px ${conf.formMarginLeft ?? conf.formMargin ?? 0}px`,
          width: conf.formWidth || '100%',
          maxWidth: conf.formMaxWidth || 'none',
          backgroundColor: conf.formBackground || 'transparent',
          border: conf.formBorder ? '1px solid var(--el-border-color)' : 'none',
          borderRadius: conf.formBorder ? `${conf.formBorderRadius || 4}px` : '0',
          boxShadow: conf.formShadow ? '0 2px 12px 0 rgba(0, 0, 0, 0.1)' : 'none',
        }"
      >
        <ElForm
          ref="formRef"
          :model="formData"
          :label-width="`${conf.labelWidth}px`"
          :label-position="conf.labelPosition"
          :size="conf.size"
          :disabled="conf.disabled || false"
          :style="{
            '--el-form-item-margin-bottom': `${conf.itemSpacing || 18}px`,
          }"
        >
          <PreviewItem
            v-for="item in conf.items"
            :key="item.id"
            :item="item"
            :model-value="formData"
          />
        </ElForm>
      </div>

      <div class="bg-accent mt-4 rounded p-4">
        <div class="text-muted-foreground mb-2 text-sm font-bold">
          {{ $t('form-design.preview.formData') }} (v-model):
        </div>
        <pre class="text-muted-foreground overflow-auto text-xs">{{
          formData
        }}</pre>
      </div>
    </ElScrollbar>

    <template #footer>
      <ElButton @click="visible = false">{{ $t('common.cancel') }}</ElButton>
      <ElButton type="primary" @click="handleSubmit">{{ $t('form-design.preview.submit') }}</ElButton>
    </template>
  </ElDialog>
</template>
