<script lang="ts" setup>
import { computed, watch } from 'vue';

import {
  ElCheckbox,
  ElCheckboxGroup,
  ElInputNumber,
  ElRadio,
  ElRadioGroup,
} from 'element-plus';

import { TypeEnum, useTabSetup } from './useTabMixin';

interface Props {
  modelValue?: string;
  disabled?: boolean;
  day?: string;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '*',
  disabled: false,
  day: '*',
});

const emit = defineEmits(['update:modelValue']);

const weekLabels = {
  0: '周日',
  1: '周一',
  2: '周二',
  3: '周三',
  4: '周四',
  5: '周五',
  6: '周六',
};

const disabledChoice = computed(() => {
  return (props.day && props.day !== '*') || props.disabled;
});

const setup = useTabSetup(
  props,
  { emit },
  {
    defaultValue: '*',
    minValue: 0,
    maxValue: 6,
    valueRange: { start: 0, end: 6 },
    valueLoop: { start: 0, interval: 1 },
    disabled: disabledChoice,
  },
);

watch(
  () => props.day,
  () => {
    setup.updateValue(disabledChoice.value ? '*' : setup.computeValue.value);
  },
);

function handleTypeChange() {
  // 类型改变时的处理
}

const {
  type,
  valueRange,
  valueList,
  specifyRange,
  typeRangeAttrs,
  typeSpecifyAttrs,
  beforeRadioAttrs,
} = setup;
</script>

<template>
  <div class="cron-config-list">
    <div class="item tip-item">
      <span class="tip-info">日和周只能设置其中之一</span>
    </div>
    <ElRadioGroup v-model="type" @change="handleTypeChange">
      <div class="item">
        <ElRadio :value="TypeEnum.every" :disabled="disabledChoice">
          每周
        </ElRadio>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.range" :disabled="disabledChoice">
          区间
        </ElRadio>
        <span class="label"> 从周 </span>
        <ElInputNumber
          v-model="valueRange.start"
          v-bind="typeRangeAttrs"
          :step="1"
        />
        <span class="label"> 至周 </span>
        <ElInputNumber
          v-model="valueRange.end"
          v-bind="typeRangeAttrs"
          :step="1"
        />
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.specify" :disabled="disabledChoice">
          指定
        </ElRadio>
        <div class="checkbox-list">
          <ElCheckboxGroup v-model="valueList">
            <ElCheckbox
              v-for="(label, value) in weekLabels"
              :key="value"
              :label="value"
              :disabled="typeSpecifyAttrs.disabled"
            >
              {{ label }}
            </ElCheckbox>
          </ElCheckboxGroup>
        </div>
      </div>
    </ElRadioGroup>
  </div>
</template>

<style scoped lang="css">
.cron-config-list {
  padding: 16px;
}

.item {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}

.tip-item {
  margin-bottom: 8px;
}

.tip-info {
  font-size: 12px;
  color: #909399;
}

.label {
  margin: 0 4px;
  white-space: nowrap;
}

.checkbox-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  margin-top: 8px;
  margin-left: 20px;
}
</style>
