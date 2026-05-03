<script lang="ts" setup>
import { computed, provide, reactive, ref, watch } from 'vue';

import { useDebounceFn } from '@vueuse/core';
import CronParser from 'cron-parser';
import { ElInput, ElTabPane, ElTabs, ElTooltip } from 'element-plus';

import DayUI from './tabs/DayUI.vue';
import HourUI from './tabs/HourUI.vue';
import MinuteUI from './tabs/MinuteUI.vue';
import MonthUI from './tabs/MonthUI.vue';
import SecondUI from './tabs/SecondUI.vue';
import WeekUI from './tabs/WeekUI.vue';
import YearUI from './tabs/YearUI.vue';

interface Props {
  modelValue?: string;
  disabled?: boolean;
  hideSecond?: boolean;
  hideYear?: boolean;
  remote?: (
    cron: string,
    timestamp: number,
    callback: (result: string) => void,
  ) => void;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  disabled: false,
  hideSecond: true,
  hideYear: true,
});

const emit = defineEmits(['update:modelValue', 'change']);

provide('prefixCls', 'cron');

const activeKey = ref('minute');
const second = ref('*');
const minute = ref('*');
const hour = ref('*');
const day = ref('*');
const month = ref('*');
const week = ref('*');
const year = ref('*');

const inputValues = reactive({
  second: '',
  minute: '',
  hour: '',
  day: '',
  month: '',
  week: '',
  year: '',
  cron: '',
});

const preTimeList = ref('执行预览，会忽略年份参数。');

// 计算 cron 表达式
const cronValueInner = computed(() => {
  const result: string[] = [];
  if (!props.hideSecond) {
    result.push(second.value ? second.value : '*');
  }
  result.push(
    minute.value ? minute.value : '*',
    hour.value ? hour.value : '*',
    day.value ? day.value : '*',
    month.value ? month.value : '*',
    week.value ? week.value : '*',
  );
  if (!props.hideYear && !props.hideSecond)
    result.push(year.value ? year.value : '*');
  return result.join(' ');
});

// 不含年的 cron 表达式
const cronValueNoYear = computed(() => {
  const v = cronValueInner.value;
  if (props.hideYear || props.hideSecond) return v;
  let vs = v.split(' ');
  if (vs.length >= 5) {
    // 转成 Quartz 的规则
    vs = ['0', vs[0], vs[1], vs[2], vs[3], convertWeekToQuartz(vs[4]), '*'];
  }
  return vs.slice(0, -1).join(' ');
});

const calTriggerList = useDebounceFn(calTriggerListInner, 500);

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal === cronValueInner.value) {
      return;
    }
    formatValue();
  },
  { immediate: true },
);

watch(cronValueInner, (newValue) => {
  calTriggerList();
  emitValue(newValue);
  assignInput();
});

assignInput();
formatValue();
calTriggerListInner();

function assignInput() {
  inputValues.second = second.value;
  inputValues.minute = minute.value;
  inputValues.hour = hour.value;
  inputValues.day = day.value;
  inputValues.month = month.value;
  inputValues.week = week.value;
  inputValues.year = year.value;
  inputValues.cron = cronValueInner.value;
  if (!props.modelValue) emitValue(inputValues.cron);
}

function formatValue() {
  if (!props.modelValue) return;
  const values = props.modelValue.split(' ').filter((item) => !!item);
  if (!values || values.length <= 0) return;
  let i = 0;
  if (!props.hideSecond) second.value = values[i++];
  if (values.length > i) minute.value = values[i++];
  if (values.length > i) hour.value = values[i++];
  if (values.length > i) day.value = values[i++];
  if (values.length > i) month.value = values[i++];
  if (values.length > i) week.value = values[i++];
  if (values.length > i) year.value = values[i];
  assignInput();
}

// Quartz 的规则：
// 1 = 周日，2 = 周一，3 = 周二，4 = 周三，5 = 周四，6 = 周五，7 = 周六
function convertWeekToQuartz(week: string) {
  const convert = (v: string) => {
    if (v === '0') {
      return '1';
    }
    if (v === '1') {
      return '0';
    }
    return (Number.parseInt(v) - 1).toString();
  };

  const patten1 = /^([0-7])([-/])([0-7])$/;
  const patten2 = /^([0-7])(,[0-7])+$/;

  if (/^[0-7]$/.test(week)) {
    return convert(week);
  } else if (patten1.test(week)) {
    return week.replace(patten1, (_$0, before, separator, after) => {
      return separator === '/'
        ? convert(before) + separator + after
        : convert(before) + separator + convert(after);
    });
  } else if (patten2.test(week)) {
    return week
      .split(',')
      .map((v) => convert(v))
      .join(',');
  }
  return week;
}

