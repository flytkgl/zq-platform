<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElButton,
  ElColorPicker,
  ElRadioButton,
  ElRadioGroup,
} from 'element-plus';

type ColorMode = 'gradient' | 'solid';
type GradientDirection =
  | 'to bottom'
  | 'to bottom left'
  | 'to bottom right'
  | 'to left'
  | 'to right'
  | 'to top'
  | 'to top left'
  | 'to top right';

interface GradientPreset {
  label: string;
  value: string;
}

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    showAlpha?: boolean;
  }>(),
  {
    modelValue: '',
    showAlpha: true,
  },
);

const emit = defineEmits<{
  (e: 'change', value: string): void;
  (e: 'update:modelValue', value: string): void;
}>();

// 内置纯色预设（半透明，兼容 dark/light 模式）
const solidPresets = [
  'rgba(99, 102, 241, 0.35)',
  'rgba(59, 130, 246, 0.35)',
  'rgba(14, 165, 233, 0.35)',
  'rgba(20, 184, 166, 0.35)',
  'rgba(34, 197, 94, 0.35)',
  'rgba(132, 204, 22, 0.35)',
  'rgba(245, 158, 11, 0.35)',
  'rgba(249, 115, 22, 0.35)',
  'rgba(239, 68, 68, 0.35)',
  'rgba(236, 72, 153, 0.35)',
  'rgba(168, 85, 247, 0.35)',
  'rgba(107, 114, 128, 0.3)',
];

// 内置渐变色预设
const gradientPresets = computed<GradientPreset[]>(() => [
  {
    label: $t('dashboard-design.gradient.presets.warmSunrise'),
    value:
      'linear-gradient(135deg, rgba(245,247,250,0.45) 0%, rgba(195,207,226,0.45) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.oceanBreeze'),
    value:
      'linear-gradient(135deg, rgba(224,195,252,0.4) 0%, rgba(142,197,252,0.4) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.freshMint'),
    value:
      'linear-gradient(135deg, rgba(212,252,121,0.35) 0%, rgba(150,230,161,0.35) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.peachGlow'),
    value:
      'linear-gradient(135deg, rgba(255,236,210,0.45) 0%, rgba(252,182,159,0.4) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.lavenderDream'),
    value:
      'linear-gradient(135deg, rgba(161,140,209,0.35) 0%, rgba(251,194,235,0.35) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.skyBlue'),
    value:
      'linear-gradient(135deg, rgba(137,247,254,0.3) 0%, rgba(102,166,255,0.35) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.roseWater'),
    value:
      'linear-gradient(135deg, rgba(254,207,239,0.4) 0%, rgba(255,154,158,0.35) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.softGrass'),
    value:
      'linear-gradient(135deg, rgba(193,223,196,0.4) 0%, rgba(222,236,221,0.4) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.winterNymph'),
    value:
      'linear-gradient(135deg, rgba(161,196,253,0.35) 0%, rgba(194,233,251,0.35) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.cottonCandy'),
    value:
      'linear-gradient(135deg, rgba(243,231,233,0.4) 0%, rgba(227,238,255,0.4) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.sunnyMorning'),
    value:
      'linear-gradient(135deg, rgba(246,211,101,0.35) 0%, rgba(253,160,133,0.35) 100%)',
  },
  {
    label: $t('dashboard-design.gradient.presets.crystalClear'),
    value:
      'linear-gradient(135deg, rgba(253,252,251,0.4) 0%, rgba(226,209,195,0.4) 100%)',
  },
]);

const directionOptions = computed(() => [
  { label: '↓', value: 'to bottom' },
  { label: '→', value: 'to right' },
  { label: '↗', value: 'to top right' },
  { label: '↘', value: 'to bottom right' },
  { label: '↑', value: 'to top' },
  { label: '←', value: 'to left' },
  { label: '↖', value: 'to top left' },
  { label: '↙', value: 'to bottom left' },
]);

// 状态
const colorMode = ref<ColorMode>('solid');
const solidColor = ref('');
const gradientColor1 = ref('#f5f7fa');
const gradientColor2 = ref('#c3cfe2');
const gradientDirection = ref<GradientDirection>('to bottom right');

