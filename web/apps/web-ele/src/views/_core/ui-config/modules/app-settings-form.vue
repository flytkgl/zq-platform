<script lang="ts" setup>
import type { LocaleType } from '@vben/locales';

import type { PreferencesConfig } from '#/api/core/ui-config';

import { onMounted, ref, watch } from 'vue';

import {
  Block,
  Copyright,
  Footer,
  General,
  GlobalShortcutKeys,
  InputItem,
  SwitchItem,
} from '@vben/layouts/preferences-blocks';
import { $t, getSystemLanguage, loadLocaleMessages } from '@vben/locales';
import { preferences, updatePreferences } from '@vben/preferences';

import {
  ElButton,
  ElDivider,
  ElInput,
  ElMessage,
  ElOption,
  ElSelect,
} from 'element-plus';

import { uploadFile } from '#/api/core/file';
import {
  getPreferencesConfigApi,
  updatePreferencesConfigApi,
} from '#/api/core/ui-config';
import { getFileUrlPublic } from '#/composables/useFileUrl';
import { overridesPreferences } from '#/preferences';
import { useAppContextStore } from '#/store/app-context';

defineOptions({ name: 'AppSettingsForm' });

const appContextStore = useAppContextStore();

// 获取当前应用ID（子应用模式下返回应用ID，主应用模式下返回 undefined）
function getCurrentApplicationId(): string | undefined {
  return appContextStore.currentApp?.id;
}

const loading = ref(false);

const appName = ref('');
const appLocale = ref<LocaleType>('zh-CN');
const appDynamicTitle = ref(true);
const appWatermark = ref(false);
const appWatermarkContent = ref('');
const appEnableCheckUpdates = ref(true);
const appDefaultHomePath = ref('/analytics');
const appEnablePreferences = ref(true);

const footerEnable = ref(true);
const footerFixed = ref(true);

const copyrightEnable = ref(true);
const copyrightCompanyName = ref('');
const copyrightCompanySiteLink = ref('');
const copyrightDate = ref('');
const copyrightIcp = ref('');
const copyrightIcpLink = ref('');
const copyrightPoliceIcp = ref('');
const copyrightPoliceIcpLink = ref('');
const copyrightLoginOnly = ref(true);

const logoEnable = ref(true);
const logoSource = ref('');
const logoFit = ref('contain');

const shortcutKeysEnable = ref(true);
const shortcutKeysGlobalSearch = ref(true);
const shortcutKeysGlobalLogout = ref(true);
const shortcutKeysGlobalLockScreen = ref(true);

const fitOptions = [
  { label: $t('ui-config.logo.fitOptions.contain'), value: 'contain' },
  { label: $t('ui-config.logo.fitOptions.cover'), value: 'cover' },
  { label: $t('ui-config.logo.fitOptions.fill'), value: 'fill' },
  { label: $t('ui-config.logo.fitOptions.none'), value: 'none' },
  { label: $t('ui-config.logo.fitOptions.scale-down'), value: 'scale-down' },
];

