<script lang="ts" setup>
/**
 * 应用设置面板
 * 用于配置应用设置，包括应用配置、Logo配置、内置主题和布局
 */
import type { BuiltinThemeType, LayoutType, ThemeModeType } from '@vben/types';

import { computed, ref, watch } from 'vue';

import { Maximize, Minimize } from '@vben/icons';
import {
  Block,
  BuiltinTheme,
  Layout,
  Theme,
} from '@vben/layouts/preferences-blocks';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDivider,
  ElInput,
  ElMessage,
  ElOption,
  ElScrollbar,
  ElSelect,
  ElSwitch,
} from 'element-plus';

import { uploadFile } from '#/api/core/file';
import { getFileUrlPublic } from '#/composables/useFileUrl';

// 应用设置数据接口
export interface AppSettingsData {
  type: 'app_settings';
  title: string;
  data: {
    app?: {
      defaultHomePath?: string;
      dynamicTitle?: boolean;
      enableCheckUpdates?: boolean;
      enablePreferences?: boolean;
      layout?: string;
      locale?: string;
      name?: string;
      watermark?: boolean;
      watermarkContent?: string;
    };
    breadcrumb?: Record<string, any>;
    copyright?: Record<string, any>;
    footer?: Record<string, any>;
    header?: Record<string, any>;
    logo?: {
      enable?: boolean;
      fit?: string;
      source?: string;
    };
    navigation?: Record<string, any>;
    shortcutKeys?: Record<string, any>;
    sidebar?: Record<string, any>;
    tabbar?: Record<string, any>;
    theme?: {
      builtinType?: string;
      colorPrimary?: string;
      mode?: string;
      radius?: string;
      semiDarkHeader?: boolean;
      semiDarkSidebar?: boolean;
    };
    transition?: Record<string, any>;
    widget?: Record<string, any>;
  };
  nodeId?: string;
  layoutOptions?: Array<{ label: string; value: string }>;
  themeOptions?: Array<{ label: string; value: string }>;
}

interface Props {
  visible: boolean;
  settings?: AppSettingsData;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  confirm: [data: Record<string, any>];
  'update:visible': [value: boolean];
}>();

// 全屏状态
const isFullscreen = ref(false);

// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

// 应用配置
const appName = ref('');
const appDefaultHomePath = ref('/analytics');
const appEnablePreferences = ref(true);
const appLayout = ref<LayoutType>('sidebar-nav');

// Logo配置
const logoEnable = ref(true);
const logoSource = ref('');
const logoFit = ref('contain');
const logoDisplayUrl = ref('');

// 主题配置
const themeMode = ref<ThemeModeType>('light');
const themeBuiltinType = ref<BuiltinThemeType>('default');
const themeColorPrimary = ref('hsl(212 100% 45%)');
const themeSemiDarkSidebar = ref(false);
const themeSemiDarkHeader = ref(false);

// 适应方式选项
const fitOptions = computed(() => [
  { label: $t('ai-platform.appSettings.fitOptions.contain'), value: 'contain' },
  { label: $t('ai-platform.appSettings.fitOptions.cover'), value: 'cover' },
  { label: $t('ai-platform.appSettings.fitOptions.fill'), value: 'fill' },
  { label: $t('ai-platform.appSettings.fitOptions.none'), value: 'none' },
  {
    label: $t('ai-platform.appSettings.fitOptions.scale-down'),
    value: 'scale-down',
  },
]);

// 面板标题
const panelTitle = computed(() => {
  return props.settings?.title || $t('ai-platform.appSettings.title');
});

// 监听设置数据变化
watch(
  () => props.settings,
  (newSettings) => {
    if (newSettings?.data) {
      const data = newSettings.data;

      // 应用配置
      appName.value = data.app?.name || '';
      appDefaultHomePath.value = data.app?.defaultHomePath || '/analytics';
      appEnablePreferences.value = data.app?.enablePreferences ?? true;
      appLayout.value = (data.app?.layout || 'sidebar-nav') as LayoutType;

      // Logo配置
      logoEnable.value = data.logo?.enable ?? true;
      logoSource.value = data.logo?.source || '';
      logoFit.value = data.logo?.fit || 'contain';
      loadLogoDisplayUrl(logoSource.value);

      // 主题配置
      themeMode.value = (data.theme?.mode || 'light') as ThemeModeType;
      themeBuiltinType.value = (data.theme?.builtinType ||
        'default') as BuiltinThemeType;
      themeColorPrimary.value = data.theme?.colorPrimary || 'hsl(212 100% 45%)';
      themeSemiDarkSidebar.value = data.theme?.semiDarkSidebar ?? false;
      themeSemiDarkHeader.value = data.theme?.semiDarkHeader ?? false;
    }
  },
  { immediate: true },
);

