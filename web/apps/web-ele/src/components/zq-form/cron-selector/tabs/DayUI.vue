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
  week?: string;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '*',
  disabled: false,
  week: '*',
});

const emit = defineEmits(['update:modelValue']);

const disabledChoice = computed(() => {
  return (props.week && props.week !== '*') || props.disabled;
});

const setup = useTabSetup(
  props,
  { emit },
  {
    defaultValue: '*',
    valueWork: 1,
    minValue: 1,
    maxValue: 31,
    valueRange: { start: 1, end: 31 },
    valueLoop: { start: 1, interval: 1 },
    disabled: disabledChoice,
  },
);

const typeWorkAttrs = computed(() => ({
  disabled:
    setup.type.value !== TypeEnum.work ||
    props.disabled ||
    disabledChoice.value,
  ...setup.inputNumberAttrs.value,
}));

watch(
  () => props.week,
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
  valueLoop,
  valueList,
  specifyRange,
  typeRangeAttrs,
  typeLoopAttrs,
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
          每日
        </ElRadio>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.range" :disabled="disabledChoice">
          区间
        </ElRadio>
        <span class="label"> 从 </span>
        <ElInputNumber
          v-model="valueRange.start"
          v-bind="typeRangeAttrs"
          :step="1"
        />
        <span class="label"> 日 至 </span>
        <ElInputNumber
          v-model="valueRange.end"
          v-bind="typeRangeAttrs"
          :step="1"
        />
        <span class="label"> 日 </span>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.loop" :disabled="disabledChoice">
          循环
        </ElRadio>
        <span class="label"> 从 </span>
        <ElInputNumber
          v-model="valueLoop.start"
          v-bind="typeLoopAttrs"
          :step="1"
        />
        <span class="label"> 日开始，间隔 </span>
        <ElInputNumber
          v-model="valueLoop.interval"
          v-bind="typeLoopAttrs"
          :step="1"
        />
        <span class="label"> 日 </span>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.last" :disabled="disabledChoice">
          最后一日
        </ElRadio>
      </div>
      <div class="item">
        <ElRadio :value="TypeEnum.specify" :disabled="disabledChoice">
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