function getDefaultConfig() {
  const overrides = overridesPreferences as Record<string, any>;
  return {
    app: {
      name: overrides.app?.name || preferences.app.name || '',
      locale: overrides.app?.locale || preferences.app.locale || 'zh-CN',
      dynamicTitle:
        overrides.app?.dynamicTitle ?? preferences.app.dynamicTitle ?? true,
      watermark: overrides.app?.watermark ?? preferences.app.watermark ?? false,
      watermarkContent:
        overrides.app?.watermarkContent ||
        preferences.app.watermarkContent ||
        '',
      enableCheckUpdates:
        overrides.app?.enableCheckUpdates ??
        preferences.app.enableCheckUpdates ??
        true,
      defaultHomePath:
        overrides.app?.defaultHomePath ||
        preferences.app.defaultHomePath ||
        '/page-render/main_home',
      enablePreferences: overrides.app?.enablePreferences ?? true,
    },
    footer: {
      enable: overrides.footer?.enable ?? preferences.footer.enable ?? true,
      fixed: overrides.footer?.fixed ?? preferences.footer.fixed ?? true,
    },
    copyright: {
      enable:
        overrides.copyright?.enable ?? preferences.copyright.enable ?? true,
      companyName:
        overrides.copyright?.companyName ||
        preferences.copyright.companyName ||
        '',
      companySiteLink:
        overrides.copyright?.companySiteLink ||
        preferences.copyright.companySiteLink ||
        '',
      date: overrides.copyright?.date || preferences.copyright.date || '',
      icp: overrides.copyright?.icp || preferences.copyright.icp || '',
      icpLink:
        overrides.copyright?.icpLink || preferences.copyright.icpLink || '',
      policeIcp:
        overrides.copyright?.policeIcp || preferences.copyright.policeIcp || '',
      policeIcpLink:
        overrides.copyright?.policeIcpLink || preferences.copyright.policeIcpLink || '',
      loginOnly:
        overrides.copyright?.loginOnly ?? preferences.copyright.loginOnly ?? true,
    },
    logo: {
      enable: overrides.logo?.enable ?? preferences.logo.enable ?? true,
      source: overrides.logo?.source || preferences.logo.source || '',
      fit: overrides.logo?.fit || preferences.logo.fit || 'contain',
    },
    shortcutKeys: {
      enable:
        overrides.shortcutKeys?.enable ??
        preferences.shortcutKeys.enable ??
        true,
      globalSearch:
        overrides.shortcutKeys?.globalSearch ??
        preferences.shortcutKeys.globalSearch ??
        true,
      globalLogout:
        overrides.shortcutKeys?.globalLogout ??
        preferences.shortcutKeys.globalLogout ??
        true,
      globalLockScreen:
        overrides.shortcutKeys?.globalLockScreen ??
        preferences.shortcutKeys.globalLockScreen ??
        true,
    },
  };
}

async function loadConfig() {
  loading.value = true;
  try {
    const applicationId = getCurrentApplicationId();
    const data = await getPreferencesConfigApi(applicationId);
    const defaults = getDefaultConfig();

    appName.value = data?.app?.name || defaults.app.name;
    appLocale.value = (data?.app?.locale || defaults.app.locale) as LocaleType;
    appDynamicTitle.value =
      data?.app?.dynamicTitle ?? defaults.app.dynamicTitle;
    appWatermark.value = data?.app?.watermark ?? defaults.app.watermark;
    appWatermarkContent.value =
      data?.app?.watermarkContent || defaults.app.watermarkContent;
    appEnableCheckUpdates.value =
      data?.app?.enableCheckUpdates ?? defaults.app.enableCheckUpdates;
    appDefaultHomePath.value =
      data?.app?.defaultHomePath || defaults.app.defaultHomePath;
    appEnablePreferences.value =
      data?.app?.enablePreferences ?? defaults.app.enablePreferences;

    footerEnable.value = data?.footer?.enable ?? defaults.footer.enable;
    footerFixed.value = data?.footer?.fixed ?? defaults.footer.fixed;

    copyrightEnable.value =
      data?.copyright?.enable ?? defaults.copyright.enable;
    copyrightCompanyName.value =
      data?.copyright?.companyName || defaults.copyright.companyName;
    copyrightCompanySiteLink.value =
      data?.copyright?.companySiteLink || defaults.copyright.companySiteLink;
    copyrightDate.value = data?.copyright?.date || defaults.copyright.date;
    copyrightIcp.value = data?.copyright?.icp || defaults.copyright.icp;
    copyrightIcpLink.value =
      data?.copyright?.icpLink || defaults.copyright.icpLink;
    copyrightPoliceIcp.value =
      data?.copyright?.policeIcp || defaults.copyright.policeIcp;
    copyrightPoliceIcpLink.value =
      data?.copyright?.policeIcpLink || defaults.copyright.policeIcpLink;
    copyrightLoginOnly.value =
      data?.copyright?.loginOnly ?? defaults.copyright.loginOnly;

    logoEnable.value = data?.logo?.enable ?? defaults.logo.enable;
    logoSource.value = data?.logo?.source || defaults.logo.source;
    logoFit.value = data?.logo?.fit || defaults.logo.fit;

    shortcutKeysEnable.value =
      data?.shortcutKeys?.enable ?? defaults.shortcutKeys.enable;
    shortcutKeysGlobalSearch.value =
      data?.shortcutKeys?.globalSearch ?? defaults.shortcutKeys.globalSearch;
    shortcutKeysGlobalLogout.value =
      data?.shortcutKeys?.globalLogout ?? defaults.shortcutKeys.globalLogout;
    shortcutKeysGlobalLockScreen.value =
      data?.shortcutKeys?.globalLockScreen ??
      defaults.shortcutKeys.globalLockScreen;
  } catch {
    const defaults = getDefaultConfig();
    appName.value = defaults.app.name;
    appLocale.value = defaults.app.locale as LocaleType;
    logoEnable.value = defaults.logo.enable;
    logoSource.value = defaults.logo.source;
    logoFit.value = defaults.logo.fit;
  } finally {
    loading.value = false;
  }
}

