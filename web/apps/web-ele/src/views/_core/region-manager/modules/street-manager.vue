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

defineOptions({ name: 'StreetManager' });

const dialogVisible = ref(false);
const dialogMode = ref<'add' | 'edit'>('add');
const editingId = ref('');
const provinces = ref<any[]>([]);
const cities = ref<any[]>([]);
const areas = ref<any[]>([]);
const selectedProvince = ref('');
const selectedCity = ref('');
const selectedArea = ref('');

async function loadProvinces() {
  const res = await RegionApi.getProvinces();
  provinces.value = res;
}

async function loadCities() {
  selectedCity.value = '';
  selectedArea.value = '';
  cities.value = [];
  areas.value = [];
  if (selectedProvince.value) {
    const res = await RegionApi.getCities(selectedProvince.value);
    cities.value = res;
  }
}

async function loadAreas() {
  selectedArea.value = '';
  areas.value = [];
  if (selectedCity.value) {
    const res = await RegionApi.getAreas(selectedCity.value);
    areas.value = res;
  }
}

const fetchStreets = async (params: any) => {
  if (!selectedArea.value) return { items: [], total: 0 };
  const res = await RegionApi.getStreets(selectedArea.value);
  return { items: res, total: res.length };
};

const [Grid, gridApi] = useZqTable({
  gridOptions: {
    columns: [
      { key: 'code', title: '街道代码', width: 150 },
      { key: 'name', title: '街道名称', minWidth: 200 },
      { key: 'area_code', title: '区县代码', width: 150 },
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
      ajax: { query: fetchStreets },
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
      component: 'Select',
      componentProps: { placeholder: '请选择区县', options: [] },
      fieldName: 'area_code',
      label: '所属区县',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: { placeholder: '请输入街道代码' },
      fieldName: 'code',
      label: '街道代码',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: { placeholder: '请输入街道名称' },
      fieldName: 'name',
      label: '街道名称',
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
  const areaOptions = areas.value.map((a: any) => ({
    label: a.name,
    value: a.code,
  }));
  formMethods.updateSchema([
    {
      fieldName: 'province_code',
      componentProps: { options: provinceOptions },
    },
    { fieldName: 'city_code', componentProps: { options: cityOptions } },
    { fieldName: 'area_code', componentProps: { options: areaOptions } },
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
    area_code: row.area_code,
    code: row.code,
    name: row.name,
    sort: row.sort || 0,
  });
  dialogVisible.value = true;
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除该街道吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    await RegionApi.deleteStreet(row.id);
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
      await RegionApi.createStreet(values);
      ElMessage.success('新增成功');
    } else {
      await RegionApi.updateStreet(editingId.value, values);
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
        style="width: 140px; margin-right: 8px"
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
        style="width: 140px; margin-right: 8px"
        @change="loadAreas"
      >
        <ElOption
          v-for="city in cities"
          :key="city.code"
          :label="city.name"
          :value="city.code"
        />
      </ElSelect>
      <ElSelect
        v-model="selectedArea"
        placeholder="选择区县"
        clearable
        filterable
        style="width: 140px; margin-right: 12px"
        @change="gridApi.reload()"
      >
        <ElOption
          v-for="area in areas"
          :key="area.code"
          :label="area.name"
          :value="area.code"
        />
      </ElSelect>
      <ElButton type="primary" :icon="Plus" @click="handleAdd">
        新增街道
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
    :title="dialogMode === 'add' ? '新增街道' : '编辑街道'"
    width="600px"
    @confirm="handleSave"
  >
    <FormRegister />
  </ZqDialog>
</template>
