<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElSelect,
  ElTag,
} from 'element-plus';

import {
  createRedisKeyApi,
  getRedisKeyDetailApi,
  updateRedisKeyApi,
} from '#/api/core/redis-manager';

interface Props {
  visible: boolean;
  dbIndex: number;
  mode: 'create' | 'edit';
  editingKey?: string;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 表单数据
const formData = reactive({
  key: '',
  type: 'string' as 'hash' | 'list' | 'set' | 'string' | 'zset',
  value: '',
  ttl: -1,
});

// 复杂类型的值
const listValue = ref<string[]>(['']);
const setValue = ref<string[]>(['']);
const zsetValue = ref<Array<{ member: string; score: number }>>([
  { member: '', score: 0 },
]);
const hashValue = ref<Array<{ field: string; value: string }>>([
  { field: '', value: '' },
]);

const loading = ref(false);
const formRef = ref();

// 类型选项
const typeOptions = [
  { label: 'String', value: 'string' },
  { label: 'List', value: 'list' },
  { label: 'Set', value: 'set' },
  { label: 'ZSet', value: 'zset' },
  { label: 'Hash', value: 'hash' },
] as const;

// 表单规则
const rules = {
  key: [
    {
      required: true,
      message: $t('redis-manager.keyRequired'),
      trigger: 'blur',
    },
  ],
  type: [
    {
      required: true,
      message: $t('redis-manager.typeRequired'),
      trigger: 'change',
    },
  ],
  value: [
    {
      required: true,
      message: $t('redis-manager.valueRequired'),
      trigger: 'blur',
    },
  ],
};

// 对话框标题
const dialogTitle = computed(() => {
  return props.mode === 'create'
    ? $t('redis-manager.addKey')
    : $t('redis-manager.editKey');
});

// 加载键详情（编辑模式）
async function loadKeyDetail() {
  if (props.mode !== 'edit' || !props.editingKey) return;

  try {
    loading.value = true;
    const detail = await getRedisKeyDetailApi(props.dbIndex, props.editingKey);

    formData.key = detail.key;
    formData.type = detail.type;
    formData.ttl = detail.ttl;

    // 根据类型设置值
    switch (detail.type) {
      case 'hash': {
        hashValue.value = Object.entries(detail.value || {}).map(
          ([field, value]) => ({
            field,
            value: value as string,
          }),
        );
        if (hashValue.value.length === 0) {
          hashValue.value = [{ field: '', value: '' }];
        }

        break;
      }
      case 'list': {
        listValue.value = detail.value || [''];

        break;
      }
      case 'set': {
        setValue.value = detail.value || [''];

        break;
      }
      case 'string': {
        formData.value = detail.value;

        break;
      }
      case 'zset': {
        zsetValue.value = detail.value || [{ member: '', score: 0 }];

        break;
      }
      // No default
    }
  } catch (error) {
    console.error('Failed to load key detail:', error);
    ElMessage.error($t('redis-manager.loadKeyDetailFailed'));
  } finally {
    loading.value = false;
  }
}

// 重置表单
function resetForm() {
  formData.key = '';
  formData.type = 'string';
  formData.value = '';
  formData.ttl = -1;
  listValue.value = [''];
  setValue.value = [''];
  zsetValue.value = [{ member: '', score: 0 }];
  hashValue.value = [{ field: '', value: '' }];
  formRef.value?.clearValidate();
}

// 添加列表项
function addListItem() {
  listValue.value.push('');
}

// 删除列表项
function removeListItem(index: number) {
  if (listValue.value.length > 1) {
    listValue.value.splice(index, 1);
  }
}

// 添加集合成员
function addSetMember() {
  setValue.value.push('');
}

// 删除集合成员
function removeSetMember(index: number) {
  if (setValue.value.length > 1) {
    setValue.value.splice(index, 1);
  }
}

// 添加有序集合成员
function addZSetMember() {
  zsetValue.value.push({ member: '', score: 0 });
}

// 删除有序集合成员
function removeZSetMember(index: number) {
  if (zsetValue.value.length > 1) {
    zsetValue.value.splice(index, 1);
  }
}

// 添加哈希字段
function addHashField() {
  hashValue.value.push({ field: '', value: '' });
}

// 删除哈希字段
function removeHashField(index: number) {
  if (hashValue.value.length > 1) {
    hashValue.value.splice(index, 1);
  }
}

// 获取提交的值
function getSubmitValue() {
  switch (formData.type) {
    case 'hash': {
      const result: Record<string, string> = {};
      for (const item of hashValue.value) {
        if (item.field.trim() !== '') {
          result[item.field] = item.value;
        }
      }
      return result;
    }
    case 'list': {
      return listValue.value.filter((v) => v.trim() !== '');
    }
    case 'set': {
      return setValue.value.filter((v) => v.trim() !== '');
    }
    case 'string': {
      return formData.value;
    }
    case 'zset': {
      return zsetValue.value.filter((v) => v.member.trim() !== '');
    }
    // No default
  }
  return formData.value;
}

// 提交表单
async function handleSubmit() {
  try {
    await formRef.value?.validate();

    loading.value = true;

    const value = getSubmitValue();

    if (props.mode === 'create') {
      await createRedisKeyApi(props.dbIndex, {
        key: formData.key,
        type: formData.type,
        value,
        ttl: formData.ttl,
      });
      ElMessage.success($t('redis-manager.createSuccess'));
    } else {
      await updateRedisKeyApi(props.dbIndex, formData.key, {
        value,
        ttl: formData.ttl,
      });
      ElMessage.success($t('redis-manager.updateSuccess'));
    }

    emit('success');
    handleClose();
  } catch (error: any) {
    if (error !== false) {
      console.error('Failed to submit:', error);
      ElMessage.error(
        props.mode === 'create'
          ? $t('redis-manager.createFailed')
          : $t('redis-manager.updateFailed'),
      );
    }
  } finally {
    loading.value = false;
  }
}

// 关闭对话框
function handleClose() {
  emit('update:visible', false);
  resetForm();
}

// 监听对话框打开
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      if (props.mode === 'edit') {
        loadKeyDetail();
      } else {
        resetForm();
      }
    }
  },
);
</script>

