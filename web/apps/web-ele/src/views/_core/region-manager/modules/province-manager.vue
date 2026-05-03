<script lang="ts" setup>
import { ref } from 'vue';

import { Edit, Plus, Trash2 } from '@vben/icons';

import { ElButton, ElMessage, ElMessageBox } from 'element-plus';

import { useVbenForm } from '#/adapter/form';
import { RegionApi } from '#/api/core/region';
import ZqDialog from '#/components/zq-dialog/zq-dialog.vue';
import { useZqTable } from '#/components/zq-table';

defineOptions({ name: 'ProvinceManager' });

const dialogVisible = ref(false);
const dialogMode = ref<'add' | 'edit'>('add');
const editingId = ref('');

const fetchProvinces = async (params: any) => {
  const res = await RegionApi.getProvinces();
  return {
    items: res,
    total: res.length,
  };
};

const [Grid, gridApi] = useZqTable({
  gridOptions: {
    columns: [
      {
        key: 'code',
        title: '省份代码',
        width: 150,
      },
      {
        key: 'name',
        title: '省份名称',
        minWidth: 200,
      },
      {
        key: 'sort',
        title: '排序',
        width: 100,
        align: 'center',
      },
      {
        key: 'actions',
        title: '操作',
        width: 150,
        fixed: 'right',
        align: 'center',
        slots: { default: 'cell-actions' },
      },
    ],
    border: true,
    stripe: true,
    proxyConfig: {
      autoLoad: true,
      ajax: {
        query: fetchProvinces,
      },
    },
    pagerConfig: {
      enabled: false,
    },
    toolbarConfig: {
      refresh: true,
      zoom: true,
      custom: true,
    },
  },
});

const [FormRegister, formMethods] = useVbenForm({
  schema: [
    {
      component: 'Input',
      componentProps: { placeholder: '请输入省份代码' },
      fieldName: 'code',
      label: '省份代码',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: { placeholder: '请输入省份名称' },
      fieldName: 'name',
      label: '省份名称',
      rules: 'required',
    },
    {
      component: 'InputNumber',
      componentProps: { placeholder: '请输入排序', min: 0 },
      fieldName: 'sort',
      label: '排序',
      defaultValue: 0,
    },
  ],
});

function handleAdd() {
  dialogMode.value = 'add';
  editingId.value = '';
  formMethods.resetForm();
  dialogVisible.value = true;
}

function handleEdit(row: any) {
  dialogMode.value = 'edit';
  editingId.value = row.id;
  formMethods.setValues({
    code: row.code,
    name: row.name,
    sort: row.sort || 0,
  });
  dialogVisible.value = true;
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除该省份吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    await RegionApi.deleteProvince(row.id);
    ElMessage.success('删除成功');
    gridApi.reload();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败');
    }
  }
}

async function handleSave() {
  try {
    await formMethods.validate();
    const values = await formMethods.getValues();
    if (dialogMode.value === 'add') {
      await RegionApi.createProvince(values);
      ElMessage.success('新增成功');
    } else {
      await RegionApi.updateProvince(editingId.value, values);
      ElMessage.success('更新成功');
    }
    dialogVisible.value = false;
    gridApi.reload();
  } catch (error: any) {
    if (error?.errorFields) {
      ElMessage.error('请填写完整信息');
    } else {
      ElMessage.error(error.message || '保存失败');
    }
  }
}
</script>

<template>
  <Grid>
    <template #toolbar-actions>
      <ElButton type="primary" :icon="Plus" @click="handleAdd">
        新增省份
      </ElButton>
    </template>

    <template #cell-actions="{ row }">
      <ElButton link type="primary" :icon="Edit" @click="handleEdit(row)">
        编辑
      </ElButton>
      <ElButton link type="danger" :icon="Trash2" @click="handleDelete(row)">
        删除
      </ElButton>
    </template>
  </Grid>

  <ZqDialog
    v-model="dialogVisible"
    :title="dialogMode === 'add' ? '新增省份' : '编辑省份'"
    width="600px"
    @confirm="handleSave"
  >
    <FormRegister />
  </ZqDialog>
</template>