// 监听logoSource变化，加载显示URL
watch(logoSource, (newSource) => {
  loadLogoDisplayUrl(newSource);
});

// 判断是否为文件ID
function isFileId(value: string): boolean {
  return (
    /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i.test(value) ||
    /^\d+$/.test(value) ||
    /^[\w-]{10,30}$/.test(value)
  );
}

// 加载Logo显示URL
function loadLogoDisplayUrl(source: string) {
  if (!source) {
    logoDisplayUrl.value = '';
    return;
  }
  if (
    source.startsWith('http://') ||
    source.startsWith('https://') ||
    source.startsWith('/') ||
    source.startsWith('data:')
  ) {
    logoDisplayUrl.value = source;
    return;
  }
  if (isFileId(source)) {
    logoDisplayUrl.value = getFileUrlPublic(source);
    return;
  }
  logoDisplayUrl.value = source;
}

// 文件上传
const uploadInputRef = ref<HTMLInputElement>();

function openFileSelector() {
  uploadInputRef.value?.click();
}

async function handleFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  try {
    const response = await uploadFile(file, {
      isPublic: true,
      source: 'avatar',
    });
    if (response?.id) {
      logoSource.value = getFileUrlPublic(String(response.id));
    }
  } catch {
    ElMessage.error($t('ui-config.loadError'));
  }
  target.value = '';
}

function clearLogo() {
  logoSource.value = '';
}

// 构建设置数据
function buildSettingsData(): Record<string, any> {
  return {
    app: {
      name: appName.value,
      defaultHomePath: appDefaultHomePath.value,
      enablePreferences: appEnablePreferences.value,
      layout: appLayout.value,
    },
    logo: {
      enable: logoEnable.value,
      source: logoSource.value,
      fit: logoFit.value,
    },
    theme: {
      mode: themeMode.value,
      builtinType: themeBuiltinType.value,
      colorPrimary: themeColorPrimary.value,
      semiDarkSidebar: themeSemiDarkSidebar.value,
      semiDarkHeader: themeSemiDarkHeader.value,
    },
    // 保留原有的其他配置
    sidebar: props.settings?.data?.sidebar,
    header: props.settings?.data?.header,
    footer: props.settings?.data?.footer,
    copyright: props.settings?.data?.copyright,
    navigation: props.settings?.data?.navigation,
    tabbar: props.settings?.data?.tabbar,
    breadcrumb: props.settings?.data?.breadcrumb,
    transition: props.settings?.data?.transition,
    widget: props.settings?.data?.widget,
    shortcutKeys: props.settings?.data?.shortcutKeys,
  };
}

// 确认并继续
function handleConfirm() {
  emit('confirm', buildSettingsData());
}

// 关闭
function handleClose() {
  emit('update:visible', false);
  emit('close');
}
</script>

