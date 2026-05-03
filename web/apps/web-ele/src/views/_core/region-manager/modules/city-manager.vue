<script lang="ts" setup>
import { ref } from 'vue';

import { Edit, Plus, Trash2 } from '@vben/icons';

import {
  ElButton,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
} from 'element-plus';

import { useVbenForm } from '#/adapter/form';
import { RegionApi } from '#/api/core/region';
import ZqDialog from '#/components/zq-dialog/zq-dialog.vue';
import { useZqTable } from '#/components/zq-table';

defineOptions({ name: 'CityManager' });

const dialogVisible = ref(false);
const dialogMode = ref<'add' | 'edit'>('add');
const editingId = ref('');
const provinces = ref<any[]>([]);
const selectedProvince = ref('');

async function loadProvinces() {
  try {
    const res = await RegionApi.getProvinces();
    provinces.value = res;
  } catch {
    ElMessage.error('加载省份列表失败');
  }
}

const fetchCities = async (params: any) => {
  const res = await RegionApi.getCities(selectedProvince.value || undefined);
  return {
    items: res,
    total: res.length,
  };
};

const [Grid, gridApi] = useZqTable({
  gridOptions: {
    columns: [
      { key: 'code', title: '城市代码', width: 150 },
      { key: 'name', title: '城市名称', minWidth: 200 },
      { key: 'province_code', title: '省份代码', width: 150 },
      { key: 'sort', title: '排序', width: 100, align: 'center' },
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
      ajax: { query: fetchCities },
    },
    pagerConfig: { enabled: false },
    toolbarConfig: { refresh: true, zoom: true, custom: true },
  },
});

const [FormRegister, formMethods] = useVbenForm({
  schema: [
    {
      component: 'Select',
      componentProps: { placeholder: '请选择省份', options: [] },
      fieldName: 'province_code',
      label: '所属省份',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: { placeholder: '请输入城市代码' },
      fieldName: 'code',
      label: '城市代码',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: { placeholder: '请输入城市名称' },
      fieldName: 'name',
      label: '城市名称',
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

function updateProvinceOptions() {
  const provinceOptions = provinces.value.map((p: any) => ({
    label: p.name,
    value: p.code,
  }));
  formMethods.updateSchema([
    {
      fieldName: 'province_code',
      componentProps: { options: provinceOptions },
    },
  ]);
}

function handleAdd() {
  dialogMode.value = 'add';
  editingId.value = '';
  formMethods.resetForm();
  updateProvinceOptions();
  dialogVisible.value = true;
}

function handleEdit(row: any) {
  dialogMode.value = 'edit';
  editingId.value = row.id;
  updateProvinceOptions();
  formMethods.setValues({
    province_code: row.province_code,
    code: row.code,
    name: row.name,
    sort: row.sort || 0,
  });
  dialogVisible.value = true;
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除该城市吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    await RegionApi.deleteCity(row.id);
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
      await RegionApi.createCity(values);
      ElMessage.success('新增成功');
    } else {
      await RegionApi.updateCity(editingId.value, values);
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

function handleProvinceChange() {
  gridApi.reload();
}

loadProvinces();
</script>

<template>
  <Grid>
    <template #toolbar-actions>
      <ElSelect
        v-model="selectedProvince"
        placeholder="选择省份筛选"
        clearable
        filterable
        style="width: 200px; margin-right: 12px"
        @change="handleProvinceChange"
      >
        <ElOption
          v-for="province in provinces"
          :key="province.code"
          :label="province.name"
          :value="province.code"
        />
      </ElSelect>
      <ElButton type="primary" :icon="Plus" @click="handleAdd">
        新增城市
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
    :title="dialogMode === 'add' ? '新增城市' : '编辑城市'"
    width="600px"
    @confirm="handleSave"
  >
    <FormRegister />
  </ZqDialog>
</template>
