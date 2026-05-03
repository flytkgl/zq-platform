<script setup lang="ts">
import { computed, ref } from 'vue';

import {
  AppWindow,
  CircleCheck,
  ExternalLink,
  FileText,
  LayoutDashboard,
  Maximize,
  Minimize,
} from '@vben/icons';
import { useI18n } from '@vben/locales';

import { ElButton, ElCard, ElEmpty } from 'element-plus';

export interface SystemSummaryData {
  type: 'system_summary';
  title: string;
  data: {
    app?: {
      code: string;
      description: string;
      icon: string;
      id: string;
      link: string;
      name: string;
    };
    base_url?: string;
    created_at: string;
    dashboard?: {
      code: string;
      description: string;
      icon: string;
      id: string;
      link: string;
      name: string;
    };
    forms: Array<{
      code: string;
      description: string;
      icon: string;
      id: string;
      link: string;
      name: string;
    }>;
    statistics?: {
      forms_count: number;
      has_app: boolean;
      has_dashboard: boolean;
      total_modules: number;
    };
    title: string;
  };
  nodeId: string;
}

const props = defineProps<{
  data?: SystemSummaryData;
  visible: boolean;
}>();

const emit = defineEmits<{
  close: [];
  confirm: [data: any];
  'update:visible': [value: boolean];
}>();

const { t } = useI18n();

// 全屏状态
const isFullscreen = ref(false);

// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
});

const summaryData = computed(() => props.data?.data || ({} as any));
const statistics = computed(() => summaryData.value.statistics);
const app = computed(() => summaryData.value.app);
const forms = computed(() => summaryData.value.forms || []);
const dashboard = computed(() => summaryData.value.dashboard);

const handleConfirm = () => {
  emit('confirm', summaryData.value);
};

const handleClose = () => {
  dialogVisible.value = false;
  emit('close');
};

const openLink = (link: string) => {
  if (link) {
    const baseUrl = summaryData.value.base_url || '';
    const fullUrl = baseUrl ? `${baseUrl}${link}` : link;
    window.open(fullUrl, '_blank');
  }
};
</script>

