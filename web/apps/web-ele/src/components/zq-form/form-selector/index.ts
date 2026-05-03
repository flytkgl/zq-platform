import { defineAsyncComponent } from 'vue';

export const FormSelector = defineAsyncComponent(() =>
  import('./form-selector.vue').then((module) => module.default),
);

export * from './types';
