<script lang="ts" setup>
/**
 * 省市区街道村庄级联选择器组件
 * 支持静态数据和动态 API 加载两种模式
 * 支持五级行政区划：省、市、区、街道、村庄
 */
import type { RegionItem, RegionLevel } from './types';

import { computed, ref, watch } from 'vue';

import { ElCascader, ElMessage } from 'element-plus';

import { RegionApi } from '#/api/core/region';

import { regionData as staticRegionData } from './region-data';

defineOptions({
  name: 'RegionSelector',
});

const props = withDefaults(
  defineProps<{
    apiUrl?: string;
    checkStrictly?: boolean;
    clearable?: boolean;
    dataSource?: 'api' | 'static';
    disabled?: boolean;
    expandTrigger?: 'click' | 'hover';
    lazy?: boolean;
    level?: RegionLevel;
    modelValue?: string | string[];
    multiple?: boolean;
    placeholder?: string;
    separator?: string;
    showAllLevels?: boolean;
  }>(),
  {
    modelValue: undefined,
    level: 3,
    placeholder: undefined,
    disabled: false,
    clearable: true,
    multiple: false,
    showAllLevels: true,
    separator: '/',
    dataSource: 'api',
    apiUrl: '/api/core/regions',
    lazy: true,
    checkStrictly: false,
    expandTrigger: 'click',
  },
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (
    e: 'change',
    value: string | string[] | undefined,
    selectedOptions: RegionItem[],
  ): void;
}>();

// 内部值
const innerValue = ref<string[]>([]);

// 区域数据（转换为 ElCascader 格式后的数据）
const regionData = ref<any[]>([]);
const loading = ref(false);

// 转换数据格式为 ElCascader 需要的格式
const convertToElCascaderFormat = (
  items: RegionItem[],
  currentLevel: number = 1,
): any[] => {
  return items.map((item) => {
    const node: any = {
      value: item.code,
      label: item.name,
    };

    // 如果是懒加载模式且未达到最大级别，标记为可展开
    if (props.lazy && currentLevel < props.level) {
      node.leaf = false;
    } else if (item.children && item.children.length > 0) {
      node.children = convertToElCascaderFormat(
        item.children,
        currentLevel + 1,
      );
    }

    return node;
  });
};

// 根据级别过滤数据
const filterDataByLevel = (data: RegionItem[], level: number): any[] => {
  let filtered = data;

  if (level === 1) {
    // 只保留省级
    filtered = data.map((province) => ({
      code: province.code,
      name: province.name,
    }));
  } else if (level === 2) {
    // 保留省市两级
    filtered = data.map((province) => ({
      code: province.code,
      name: province.name,
      children: province.children?.map((city) => ({
        code: city.code,
        name: city.name,
      })),
    }));
  }

  // 转换为 ElCascader 格式
  return convertToElCascaderFormat(filtered);
};

// 加载静态数据
const loadStaticData = () => {
  console.log('loadStaticData 被调用');
  console.log('staticRegionData:', staticRegionData);
  console.log('staticRegionData.length:', staticRegionData.length);
  const result = filterDataByLevel(staticRegionData, props.level);
  console.log('转换后的数据:', result);
  console.log('转换后的数据长度:', result.length);
  regionData.value = result;
  console.log('赋值后 regionData.value:', regionData.value);
};

// 加载 API 数据（初始加载省份）
const loadApiData = async () => {
  loading.value = true;
  try {
    const provinces = await RegionApi.getProvinces();
    regionData.value = convertToElCascaderFormat(provinces, 1);
  } catch (error) {
    console.error('Failed to load region data:', error);
    ElMessage.error('加载省份数据失败');
    regionData.value = [];
  } finally {
    loading.value = false;
  }
};