<template>
  <div
    v-if="visible"
    class="app-settings-panel border-border bg-card flex flex-col rounded-lg"
    :class="[isFullscreen ? 'fixed inset-0 z-50 ml-0' : 'ml-3 h-full w-full']"
  >
    <!-- 头部 -->
    <div
      class="border-border bg-muted/50 flex items-center justify-between border-b px-4 py-3"
    >
      <div class="text-foreground font-medium">
        {{ panelTitle }}
      </div>
      <div class="flex items-center gap-2">
        <ElButton size="small" @click="handleClose">
          {{ $t('common.cancel') }}
        </ElButton>
        <ElButton size="small" type="primary" @click="handleConfirm">
          {{ $t('common.confirmAndContinue') }}
        </ElButton>
        <ElButton
          link
          :icon="isFullscreen ? Minimize : Maximize"
          :title="isFullscreen ? '退出全屏' : '全屏'"
          @click="toggleFullscreen"
        />
      </div>
    </div>

    <!-- 内容区域 -->
    <ElScrollbar class="flex-1">
      <div class="grid grid-cols-2 gap-6 p-6">
        <!-- 左列：应用配置 + Logo配置 -->
        <div class="space-y-6">
          <!-- 应用配置 -->
          <div class="config-section">
            <h4 class="mb-4 text-sm font-semibold">
              {{ $t('ai-platform.appSettings.appConfig') }}
            </h4>
            <div class="space-y-4">
              <Block :title="$t('ai-platform.appSettings.appName')">
                <ElInput
                  v-model="appName"
                  :placeholder="
                    $t('ai-platform.appSettings.appNamePlaceholder')
                  "
                  clearable
                />
              </Block>

              <Block :title="$t('ai-platform.appSettings.defaultHomePath')">
                <ElInput
                  v-model="appDefaultHomePath"
                  :placeholder="
                    $t('ai-platform.appSettings.defaultHomePathPlaceholder')
                  "
                  clearable
                />
              </Block>

              <Block :title="$t('ai-platform.appSettings.enablePreferences')">
                <ElSwitch v-model="appEnablePreferences" />
              </Block>
            </div>
          </div>

          <ElDivider />

          <!-- Logo配置 -->
          <div class="config-section">
            <h4 class="mb-4 text-sm font-semibold">
              {{ $t('ai-platform.appSettings.logoConfig') }}
            </h4>
            <div class="space-y-4">
              <Block :title="$t('ai-platform.appSettings.logoEnable')">
                <ElSwitch v-model="logoEnable" />
              </Block>

              <template v-if="logoEnable">
                <Block :title="$t('ai-platform.appSettings.logoSource')">
                  <div class="flex flex-col gap-4">
                    <!-- Logo 预览和上传 -->
                    <div class="logo-preview-container flex">
                      <div class="flex items-center gap-4">
                        <div>
                          <div
                            v-if="logoDisplayUrl"
                            class="logo-preview"
                            @click="openFileSelector"
                          >
                            <img
                              :src="logoDisplayUrl"
                              alt="Logo"
                              class="logo-image"
                            />
                            <div class="logo-overlay">
                              <span class="text-sm text-white">{{
                                $t('common.replace')
                              }}</span>
                            </div>
                          </div>
                          <div
                            v-else
                            class="logo-placeholder"
                            @click="openFileSelector"
                          >
                            <span class="text-muted-foreground text-sm">{{
                              $t(
                                'ai-platform.appSettings.logoSourcePlaceholder',
                              )
                            }}</span>
                          </div>
                        </div>

                        <ElButton
                          v-if="logoDisplayUrl"
                          size="small"
                          @click="clearLogo"
                        >
                          {{ $t('common.clear') }}
                        </ElButton>
                      </div>
                    </div>
                    <input
                      ref="uploadInputRef"
                      type="file"
                      accept="image/*"
                      style="display: none"
                      @change="handleFileInputChange"
                    />
                    <ElInput
                      v-model="logoSource"
                      :placeholder="
                        $t('ai-platform.appSettings.logoSourcePlaceholder')
                      "
                      clearable
                    />
                  </div>
                </Block>

                <Block :title="$t('ai-platform.appSettings.logoFit')">
                  <ElSelect v-model="logoFit" class="w-full">
                    <ElOption
                      v-for="item in fitOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </ElSelect>
                </Block>
              </template>
            </div>
          </div>
        </div>

        <!-- 右列：布局配置 + 主题配置 -->
        <div class="space-y-6">
          <!-- 布局配置 -->
          <div class="config-section">
            <h4 class="mb-4 text-sm font-semibold">
              {{ $t('ai-platform.appSettings.layoutConfig') }}
            </h4>
            <div class="space-y-4">
              <Block :title="$t('ai-platform.appSettings.layout')">
                <Layout v-model="appLayout" />
              </Block>
            </div>
          </div>

          <ElDivider />

          <!-- 主题配置 -->
          <div class="config-section">
            <h4 class="mb-4 text-sm font-semibold">
              {{ $t('ai-platform.appSettings.themeConfig') }}
            </h4>
            <div class="space-y-4">
              <Block :title="$t('ai-platform.appSettings.themeMode')">
                <Theme
                  v-model="themeMode"
                  v-model:theme-semi-dark-sidebar="themeSemiDarkSidebar"
                  v-model:theme-semi-dark-header="themeSemiDarkHeader"
                />
              </Block>

              <Block :title="$t('ai-platform.appSettings.builtinTheme')">
                <BuiltinTheme
                  v-model="themeBuiltinType"
                  v-model:theme-color-primary="themeColorPrimary"
                  :is-dark="themeMode === 'dark'"
                />
              </Block>
            </div>
          </div>
        </div>
      </div>
    </ElScrollbar>
  </div>
</template>

<style scoped>
.app-settings-panel {
  min-width: 600px;
}

.logo-preview-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.logo-preview {
  position: relative;
  width: 100px;
  height: 100px;
  border: 1px solid hsl(var(--border));
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(0 0 0 / 50%);
  opacity: 0;
  transition: opacity 0.2s;
}

.logo-preview:hover .logo-overlay {
  opacity: 1;
}

.logo-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border: 2px dashed hsl(var(--border));
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.logo-placeholder:hover {
  border-color: hsl(var(--primary));
}
</style>