function calTriggerListInner() {
  if (props.remote) {
    props.remote(cronValueInner.value, Date.now(), (v) => {
      preTimeList.value = v;
    });
    return;
  }

  const options = {
    currentDate: new Date(),
  };

  try {
    const iter = CronParser.parseExpression(cronValueNoYear.value, options);
    const result: string[] = [];
    for (let i = 0; i < 10; i++) {
      const nextDate = iter.next();
      result.push(nextDate.toDate().toLocaleString());
    }
    preTimeList.value = result.length > 0 ? result.join('\n') : '无执行时间';
  } catch {
    preTimeList.value = '无效的Cron表达式';
  }
}

function onInputBlur() {
  second.value = inputValues.second;
  minute.value = inputValues.minute;
  hour.value = inputValues.hour;
  day.value = inputValues.day;
  month.value = inputValues.month;
  week.value = inputValues.week;
  year.value = inputValues.year;
}

function onInputCronBlur() {
  emitValue(inputValues.cron);
}

function emitValue(value: string) {
  emit('change', value);
  emit('update:modelValue', value);
}
</script>

<template>
  <div class="cron-inner">
    <ElTabs v-model="activeKey">
      <ElTabPane v-if="!hideSecond" label="秒" name="second">
        <SecondUI v-model="second" :disabled="disabled" />
      </ElTabPane>
      <ElTabPane label="分" name="minute">
        <MinuteUI v-model="minute" :disabled="disabled" />
      </ElTabPane>
      <ElTabPane label="时" name="hour">
        <HourUI v-model="hour" :disabled="disabled" />
      </ElTabPane>
      <ElTabPane label="日" name="day">
        <DayUI v-model="day" :week="week" :disabled="disabled" />
      </ElTabPane>
      <ElTabPane label="月" name="month">
        <MonthUI v-model="month" :disabled="disabled" />
      </ElTabPane>
      <ElTabPane label="周" name="week">
        <WeekUI v-model="week" :day="day" :disabled="disabled" />
      </ElTabPane>
      <ElTabPane v-if="!hideYear && !hideSecond" label="年" name="year">
        <YearUI v-model="year" :disabled="disabled" />
      </ElTabPane>
    </ElTabs>
    <!-- 执行时间预览 -->
    <div class="time-list-container">
      <div class="time-inputs">
        <ElInput
          v-model="inputValues.minute"
          @blur="onInputBlur"
          :disabled="disabled"
        >
          <template #prepend>
            <span class="label-text" @click="activeKey = 'minute'">分</span>
          </template>
        </ElInput>
        <ElInput
          v-model="inputValues.hour"
          @blur="onInputBlur"
          :disabled="disabled"
        >
          <template #prepend>
            <span class="label-text" @click="activeKey = 'hour'">时</span>
          </template>
        </ElInput>
        <ElInput
          v-model="inputValues.day"
          @blur="onInputBlur"
          :disabled="disabled"
        >
          <template #prepend>
            <span class="label-text" @click="activeKey = 'day'">日</span>
          </template>
        </ElInput>
        <ElInput
          v-model="inputValues.month"
          @blur="onInputBlur"
          :disabled="disabled"
        >
          <template #prepend>
            <span class="label-text" @click="activeKey = 'month'">月</span>
          </template>
        </ElInput>
        <ElInput
          v-model="inputValues.week"
          @blur="onInputBlur"
          :disabled="disabled"
        >
          <template #prepend>
            <span class="label-text" @click="activeKey = 'week'">周</span>
          </template>
        </ElInput>
      </div>

      <ElInput
        v-model="inputValues.cron"
        @blur="onInputCronBlur"
        :disabled="disabled"
        class="cron-expression-input"
      >
        <template #prepend>
          <ElTooltip title="Cron表达式">Cron表达式</ElTooltip>
        </template>
      </ElInput>
    </div>

    <div class="preview-container">
      <div class="preview-label">近十次执行时间（不含年）</div>
      <ElInput
        v-model="preTimeList"
        type="textarea"
        :rows="5"
        readonly
        class="preview-textarea"
      />
    </div>
  </div>
</template>

<style scoped lang="css">
.cron-inner {
  padding: 0 16px 16px;
  background: #fff;
}

.time-list-container {
  margin-bottom: 16px;
}

.time-inputs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.label-text {
  padding: 0 4px;
  cursor: pointer;
  user-select: none;
}

.label-text:hover {
  color: var(--el-color-primary);
}

.cron-expression-input {
  margin-bottom: 12px;
}

.preview-container {
  margin-top: 16px;
}

.preview-label {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.preview-textarea {
  width: 100%;
}
</style>