<template>
  <ElDialog
    :model-value="visible"
    :title="dialogTitle"
    width="600px"
    @close="handleClose"
  >
    <ElForm ref="formRef" :model="formData" :rules="rules" label-width="80px">
      <ElFormItem :label="$t('redis-manager.keyName')" prop="key">
        <ElInput
          v-model="formData.key"
          :placeholder="$t('redis-manager.keyName')"
          :disabled="mode === 'edit'"
        />
      </ElFormItem>

      <ElFormItem :label="$t('redis-manager.type')" prop="type">
        <ElSelect
          v-model="formData.type"
          :placeholder="$t('redis-manager.typeRequired')"
          :disabled="mode === 'edit'"
          style="width: 100%"
        >
          <ElOption
            v-for="option in typeOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </ElSelect>
      </ElFormItem>

      <!-- String 类型 -->
      <ElFormItem
        v-if="formData.type === 'string'"
        :label="$t('redis-manager.value')"
        prop="value"
      >
        <ElInput
          v-model="formData.value"
          type="textarea"
          :rows="4"
          :placeholder="$t('redis-manager.value')"
        />
      </ElFormItem>

      <!-- List 类型 -->
      <ElFormItem
        v-if="formData.type === 'list'"
        :label="$t('redis-manager.listItem')"
      >
        <div class="w-full space-y-2">
          <div
            v-for="(_item, index) in listValue"
            :key="index"
            class="flex gap-2"
          >
            <ElInput
              v-model="listValue[index]"
              :placeholder="$t('redis-manager.listItem')"
            />
            <ElButton
              v-if="listValue.length > 1"
              type="danger"
              @click="removeListItem(index)"
            >
              {{ $t('redis-manager.deleteKey') }}
            </ElButton>
          </div>
          <ElButton type="primary" @click="addListItem">
            {{ $t('redis-manager.addItem') }}
          </ElButton>
        </div>
      </ElFormItem>

      <!-- Set 类型 -->
      <ElFormItem
        v-if="formData.type === 'set'"
        :label="$t('redis-manager.setMember')"
      >
        <div class="w-full space-y-2">
          <div
            v-for="(_item, index) in setValue"
            :key="index"
            class="flex gap-2"
          >
            <ElInput
              v-model="setValue[index]"
              :placeholder="$t('redis-manager.member')"
            />
            <ElButton
              v-if="setValue.length > 1"
              type="danger"
              @click="removeSetMember(index)"
            >
              {{ $t('redis-manager.deleteKey') }}
            </ElButton>
          </div>
          <ElButton type="primary" @click="addSetMember">
            {{ $t('redis-manager.addMember') }}
          </ElButton>
        </div>
      </ElFormItem>

      <!-- ZSet 类型 -->
      <ElFormItem
        v-if="formData.type === 'zset'"
        :label="$t('redis-manager.zsetMember')"
      >
        <div class="w-full space-y-2">
          <div
            v-for="(_item, index) in zsetValue"
            :key="index"
            class="flex gap-2"
          >
            <ElInput
              v-model="zsetValue[index]!.member"
              :placeholder="$t('redis-manager.member')"
              style="flex: 2"
            />
            <ElInputNumber
              v-model="zsetValue[index]!.score"
              :placeholder="$t('redis-manager.score')"
              style="flex: 1"
            />
            <ElButton
              v-if="zsetValue.length > 1"
              type="danger"
              @click="removeZSetMember(index)"
            >
              {{ $t('redis-manager.deleteKey') }}
            </ElButton>
          </div>
          <ElButton type="primary" @click="addZSetMember">
            {{ $t('redis-manager.addMember') }}
          </ElButton>
        </div>
      </ElFormItem>

      <!-- Hash 类型 -->
      <ElFormItem
        v-if="formData.type === 'hash'"
        :label="$t('redis-manager.hashField')"
      >
        <div class="w-full space-y-2">
          <div
            v-for="(_item, index) in hashValue"
            :key="index"
            class="flex gap-2"
          >
            <ElInput
              v-model="hashValue[index]!.field"
              :placeholder="$t('redis-manager.fieldName')"
              style="flex: 1"
            />
            <ElInput
              v-model="hashValue[index]!.value"
              :placeholder="$t('redis-manager.fieldValue')"
              style="flex: 2"
            />
            <ElButton
              v-if="hashValue.length > 1"
              type="danger"
              @click="removeHashField(index)"
            >
              {{ $t('redis-manager.deleteKey') }}
            </ElButton>
          </div>
          <ElButton type="primary" @click="addHashField">
            {{ $t('redis-manager.addField') }}
          </ElButton>
        </div>
      </ElFormItem>

      <ElFormItem :label="$t('redis-manager.ttl')">
        <div class="flex items-center gap-2">
          <ElInputNumber
            v-model="formData.ttl"
            :min="-1"
            :placeholder="$t('redis-manager.seconds')"
            style="flex: 1"
          />
          <ElTag size="small" type="info">
            {{ $t('redis-manager.ttlDesc') }}
          </ElTag>
        </div>
      </ElFormItem>
    </ElForm>

    <template #footer>
      <ElButton @click="handleClose">{{ $t('redis-manager.cancel') }}</ElButton>
      <ElButton type="primary" :loading="loading" @click="handleSubmit">
        {{
          mode === 'create'
            ? $t('redis-manager.create')
            : $t('redis-manager.update')
        }}
      </ElButton>
    </template>
  </ElDialog>
</template>

<style scoped>
/* 自定义样式 */
</style>