// 获取带子应用前缀的首页路径
function getDefaultHomePathWithPrefix(): string {
  const path = appDefaultHomePath.value || '/analytics';
  const appCode = appContextStore.appCode;
  // 如果是子应用模式且路径不包含子应用前缀，自动添加
  if (appCode && !path.startsWith(`/app/${appCode}`)) {
    return `/app/${appCode}${path.startsWith('/') ? path : `/${path}`}`;
  }
  return path;
}

function buildConfig(): PreferencesConfig {
  return {
    app: {
      name: appName.value,
      locale: appLocale.value,
      dynamicTitle: appDynamicTitle.value,
      watermark: appWatermark.value,
      watermarkContent: appWatermarkContent.value,
      enableCheckUpdates: appEnableCheckUpdates.value,
      defaultHomePath: getDefaultHomePathWithPrefix(),
      enablePreferences: appEnablePreferences.value,
    },
    footer: {
      enable: footerEnable.value,
      fixed: footerFixed.value,
    },
    copyright: {
      enable: copyrightEnable.value,
      companyName: copyrightCompanyName.value,
      companySiteLink: copyrightCompanySiteLink.value,
      date: copyrightDate.value,
      icp: copyrightIcp.value,
      icpLink: copyrightIcpLink.value,
      policeIcp: copyrightPoliceIcp.value,
      policeIcpLink: copyrightPoliceIcpLink.value,
      loginOnly: copyrightLoginOnly.value,
    },
    logo: {
      enable: logoEnable.value,
      source: logoSource.value,
      fit: logoFit.value,
    },
    shortcutKeys: {
      enable: shortcutKeysEnable.value,
      globalSearch: shortcutKeysGlobalSearch.value,
      globalLogout: shortcutKeysGlobalLogout.value,
      globalLockScreen: shortcutKeysGlobalLockScreen.value,
    },
  };
}

function applyPreferences() {
  const config = buildConfig();
  updatePreferences({
    app: config.app,
    footer: config.footer,
    copyright: config.copyright,
    logo: config.logo,
    shortcutKeys: config.shortcutKeys,
  });
}

async function save() {
  if (loading.value) return;
  try {
    applyPreferences();

    if (appLocale.value !== preferences.app.locale) {
      // 如果是跟随系统，获取系统语言
      const actualLocale =
        appLocale.value === 'auto' ? getSystemLanguage() : appLocale.value;
      await loadLocaleMessages(actualLocale);
    }

    const applicationId = getCurrentApplicationId();
    const currentConfig = (await getPreferencesConfigApi(applicationId)) ?? {};
    const newConfig: PreferencesConfig = {
      ...currentConfig,
      ...buildConfig(),
    };
    await updatePreferencesConfigApi(newConfig, applicationId);
    ElMessage.success($t('ui-config.saveSuccess'));
  } catch {
    ElMessage.error($t('ui-config.saveError'));
  }
}

function reset() {
  loadConfig();
}

defineExpose({ reset, save });

function isFileId(value: string): boolean {
  // 支持多种ID格式：UUID、纯数字、nanoid（字母数字混合，通常21位）
  return (
    /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i.test(value) ||
    /^\d+$/.test(value) ||
    /^[\w-]{10,30}$/.test(value) // nanoid格式：字母数字下划线横杠，10-30位
  );
}

// Logo显示URL（响应式）
const logoDisplayUrl = ref('');

// 加载Logo URL（Logo是公开文件，无需认证）
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
    // Logo是公开文件，直接使用公开URL，无需临时token
    logoDisplayUrl.value = getFileUrlPublic(source);
    return;
  }
  logoDisplayUrl.value = source;
}

// 监听logoSource变化，加载显示URL
watch(
  logoSource,
  (newSource) => {
    loadLogoDisplayUrl(newSource);
  },
  { immediate: true },
);