<template>
  <div
    v-if="visible"
    class="border-border bg-card flex flex-col rounded-lg"
    :class="[isFullscreen ? 'fixed inset-0 z-50 ml-0' : 'ml-3 h-full w-full']"
  >
    <!-- 头部 -->
    <div
      class="border-border bg-muted/50 flex items-center justify-between border-b px-4 py-3"
    >
      <div class="text-foreground font-medium">
        {{ data?.title || t('ai.systemSummary.title') }}
      </div>
      <div class="flex items-center gap-2">
        <ElButton size="small" @click="handleClose">
          {{ t('common.cancel') }}
        </ElButton>
        <ElButton size="small" type="primary" @click="handleConfirm">
          <CircleCheck class="mr-1 size-4" />
          {{ t('ai.systemSummary.complete') }}
        </ElButton>
        <ElButton
          link
          :icon="isFullscreen ? Minimize : Maximize"
          :title="isFullscreen ? '退出全屏' : '全屏'"
          @click="toggleFullscreen"
        />
      </div>
    </div>

    <!-- 内容 -->
    <div class="flex-1 overflow-auto p-6">
      <div
        class="mb-6 flex items-center gap-3 border-b border-green-200 pb-4 dark:border-green-800"
      >
        <div
          class="flex size-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900"
        >
          <CircleCheck class="size-6 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h2 class="text-xl font-semibold text-green-700 dark:text-green-300">
            {{ summaryData.title || t('ai.systemSummary.title') }}
          </h2>
          <p class="text-muted-foreground text-sm">
            {{ t('ai.systemSummary.subtitle') }}
          </p>
        </div>
      </div>

      <div v-if="statistics" class="mb-6 grid grid-cols-3 gap-4">
        <div
          class="rounded-lg border bg-blue-50 p-4 text-center dark:bg-blue-950"
        >
          <div class="text-3xl font-bold text-blue-600 dark:text-blue-400">
            {{ statistics.has_app ? 1 : 0 }}
          </div>
          <div class="text-muted-foreground mt-1 text-sm">
            {{ t('ai.systemSummary.app') }}
          </div>
        </div>
        <div
          class="rounded-lg border bg-purple-50 p-4 text-center dark:bg-purple-950"
        >
          <div class="text-3xl font-bold text-purple-600 dark:text-purple-400">
            {{ statistics.forms_count }}
          </div>
          <div class="text-muted-foreground mt-1 text-sm">
            {{ t('ai.systemSummary.formModules') }}
          </div>
        </div>
        <div
          class="rounded-lg border bg-orange-50 p-4 text-center dark:bg-orange-950"
        >
          <div class="text-3xl font-bold text-orange-600 dark:text-orange-400">
            {{ statistics.has_dashboard ? 1 : 0 }}
          </div>
          <div class="text-muted-foreground mt-1 text-sm">
            {{ t('ai.systemSummary.dashboard') }}
          </div>
        </div>
      </div>

      <div v-if="app" class="mb-6">
        <h3 class="mb-3 flex items-center gap-2 font-medium">
          <AppWindow class="size-5 text-blue-500" />
          {{ t('ai.systemSummary.appInfo') }}
        </h3>
        <ElCard
          shadow="hover"
          class="cursor-pointer"
          @click="openLink(app.link)"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex size-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900"
              >
                <AppWindow class="size-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div class="font-medium">{{ app.name }}</div>
                <div class="text-muted-foreground text-sm">
                  {{ app.description || app.code }}
                </div>
              </div>
            </div>
            <ElButton
              v-if="app.link"
              type="primary"
              link
              @click.stop="openLink(app.link)"
            >
              <ExternalLink class="mr-1 size-4" />
              {{ t('ai.systemSummary.visit') }}
            </ElButton>
          </div>
        </ElCard>
      </div>

      <div v-if="forms.length > 0" class="mb-6">
        <h3 class="mb-3 flex items-center gap-2 font-medium">
          <FileText class="size-5 text-purple-500" />
          {{ t('ai.systemSummary.formModulesTitle') }}
          <span class="text-muted-foreground text-sm">({{ forms.length }})</span>
        </h3>
        <div class="space-y-3">
          <ElCard
            v-for="form in forms"
            :key="form.id || form.code"
            shadow="hover"
            class="cursor-pointer"
            @click="openLink(form.link)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div
                  class="flex size-10 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900"
                >
                  <FileText
                    class="size-5 text-purple-600 dark:text-purple-400"
                  />
                </div>
                <div>
                  <div class="font-medium">{{ form.name }}</div>
                  <div class="text-muted-foreground text-sm">
                    {{ form.description || form.code }}
                  </div>
                </div>
              </div>
              <ElButton
                v-if="form.link"
                type="primary"
                link
                @click.stop="openLink(form.link)"
              >
                <ExternalLink class="mr-1 size-4" />
                {{ t('ai.systemSummary.visit') }}
              </ElButton>
            </div>
          </ElCard>
        </div>
      </div>

      <div v-if="dashboard" class="mb-6">
        <h3 class="mb-3 flex items-center gap-2 font-medium">
          <LayoutDashboard class="size-5 text-orange-500" />
          {{ t('ai.systemSummary.dashboardTitle') }}
        </h3>
        <ElCard
          shadow="hover"
          class="cursor-pointer"
          @click="openLink(dashboard.link)"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex size-10 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900"
              >
                <LayoutDashboard
                  class="size-5 text-orange-600 dark:text-orange-400"
                />
              </div>
              <div>
                <div class="font-medium">{{ dashboard.name }}</div>
                <div class="text-muted-foreground text-sm">
                  {{ dashboard.description || dashboard.code }}
                </div>
              </div>
            </div>
            <ElButton
              v-if="dashboard.link"
              type="primary"
              link
              @click.stop="openLink(dashboard.link)"
            >
              <ExternalLink class="mr-1 size-4" />
              {{ t('ai.systemSummary.visit') }}
            </ElButton>
          </div>
        </ElCard>
      </div>

      <ElEmpty
        v-if="!app && forms.length === 0 && !dashboard"
        :description="t('ai.systemSummary.noData')"
      />
    </div>
  </div>
</template>
