import { defineAsyncComponent } from 'vue';

export const PostSelector = defineAsyncComponent(() =>
  import('./post-selector.vue').then((module) => module.default),
);