const uploadInputRef = ref<HTMLInputElement>();

function openFileSelector() {
  uploadInputRef.value?.click();
}

async function handleFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  try {
    // Logo上传时设置为公开，这样无需认证即可访问
    const response = await uploadFile(file, {
      isPublic: true,
      source: 'avatar',
    });
    if (response && response.id) {
      // 保存公开文件的完整URL路径，这样layout和auth页面可以直接使用
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

onMounted(() => {
  loadConfig();
});
</script>

<template>
  <div v-loading="loading" class="grid grid-cols-3 gap-6 p-4">
    <!-- 第一列：应用配置 -->
    <div class="app-column">
      <Block :title="$t('ui-config.app.title')">
        <InputItem
          v-model="appName"
          :placeholder="$t('ui-config.app.namePlaceholder')"
        >
          {{ $t('ui-config.app.name') }}
        </InputItem>

        <InputItem
          v-model="appDefaultHomePath"
          :placeholder="$t('ui-config.app.defaultHomePathPlaceholder')"
        >
          {{ $t('ui-config.app.defaultHomePath') }}
        </InputItem>

        <SwitchItem v-model="appEnablePreferences">
          {{ $t('ui-config.app.enablePreferences') }}
        </SwitchItem>
      </Block>

      <Block :title="$t('preferences.footer.title')">
        <Footer
          v-model:footer-enable="footerEnable"
          v-model:footer-fixed="footerFixed"
        />
      </Block>

      <Block :title="$t('preferences.copyright.title')">
        <Copyright
          v-model:copyright-enable="copyrightEnable"
          v-model:copyright-login-only="copyrightLoginOnly"
          v-model:copyright-company-name="copyrightCompanyName"
          v-model:copyright-company-site-link="copyrightCompanySiteLink"
          v-model:copyright-date="copyrightDate"
          v-model:copyright-icp="copyrightIcp"
          v-model:copyright-icp-link="copyrightIcpLink"
          v-model:copyright-police-icp="copyrightPoliceIcp"
          v-model:copyright-police-icp-link="copyrightPoliceIcpLink"
          :disabled="false"
        />
      </Block>
    </div>

    <!-- 第二列：Logo配置 -->
    <div class="logo-column">
      <Block :title="$t('ui-config.logoConfig')">
        <SwitchItem v-model="logoEnable">
          {{ $t('ui-config.logo.enable') }}
        </SwitchItem>

        <template v-if="logoEnable">
          <ElDivider />

          <div class="mb-4">
            <div class="text-muted-foreground mb-2 text-sm">
              {{ $t('ui-config.logo.source') }}
            </div>
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
                        $t('ui-config.logo.sourcePlaceholder')
                      }}</span>
                    </div>
                  </div>

                  <ElButton
                    v-if="logoDisplayUrl"
                    size="small"
                    class="mt-2"
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
                :placeholder="$t('ui-config.logo.sourcePlaceholder')"
                clearable
              />
            </div>
          </div>

          <div class="mb-4">
            <div class="text-muted-foreground mb-2 text-sm">
              {{ $t('ui-config.logo.fit') }}
            </div>
            <ElSelect v-model="logoFit" class="w-full">
              <ElOption
                v-for="item in fitOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </ElSelect>
          </div>
        </template>
      </Block>
    </div>

    <!-- 第三列：快捷键 -->
    <div class="shortcut-column">
      <Block :title="$t('preferences.shortcutKeys.global')">
        <GlobalShortcutKeys
          v-model:shortcut-keys-enable="shortcutKeysEnable"
          v-model:shortcut-keys-global-search="shortcutKeysGlobalSearch"
          v-model:shortcut-keys-lock-screen="shortcutKeysGlobalLockScreen"
          v-model:shortcut-keys-logout="shortcutKeysGlobalLogout"
        />
      </Block>

      <Block :title="$t('preferences.general')">
        <General
          v-model:app-locale="appLocale"
          v-model:app-dynamic-title="appDynamicTitle"
          v-model:app-watermark="appWatermark"
          v-model:app-watermark-content="appWatermarkContent"
          v-model:app-enable-check-updates="appEnableCheckUpdates"
        />
      </Block>
    </div>
  </div>
</template>

<style scoped>
.app-column,
.logo-column,
.shortcut-column {
  min-width: 0;
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