// 懒加载子节点
const lazyLoad = async (node: any, resolve: any) => {
  const { level, value } = node;

  try {
    let children: any[] = [];

    // 根据当前级别加载下一级数据
    switch (level) {
      case 0: {
        // 加载省份（不应该走到这里，因为省份在初始化时已加载）
        const provinces = await RegionApi.getProvinces();
        children = provinces;

        break;
      }
      case 1: {
        // 加载城市
        const cities = await RegionApi.getCities(value);
        children = cities;

        break;
      }
      case 2: {
        // 加载区县
        const areas = await RegionApi.getAreas(value);
        children = areas;

        break;
      }
      case 3: {
        // 加载街道
        const streets = await RegionApi.getStreets(value);
        children = streets;

        break;
      }
      case 4: {
        // 加载村庄
        const villages = await RegionApi.getVillages(value);
        children = villages;

        break;
      }
      // No default
    }

    // 转换格式
    const nodes = children.map((item: any) => ({
      value: item.code,
      label: item.name,
      leaf: level + 1 >= props.level, // 如果达到指定级别，标记为叶子节点
    }));

    resolve(nodes);
  } catch (error) {
    console.error('Failed to load children:', error);
    ElMessage.error('加载数据失败');
    resolve([]);
  }
};

// 加载数据
const loadData = () => {
  if (props.dataSource === 'api') {
    loadApiData();
  } else {
    loadStaticData();
  }
};

// 初始化加载
loadData();

// 监听数据源变化
watch(
  () => [props.dataSource, props.apiUrl, props.level],
  () => {
    loadData();
  },
);

// 同步外部值到内部
watch(
  () => props.modelValue,
  (val) => {
    if (val === undefined || val === null) {
      innerValue.value = [];
    } else if (Array.isArray(val)) {
      innerValue.value = val;
    } else {
      // 兼容旧格式：如果传入的是字符串，尝试解析
      innerValue.value = [];
    }
  },
  { immediate: true },
);

// 获取选中的区域对象
const getSelectedRegions = (codes: string[]): RegionItem[] => {
  const regions: RegionItem[] = [];
  let currentLevel = regionData.value;

  for (const code of codes) {
    const node = currentLevel.find((n) => n.code === code);
    if (node) {
      regions.push({ code: node.code, name: node.name });
      currentLevel = node.children || [];
    }
  }

  return regions;
};

// 处理值变化
const handleChange = (value: any) => {
  const codes = Array.isArray(value) ? value : [];
  innerValue.value = codes;

  // 输出完整路径数组，而不是单个编码
  const outputValue = codes.length > 0 ? codes : undefined;
  const selectedRegions = codes.length > 0 ? getSelectedRegions(codes) : [];

  emit('update:modelValue', outputValue);
  emit('change', outputValue, selectedRegions);
};

// 计算 placeholder
const computedPlaceholder = computed(() => {
  if (props.placeholder) return props.placeholder;

  const levelTexts: Record<number, string> = {
    1: '请选择省份',
    2: '请选择省/市',
    3: '请选择省/市/区',
    4: '请选择省/市/区/街道',
    5: '请选择省/市/区/街道/村庄',
  };

  return levelTexts[props.level] || levelTexts[3];
});

// Cascader Props
const cascaderProps = computed(() => {
  const baseProps: any = {
    checkStrictly: props.checkStrictly,
    expandTrigger: props.expandTrigger,
  };

  // 如果是懒加载模式
  if (props.lazy && props.dataSource === 'api') {
    baseProps.lazy = true;
    baseProps.lazyLoad = lazyLoad;
  }

  return baseProps;
});
</script>

<template>
  <div>
    <ElCascader
      v-model="innerValue"
      :options="regionData"
      :props="cascaderProps"
      :placeholder="computedPlaceholder"
      :disabled="disabled"
      :clearable="clearable"
      :show-all-levels="showAllLevels"
      :separator="separator"
      :loading="loading"
      filterable
      class="w-full"
      @change="handleChange"
    />
  </div>
</template>
