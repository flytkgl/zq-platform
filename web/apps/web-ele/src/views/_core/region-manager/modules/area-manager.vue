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

defineOptions({ name: 'AreaManager' });

const dialogVisible = ref(false);
const dialogMode = ref<'add' | 'edit'>('add');
const editingId = ref('');
const provinces = ref<any[]>([]);
const cities = ref<any[]>([]);
const selectedProvince = ref('');
const selectedCity = ref('');

async function loadProvinces() {
  const res = await RegionApi.getProvinces();
  provinces.value = res;
}

async function loadCities() {
  selectedCity.value = '';
  cities.value = [];
  if (selectedProvince.value) {
    const res = await RegionApi.getCities(selectedProvince.value);
    cities.value = res;
  }
}

const fetchAreas = async (params: any) => {
  if (!selectedCity.value) return { items: [], total: 0 };
  const res = await RegionApi.getAreas(selectedCity.value);
  return { items: res, total: res.length };
};

const [Grid, gridApi] = useZqTable({
  gridOptions: {
    columns: [
      { key: 'code', title: '区县代码', width: 150 },
      { key: 'name', title: '区县名称', minWidth: 200 },
      { key: 'city_code', title: '城市代码', width: 150 },
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
      ajax: { query: fetchAreas },
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
      component: 'Select',
      componentProps: { placeholder: '请选择城市', options: [] },
      fieldName: 'city_code',
      label: '所属城市',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: { placeholder: '请输入区县代码' },
      fieldName: 'code',
      label: '区县代码',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: { placeholder: '请输入区县名称' },
      fieldName: 'name',
      label: '区县名称',
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

function updateFormOptions() {
  const provinceOptions = provinces.value.map((p: any) => ({
    label: p.name,
    value: p.code,
  }));
  const cityOptions = cities.value.map((c: any) => ({
    label: c.name,
    value: c.code,
  }));
  formMethods.updateSchema([
    {
      fieldName: 'province_code',
      componentProps: { options: provinceOptions },
    },
    { fieldName: 'city_code', componentProps: { options: cityOptions } },
  ]);
}

function handleAdd() {
  dialogMode.value = 'add';
  editingId.value = '';
  formMethods.resetForm();
  updateFormOptions();
  dialogVisible.value = true;
}

function handleEdit(row: any) {
  dialogMode.value = 'edit';
  editingId.value = row.id;
  updateFormOptions();
  formMethods.setValues({
    province_code: row.province_code,
    city_code: row.city_code,
    code: row.code,
    name: row.name,
    sort: row.sort || 0,
  });
  dialogVisible.value = true;
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除该区县吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    await RegionApi.deleteArea(row.id);
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
      await RegionApi.createArea(values);
      ElMessage.success('新增成功');
    } else {
      await RegionApi.updateArea(editingId.value, values);
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

loadProvinces();
</script>

<template>
  <Grid>
    <template #toolbar-actions>
      <ElSelect
        v-model="selectedProvince"
        placeholder="选择省份"
        clearable
        filterable
        style="width: 150px; margin-right: 12px"
        @change="loadCities"
      >
        <ElOption
          v-for="province in provinces"
          :key="province.code"
          :label="province.name"
          :value="province.code"
        />
      </ElSelect>
      <ElSelect
        v-model="selectedCity"
        placeholder="选择城市"
        clearable
        filterable
        style="width: 150px; margin-right: 12px"
        @change="gridApi.reload()"
      >
        <ElOption
          v-for="city in cities"
          :key="city.code"
          :label="city.name"
          :value="city.code"
        />
      </ElSelect>
      <ElButton type="primary" :icon="Plus" @click="handleAdd">
        新增区县
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
    :title="dialogMode === 'add' ? '新增区县' : '编辑区县'"
    width="600px"
    @confirm="handleSave"
  >
    <FormRegister />
  </ZqDialog>
</template>
