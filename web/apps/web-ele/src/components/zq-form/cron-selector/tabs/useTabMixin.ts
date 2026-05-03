/**
 * 主要用于日和星期的互斥使用
 */
import { computed, inject, reactive, ref, unref, watch } from 'vue';

export enum TypeEnum {
  every = 'EVERY',
  last = 'LAST',
  loop = 'LOOP',
  range = 'RANGE',
  specify = 'SPECIFY',
  unset = 'UNSET',
  work = 'WORK',
}

export interface UseTabOptions {
  defaultValue?: string;
  defaultType?: TypeEnum;
  minValue: number;
  maxValue: number;
  valueRange: { end: number; start: number };
  valueLoop: { interval: number; start: number };
  valueWeek?: Record<string, any>;
  valueWork?: number;
  disabled?: (() => boolean) | boolean;
}

export interface UseTabProps {
  value: string;
  disabled: boolean;
  [key: string]: any;
}

/**
 * 公共 props
 */
export function useTabProps(options?: Partial<UseTabOptions>) {
  const defaultValue = options?.defaultValue ?? '?';
  return {
    modelValue: {
      type: String,
      default: defaultValue,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    ...options?.defaultValue,
  };
}

/**
 * 公共 setup
 */
export function useTabSetup(props: any, context: any, options: UseTabOptions) {
  const { emit } = context;
  const prefixCls = inject('prefixCls', 'cron');
  const defaultValue = ref(options?.defaultValue ?? '?');

  // 类型
  const type = ref(options.defaultType ?? TypeEnum.every);
  const valueList = ref<any[]>([]);

  // 对于不同的类型，所定义的值也有所不同
  const valueRange = reactive(options.valueRange);
  const valueLoop = reactive(options.valueLoop);
  const valueWeek = reactive(options.valueWeek || {});
  const valueWork = ref(options.valueWork);
  const maxValue = ref(options.maxValue);
  const minValue = ref(options.minValue);

  // 根据不同的类型计算出的value
  const computeValue = computed(() => {
    const valueArray: any[] = [];
    switch (type.value) {
      case TypeEnum.every: {
        valueArray.push('*');
        break;
      }
      case TypeEnum.last: {
        valueArray.push('L');
        break;
      }
      case TypeEnum.loop: {
        valueArray.push(`${valueLoop.start}/${valueLoop.interval}`);
        break;
      }
      case TypeEnum.range: {
        valueArray.push(`${valueRange.start}-${valueRange.end}`);
        break;
      }
      case TypeEnum.specify: {
        if (valueList.value.length === 0) {
          valueList.value.push(minValue.value);
        }
        valueArray.push(valueList.value.join(','));
        break;
      }
      case TypeEnum.unset: {
        valueArray.push('?');
        break;
      }
      case TypeEnum.work: {
        valueArray.push(`${valueWork.value}W`);
        break;
      }
      default: {
        valueArray.push(defaultValue.value);
        break;
      }
    }
    return valueArray.length > 0 ? valueArray.join('') : defaultValue.value;
  });

  // 指定值范围区间，介于最小值和最大值之间
  const specifyRange = computed(() => {
    const range: number[] = [];
    if (maxValue.value != null) {
      for (let i = minValue.value; i <= maxValue.value; i++) {
        range.push(i);
      }
    }
    return range;
  });

  watch(
    () => props.modelValue,
    (val) => {
      if (val !== computeValue.value) {
        parseValue(val);
      }
    },
    { immediate: true },
  );

  watch(computeValue, (v) => updateValue(v));

  function updateValue(value: string) {
    emit('update:modelValue', value);
  }

  /**
   * parseValue
   */
  function parseValue(value: string) {
    if (value === computeValue.value) {
      return;
    }
    try {
      if (!value || value === defaultValue.value) {
        type.value = TypeEnum.every;
      } else if (value.includes('?')) {
        type.value = TypeEnum.unset;
      } else if (value.includes('-')) {
        type.value = TypeEnum.range;
        const values = value.split('-');
        if (values.length >= 2) {
          valueRange.start = Number.parseInt(values[0]);
          valueRange.end = Number.parseInt(values[1]);
        }
      } else if (value.includes('/')) {
        type.value = TypeEnum.loop;
        const values = value.split('/');
        if (values.length >= 2) {
          valueLoop.start = value[0] === '*' ? 0 : Number.parseInt(values[0]);
          valueLoop.interval = Number.parseInt(values[1]);
        }
      } else if (value.includes('W')) {
        type.value = TypeEnum.work;
        const values = value.split('W');
        if (!values[0] && !isNaN(Number.parseInt(values[0]))) {
          valueWork.value = Number.parseInt(values[0]);
        }
      } else if (value.includes('L')) {
        type.value = TypeEnum.last;
      } else if (value.includes(',') || !isNaN(Number.parseInt(value))) {
        type.value = TypeEnum.specify;
        valueList.value = value.split(',').map((item) => Number.parseInt(item));
      } else {
        type.value = TypeEnum.every;
      }
    } catch {
      type.value = TypeEnum.every;
    }
  }

  const beforeRadioAttrs = computed(() => ({
    disabled: props.disabled || unref(options.disabled),
  }));

  const inputNumberAttrs = computed(() => ({
    max: maxValue.value,
    min: minValue.value,
  }));

  const typeRangeAttrs = computed(() => ({
    disabled:
      type.value !== TypeEnum.range ||
      props.disabled ||
      unref(options.disabled),
    ...inputNumberAttrs.value,
  }));

  const typeLoopAttrs = computed(() => ({
    disabled:
      type.value !== TypeEnum.loop || props.disabled || unref(options.disabled),
    ...inputNumberAttrs.value,
  }));

  const typeSpecifyAttrs = computed(() => ({
    disabled:
      type.value !== TypeEnum.specify ||
      props.disabled ||
      unref(options.disabled),
  }));

  return {
    type,
    TypeEnum,
    prefixCls,
    defaultValue,
    valueRange,
    valueLoop,
    valueWeek,
    valueList,
    valueWork,
    maxValue,
    minValue,
    computeValue,
    specifyRange,
    updateValue,
    parseValue,
    beforeRadioAttrs,
    inputNumberAttrs,
    typeRangeAttrs,
    typeLoopAttrs,
    typeSpecifyAttrs,
  };
}
