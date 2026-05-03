<script lang="ts" setup>
import {
  ElCheckbox,
  ElCheckboxGroup,
  ElInputNumber,
  ElRadio,
  ElRadioGroup,
} from 'element-plus';

import { TypeEnum, useTabProps, useTabSetup } from './useTabMixin';

const props = defineProps({
  ...useTabProps({
    defaultValue: '*',
  }),
});

const emit = defineEmits(['update:modelValue']);

const {
  type,
  valueRange,
  valueLoop,
  valueList,
  specifyRange,
  typeRangeAttrs,
  typeLoopAttrs,
  typeSpecifyAttrs,
  beforeRadioAttrs,
} = useTabSetup(
  props,
  { emit },
  {
    defaultValue: '*',
    minValue: 1,
    maxValue: 12,
    valueRange: { start: 1, end: 12 },
    valueLoop: { start: 1, interval: 1 },
  },
);

function handleTypeChange() {
  // 类型改变时的处理
}
</script>

<template>
  <div class="cron-config-list">
    <ElRadioGroup v-model="type" @change="handleTypeChange">
      <div class="item">
        <ElRadio :value="TypeEnum.every" v-bind="beforeRadioAttrs">
          每月
        </ElRadio>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.range" v-bind="beforeRadioAttrs">
          区间
        </ElRadio>
        <span class="label"> 从 </span>
        <ElInputNumber
          v-model="valueRange.start"
          v-bind="typeRangeAttrs"
          :step="1"
        />
        <span class="label"> 月 至 </span>
        <ElInputNumber
          v-model="valueRange.end"
          v-bind="typeRangeAttrs"
          :step="1"
        />
        <span class="label"> 月 </span>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.loop" v-bind="beforeRadioAttrs">循环</ElRadio>
        <span class="label"> 从 </span>
        <ElInputNumber
          v-model="valueLoop.start"
          v-bind="typeLoopAttrs"
          :step="1"
        />
        <span class="label"> 月开始，间隔 </span>
        <ElInputNumber
          v-model="valueLoop.interval"
          v-bind="typeLoopAttrs"
          :step="1"
        />
        <span class="label"> 月 </span>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.specify" v-bind="beforeRadioAttrs">
          指定
        </ElRadio>
        <div class="checkbox-list">
          <ElCheckboxGroup v-model="valueList">
            <ElCheckbox
              v-for="i in specifyRange"
              :key="i"
              :label="i"
              :disabled="typeSpecifyAttrs.disabled"
            >
              {{ i }}
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
