<script lang="ts" setup>
import type { MoneyInputEmits, MoneyInputProps } from './types';

import { computed, ref, watch } from 'vue';

import { ElInput, ElTooltip } from 'element-plus';

defineOptions({
  name: 'MoneyInput',
});

const props = withDefaults(defineProps<MoneyInputProps>(), {
  precision: 2,
  currencySymbol: '¥',
  showCurrency: true,
  showThousandSeparator: true,
  showCapital: false,
  disabled: false,
  readonly: false,
  placeholder: '请输入金额',
});

const emit = defineEmits<MoneyInputEmits>();

const inputValue = ref('');
const isFocused = ref(false);

const CAPITAL_DIGITS = [
  '零',
  '壹',
  '贰',
  '叁',
  '肆',
  '伍',
  '陆',
  '柒',
  '捌',
  '玖',
];
const CAPITAL_UNITS = ['', '拾', '佰', '仟'];
const CAPITAL_BIG_UNITS = ['', '万', '亿', '兆'];

const numberToCapital = (num: number): string => {
  if (num === 0) return '零元整';
  if (num < 0) return `负${numberToCapital(-num)}`;

  const numStr = num.toFixed(2);
  const [intPart, decPart] = numStr.split('.');

  let result = '';

  if (intPart && Number.parseInt(intPart, 10) > 0) {
    const intNum = Number.parseInt(intPart, 10);
    const intStr = intNum.toString();
    const len = intStr.length;

    let zeroFlag = false;

    for (let i = 0; i < len; i++) {
      const digit = Number.parseInt(intStr[i]!, 10);
      const pos = len - i - 1;
      const unitPos = pos % 4;
      const bigUnitPos = Math.floor(pos / 4);

      if (digit === 0) {
        zeroFlag = true;
        if (unitPos === 0 && bigUnitPos > 0) {
          result += CAPITAL_BIG_UNITS[bigUnitPos];
        }
      } else {
        if (zeroFlag) {
          result += '零';
          zeroFlag = false;
        }
        result +=
          (CAPITAL_DIGITS[digit] || '') + (CAPITAL_UNITS[unitPos] || '');
        if (unitPos === 0 && bigUnitPos > 0) {
          result += CAPITAL_BIG_UNITS[bigUnitPos];
        }
      }
    }
    result += '元';
  }

  if (decPart) {
    const jiao = Number.parseInt(decPart[0]!, 10);
    const fen = Number.parseInt(decPart[1]!, 10);

    if (jiao === 0 && fen === 0) {
      result += '整';
    } else {
      if (jiao > 0) {
        result += `${CAPITAL_DIGITS[jiao]}角`;
      } else if (result) {
        result += '零';
      }
      if (fen > 0) {
        result += `${CAPITAL_DIGITS[fen]}分`;
      }
    }
  } else {
    result += '整';
  }

  return result || '零元整';
};

const formatWithThousandSeparator = (value: string): string => {
  if (!value) return '';

  const parts = value.split('.');
  const intPart = parts[0]!.replaceAll(/\B(?=(\d{3})+(?!\d))/g, ',');

  if (parts.length > 1) {
    return `${intPart}.${parts[1]}`;
  }
  return intPart;
};

const displayValue = computed(() => {
  if (isFocused.value) {
    return inputValue.value;
  }

  if (!inputValue.value) return '';

  let result = inputValue.value;

  if (props.showThousandSeparator) {
    result = formatWithThousandSeparator(result);
  }

  return result;
});

const capitalValue = computed(() => {
  if (!props.showCapital || !inputValue.value) return '';

  const num = Number.parseFloat(inputValue.value);
  if (Number.isNaN(num)) return '';

  return numberToCapital(num);
});

const handleInput = (value: string) => {
  let cleanValue = value.replaceAll(/[^\d.-]/g, '');

  const parts = cleanValue.split('.');
  if (parts.length > 2) {
    cleanValue = `${parts[0]}.${parts.slice(1).join('')}`;
  }

  if (parts.length === 2 && parts[1]!.length > props.precision) {
    cleanValue = `${parts[0]}.${parts[1]!.slice(0, props.precision)}`;
  }

  inputValue.value = cleanValue;
};

const handleBlur = () => {
  isFocused.value = false;

  if (!inputValue.value) {
    emit('update:modelValue', '');
    emit('change', '');
    return;
  }

  let num = Number.parseFloat(inputValue.value);

  if (Number.isNaN(num)) {
    inputValue.value = '';
    emit('update:modelValue', '');
    emit('change', '');
    return;
  }

  if (props.min !== undefined && num < props.min) {
    num = props.min;
  }
  if (props.max !== undefined && num > props.max) {
    num = props.max;
  }

  const finalValue = num.toFixed(props.precision);
  inputValue.value = finalValue;

  emit('update:modelValue', num);
  emit('change', num);
};

const handleFocus = () => {
  isFocused.value = true;
};

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal === undefined || newVal === null || newVal === '') {
      inputValue.value = '';
      return;
    }

    const num = typeof newVal === 'string' ? Number.parseFloat(newVal) : newVal;
    if (!Number.isNaN(num)) {
      inputValue.value = num.toFixed(props.precision);
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="money-input-wrapper">
    <ElInput
      :model-value="displayValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
    >
      <template v-if="showCurrency" #prefix>
        <span class="text-[var(--el-text-color-regular)]">{{
          currencySymbol
        }}</span>
      </template>
    </ElInput>

    <ElTooltip
      v-if="showCapital && capitalValue"
      :content="capitalValue"
      placement="top"
    >
      <div class="mt-1 truncate text-xs text-[var(--el-text-color-secondary)]">
        {{ capitalValue }}
      </div>
    </ElTooltip>
  </div>
</template>

<style scoped>
.money-input-wrapper {
  width: 100%;
}
</style>
