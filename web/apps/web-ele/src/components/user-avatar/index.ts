import { defineAsyncComponent } from 'vue';

export const UserAvatar = defineAsyncComponent(() =>
  import('./index.vue').then((module) => module.default),
);