// 解析当前值
function parseValue(val: string) {
  if (!val) {
    colorMode.value = 'solid';
    solidColor.value = '';
    return;
  }

  const gradientMatch = val.match(
    /linear-gradient\(\s*(to\s[^,]+|[\d.]+deg)\s*,\s*(#[\da-fA-F]{3,8}|rgba?\([^)]+\)|\w+)\s+\d+%\s*,\s*(#[\da-fA-F]{3,8}|rgba?\([^)]+\)|\w+)\s+\d+%\s*\)/,
  );
  if (gradientMatch) {
    colorMode.value = 'gradient';
    gradientDirection.value =
      (gradientMatch[1]?.trim() as GradientDirection) || 'to bottom right';
    gradientColor1.value = gradientMatch[2]?.trim() || '#f5f7fa';
    gradientColor2.value = gradientMatch[3]?.trim() || '#c3cfe2';
  } else {
    colorMode.value = 'solid';
    solidColor.value = val;
  }
}

// 初始化
parseValue(props.modelValue);

// 监听外部值变化
watch(
  () => props.modelValue,
  (val) => {
    parseValue(val || '');
  },
);

// 生成渐变色值
function buildGradientValue(): string {
  return `linear-gradient(${gradientDirection.value}, ${gradientColor1.value} 0%, ${gradientColor2.value} 100%)`;
}

// 发出更新
function emitUpdate(val: string) {
  emit('update:modelValue', val);
  emit('change', val);
}

// 纯色变化
function handleSolidChange(val: null | string) {
  solidColor.value = val || '';
  emitUpdate(solidColor.value);
}

// 渐变色参数变化
function handleGradientChange() {
  const val = buildGradientValue();
  emitUpdate(val);
}

// 切换模式
function handleModeChange(mode: ColorMode) {
  colorMode.value = mode;
  if (mode === 'solid') {
    emitUpdate(solidColor.value);
  } else {
    handleGradientChange();
  }
}

// 选择预设
function handlePresetClick(preset: GradientPreset) {
  parseValue(preset.value);
  emitUpdate(preset.value);
}

// 清除
function handleClear() {
  solidColor.value = '';
  emitUpdate('');
}

// 预览色块样式
const previewStyle = computed(() => {
  const val = props.modelValue;
  if (!val) return { backgroundColor: 'var(--el-fill-color-lighter)' };
  if (val.includes('gradient')) return { background: val };
  return { backgroundColor: val };
});
</script>

<template>
  <div class="gradient-color-picker w-full">
    <!-- 模式切换 -->
    <ElRadioGroup
      :model-value="colorMode"
      size="small"
      class="mb-2 w-full"
      @change="
        (val: string | number | boolean | undefined) =>
          handleModeChange(val as ColorMode)
      "
    >
      <ElRadioButton value="solid">
        {{ $t('dashboard-design.gradient.solid') }}
      </ElRadioButton>
      <ElRadioButton value="gradient">
        {{ $t('dashboard-design.gradient.gradient') }}
      </ElRadioButton>
    </ElRadioGroup>

    <!-- 纯色模式 -->
    <div v-if="colorMode === 'solid'" class="space-y-2">
      <div class="flex items-center gap-2">
        <ElColorPicker
          :model-value="solidColor"
          :show-alpha="showAlpha"
          @change="handleSolidChange"
        />
        <span class="text-muted-foreground flex-1 truncate text-xs">
          {{ solidColor || $t('dashboard-design.gradient.noColor') }}
        </span>
        <ElButton v-if="solidColor" size="small" text @click="handleClear">
          {{ $t('dashboard-design.attribute.reset') }}
        </ElButton>
      </div>
      <!-- 纯色预设 -->
      <div class="grid grid-cols-6 gap-1.5">
        <button
          v-for="(color, index) in solidPresets"
          :key="index"
          type="button"
          class="h-6 w-full cursor-pointer rounded border transition-all hover:scale-110"
          :class="
            solidColor === color
              ? 'border-primary ring-primary/30 ring-2'
              : 'border-gray-200 dark:border-gray-600'
          "
          :style="{ backgroundColor: color }"
          @click="handleSolidChange(color)"
        ></button>
      </div>
    </div>

    <!-- 渐变模式 -->
    <div v-else class="space-y-2">
      <!-- 预览 -->
      <div class="h-8 w-full rounded-md border" :style="previewStyle"></div>

      <!-- 两个颜色 -->
      <div class="flex items-center gap-2">
        <div class="flex flex-1 items-center gap-1">
          <ElColorPicker
            v-model="gradientColor1"
            size="small"
            show-alpha
            @change="handleGradientChange"
          />
          <span class="text-muted-foreground text-xs">
            {{ $t('dashboard-design.gradient.startColor') }}
          </span>
        </div>
        <div class="flex flex-1 items-center gap-1">
          <ElColorPicker
            v-model="gradientColor2"
            size="small"
            show-alpha
            @change="handleGradientChange"
          />
          <span class="text-muted-foreground text-xs">
            {{ $t('dashboard-design.gradient.endColor') }}
          </span>
        </div>
      </div>

      <!-- 方向 -->
      <div class="flex items-center gap-2">
        <span class="text-muted-foreground whitespace-nowrap text-xs">
          {{ $t('dashboard-design.gradient.direction') }}
        </span>
        <div class="direction-grid">
          <button
            v-for="opt in directionOptions"
            :key="opt.value"
            type="button"
            class="direction-btn"
            :class="{ active: gradientDirection === opt.value }"
            :title="opt.value"
            @click="
              gradientDirection = opt.value as GradientDirection;
              handleGradientChange();
            "
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- 预设渐变 -->
      <div>
        <div class="text-muted-foreground mb-1 text-xs">
          {{ $t('dashboard-design.gradient.presetTitle') }}
        </div>
        <div class="preset-grid">
          <button
            v-for="preset in gradientPresets"
            :key="preset.value"
            type="button"
            class="preset-item"
            :style="{ background: preset.value }"
            :title="preset.label"
            @click="handlePresetClick(preset)"
          ></button>
        </div>
      </div>

      <!-- 清除 -->
      <div class="flex justify-end">
        <ElButton size="small" text @click="handleClear">
          {{ $t('dashboard-design.attribute.reset') }}
        </ElButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.direction-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2px;
}

.direction-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  font-size: 12px;
  cursor: pointer;
  background: var(--el-fill-color-lighter);
  border: 1px solid transparent;
  border-radius: 4px;
  transition: all 0.2s;
}

.direction-btn:hover {
  background: var(--el-fill-color);
}

.direction-btn.active {
  background: var(--el-color-primary-light-8);
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
}

.preset-item {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.2s;
}

.preset-item:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style>
