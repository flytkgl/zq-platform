<script lang="ts" setup>
import type {
  BreadcrumbStyleType,
  BuiltinThemeType,
  ContentCompactType,
  LayoutHeaderMenuAlignType,
  LayoutHeaderModeType,
  LayoutType,
  NavigationStyleType,
  PreferencesButtonPositionType,
  ThemeModeType,
} from '@vben/types';

import type { PreferencesConfig } from '#/api/core/ui-config';

import { onMounted, ref } from 'vue';

import {
  Animation,
  Block,
  Breadcrumb,
  BuiltinTheme,
  ColorMode,
  Content,
  Header,
  Layout,
  Navigation,
  Radius,
  Sidebar,
  Tabbar,
  Theme,
  Widget,
} from '@vben/layouts/preferences-blocks';
import { $t } from '@vben/locales';
import {
  preferences,
  updatePreferences,
  usePreferences,
} from '@vben/preferences';

import { ElMessage } from 'element-plus';

import {
  getPreferencesConfigApi,
  updatePreferencesConfigApi,
} from '#/api/core/ui-config';
import { overridesPreferences } from '#/preferences';
import { useAppContextStore } from '#/store/app-context';

defineOptions({ name: 'UIPreferencesForm' });

const appContextStore = useAppContextStore();

// 获取当前应用ID（子应用模式下返回应用ID，主应用模式下返回 undefined）
function getCurrentApplicationId(): string | undefined {
  return appContextStore.currentApp?.id;
}

const loading = ref(false);

const { isDark, isFullContent, isHeaderNav, isMixedNav, isSideMode } =
  usePreferences();

const appLayout = ref<LayoutType>('sidebar-nav');
const appColorGrayMode = ref(false);
const appColorWeakMode = ref(false);
const appContentCompact = ref<ContentCompactType>('wide');
const appPreferencesButtonPosition = ref<PreferencesButtonPositionType>('auto');

const transitionProgress = ref(true);
const transitionName = ref('fade-slide');
const transitionLoading = ref(true);
const transitionEnable = ref(true);

const themeColorPrimary = ref('hsl(212 100% 45%)');
const themeBuiltinType = ref<BuiltinThemeType>('default');
const themeMode = ref<ThemeModeType>('light');
const themeRadius = ref('0.5');
const themeSemiDarkSidebar = ref(false);
const themeSemiDarkHeader = ref(false);

const sidebarEnable = ref(true);
const sidebarWidth = ref(230);
const sidebarCollapsed = ref(false);
const sidebarCollapsedShowTitle = ref(false);
const sidebarAutoActivateChild = ref(false);
const sidebarExpandOnHover = ref(true);
const sidebarCollapsedButton = ref(true);
const sidebarFixedButton = ref(true);

const headerEnable = ref(true);
const headerMode = ref<LayoutHeaderModeType>('fixed');
const headerMenuAlign = ref<LayoutHeaderMenuAlignType>('start');

const breadcrumbEnable = ref(true);
const breadcrumbShowIcon = ref(true);
const breadcrumbShowHome = ref(true);
const breadcrumbStyleType = ref<BreadcrumbStyleType>('normal');
const breadcrumbHideOnlyOne = ref(false);

const tabbarEnable = ref(true);
const tabbarShowIcon = ref(true);
const tabbarShowMore = ref(true);
const tabbarShowMaximize = ref(true);
const tabbarPersist = ref(true);
const tabbarDraggable = ref(true);
const tabbarWheelable = ref(true);
const tabbarStyleType = ref('chrome');
const tabbarMaxCount = ref(0);
const tabbarMiddleClickToClose = ref(true);

const navigationStyleType = ref<NavigationStyleType>('rounded');
const navigationSplit = ref(true);
const navigationAccordion = ref(true);

const widgetGlobalSearch = ref(true);
const widgetFullscreen = ref(true);
const widgetLanguageToggle = ref(true);
const widgetNotification = ref(true);
const widgetThemeToggle = ref(true);
const widgetSidebarToggle = ref(true);
const widgetLockScreen = ref(true);
const widgetRefresh = ref(true);

function getDefaultConfig() {
  const overrides = overridesPreferences as Record<string, any>;
  return {
    app: {
      layout: overrides.app?.layout || preferences.app.layout || 'sidebar-nav',
      colorGrayMode:
        overrides.app?.colorGrayMode ?? preferences.app.colorGrayMode ?? false,
      colorWeakMode:
        overrides.app?.colorWeakMode ?? preferences.app.colorWeakMode ?? false,
      contentCompact:
        overrides.app?.contentCompact ||
        preferences.app.contentCompact ||
        'wide',
      preferencesButtonPosition:
        overrides.app?.preferencesButtonPosition ||
        preferences.app.preferencesButtonPosition ||
        'auto',
    },
    transition: {
      progress:
        overrides.transition?.progress ??
        preferences.transition.progress ??
        true,
      name:
        overrides.transition?.name ||
        preferences.transition.name ||
        'fade-slide',
      loading:
        overrides.transition?.loading ?? preferences.transition.loading ?? true,
      enable:
        overrides.transition?.enable ?? preferences.transition.enable ?? true,
    },
    theme: {
      colorPrimary:
        overrides.theme?.colorPrimary ||
        preferences.theme.colorPrimary ||
        'hsl(212 100% 45%)',
      builtinType:
        overrides.theme?.builtinType ||
        preferences.theme.builtinType ||
        'default',
      mode: overrides.theme?.mode || preferences.theme.mode || 'light',
      radius: String(
        overrides.theme?.radius || preferences.theme.radius || '0.5',
      ),
      semiDarkSidebar:
        overrides.theme?.semiDarkSidebar ??
        preferences.theme.semiDarkSidebar ??
        false,
      semiDarkHeader:
        overrides.theme?.semiDarkHeader ??
        preferences.theme.semiDarkHeader ??
        false,
    },
    sidebar: {
      enable: overrides.sidebar?.enable ?? preferences.sidebar.enable ?? true,
      width: overrides.sidebar?.width || preferences.sidebar.width || 230,
      collapsed:
        overrides.sidebar?.collapsed ?? preferences.sidebar.collapsed ?? false,
      collapsedShowTitle:
        overrides.sidebar?.collapsedShowTitle ??
        preferences.sidebar.collapsedShowTitle ??
        false,
      autoActivateChild:
        overrides.sidebar?.autoActivateChild ??
        preferences.sidebar.autoActivateChild ??
        false,
      expandOnHover:
        overrides.sidebar?.expandOnHover ??
        preferences.sidebar.expandOnHover ??
        true,
      collapsedButton:
        overrides.sidebar?.collapsedButton ??
        preferences.sidebar.collapsedButton ??
        true,
      fixedButton:
        overrides.sidebar?.fixedButton ??
        preferences.sidebar.fixedButton ??
        true,
    },
    header: {
      enable: overrides.header?.enable ?? preferences.header.enable ?? true,
      mode: overrides.header?.mode || preferences.header.mode || 'fixed',
      menuAlign:
        overrides.header?.menuAlign || preferences.header.menuAlign || 'start',
    },
    breadcrumb: {
      enable:
        overrides.breadcrumb?.enable ?? preferences.breadcrumb.enable ?? true,
      showIcon:
        overrides.breadcrumb?.showIcon ??
        preferences.breadcrumb.showIcon ??
        true,
      showHome:
        overrides.breadcrumb?.showHome ??
        preferences.breadcrumb.showHome ??
        true,
      styleType:
        overrides.breadcrumb?.styleType ||
        preferences.breadcrumb.styleType ||
        'normal',
      hideOnlyOne:
        overrides.breadcrumb?.hideOnlyOne ??
        preferences.breadcrumb.hideOnlyOne ??
        false,
    },
    tabbar: {
      enable: overrides.tabbar?.enable ?? preferences.tabbar.enable ?? true,
      showIcon:
        overrides.tabbar?.showIcon ?? preferences.tabbar.showIcon ?? true,
      showMore:
        overrides.tabbar?.showMore ?? preferences.tabbar.showMore ?? true,
      showMaximize:
        overrides.tabbar?.showMaximize ??
        preferences.tabbar.showMaximize ??
        true,
      persist: overrides.tabbar?.persist ?? preferences.tabbar.persist ?? true,
      draggable:
        overrides.tabbar?.draggable ?? preferences.tabbar.draggable ?? true,
      wheelable:
        overrides.tabbar?.wheelable ?? preferences.tabbar.wheelable ?? true,
      styleType:
        overrides.tabbar?.styleType || preferences.tabbar.styleType || 'chrome',
      maxCount: overrides.tabbar?.maxCount || preferences.tabbar.maxCount || 0,
      middleClickToClose:
        overrides.tabbar?.middleClickToClose ??
        preferences.tabbar.middleClickToClose ??
        true,
    },
    navigation: {
      styleType:
        overrides.navigation?.styleType ||
        preferences.navigation.styleType ||
        'rounded',
      split:
        overrides.navigation?.split ?? preferences.navigation.split ?? true,
      accordion:
        overrides.navigation?.accordion ??
        preferences.navigation.accordion ??
        true,
    },
    widget: {
      globalSearch:
        overrides.widget?.globalSearch ??
        preferences.widget.globalSearch ??
        true,
      fullscreen:
        overrides.widget?.fullscreen ?? preferences.widget.fullscreen ?? true,
      languageToggle:
        overrides.widget?.languageToggle ??
        preferences.widget.languageToggle ??
        true,
      notification:
        overrides.widget?.notification ??
        preferences.widget.notification ??
        true,
      themeToggle:
        overrides.widget?.themeToggle ?? preferences.widget.themeToggle ?? true,
      sidebarToggle:
        overrides.widget?.sidebarToggle ??
        preferences.widget.sidebarToggle ??
        true,
      lockScreen:
        overrides.widget?.lockScreen ?? preferences.widget.lockScreen ?? true,
      refresh: overrides.widget?.refresh ?? preferences.widget.refresh ?? true,
    },
  };
}

async function loadConfig() {
  loading.value = true;
  try {
    const applicationId = getCurrentApplicationId();
    const data = await getPreferencesConfigApi(applicationId);
    const defaults = getDefaultConfig();

    appLayout.value = (data?.app?.layout || defaults.app.layout) as LayoutType;
    appColorGrayMode.value =
      data?.app?.colorGrayMode ?? defaults.app.colorGrayMode;
    appColorWeakMode.value =
      data?.app?.colorWeakMode ?? defaults.app.colorWeakMode;
    appContentCompact.value = (data?.app?.contentCompact ||
      defaults.app.contentCompact) as ContentCompactType;
    appPreferencesButtonPosition.value = (data?.app
      ?.preferencesButtonPosition ||
      defaults.app.preferencesButtonPosition) as PreferencesButtonPositionType;

    transitionProgress.value =
      data?.transition?.progress ?? defaults.transition.progress;
    transitionName.value = data?.transition?.name || defaults.transition.name;
    transitionLoading.value =
      data?.transition?.loading ?? defaults.transition.loading;
    transitionEnable.value =
      data?.transition?.enable ?? defaults.transition.enable;

    themeColorPrimary.value =
      data?.theme?.colorPrimary || defaults.theme.colorPrimary;
    themeBuiltinType.value = (data?.theme?.builtinType ||
      defaults.theme.builtinType) as BuiltinThemeType;
    themeMode.value = (data?.theme?.mode ||
      defaults.theme.mode) as ThemeModeType;
    themeRadius.value = String(data?.theme?.radius || defaults.theme.radius);
    themeSemiDarkSidebar.value =
      data?.theme?.semiDarkSidebar ?? defaults.theme.semiDarkSidebar;
    themeSemiDarkHeader.value =
      data?.theme?.semiDarkHeader ?? defaults.theme.semiDarkHeader;

    sidebarEnable.value = data?.sidebar?.enable ?? defaults.sidebar.enable;
    sidebarWidth.value = data?.sidebar?.width || defaults.sidebar.width;
    sidebarCollapsed.value =
      data?.sidebar?.collapsed ?? defaults.sidebar.collapsed;
    sidebarCollapsedShowTitle.value =
      data?.sidebar?.collapsedShowTitle ?? defaults.sidebar.collapsedShowTitle;
    sidebarAutoActivateChild.value =
      data?.sidebar?.autoActivateChild ?? defaults.sidebar.autoActivateChild;
    sidebarExpandOnHover.value =
      data?.sidebar?.expandOnHover ?? defaults.sidebar.expandOnHover;
    sidebarCollapsedButton.value =
      data?.sidebar?.collapsedButton ?? defaults.sidebar.collapsedButton;
    sidebarFixedButton.value =
      data?.sidebar?.fixedButton ?? defaults.sidebar.fixedButton;

    headerEnable.value = data?.header?.enable ?? defaults.header.enable;
    headerMode.value = (data?.header?.mode ||
      defaults.header.mode) as LayoutHeaderModeType;
    headerMenuAlign.value = (data?.header?.menuAlign ||
      defaults.header.menuAlign) as LayoutHeaderMenuAlignType;

    breadcrumbEnable.value =
      data?.breadcrumb?.enable ?? defaults.breadcrumb.enable;
    breadcrumbShowIcon.value =
      data?.breadcrumb?.showIcon ?? defaults.breadcrumb.showIcon;
    breadcrumbShowHome.value =
      data?.breadcrumb?.showHome ?? defaults.breadcrumb.showHome;
    breadcrumbStyleType.value = (data?.breadcrumb?.styleType ||
      defaults.breadcrumb.styleType) as BreadcrumbStyleType;
    breadcrumbHideOnlyOne.value =
      data?.breadcrumb?.hideOnlyOne ?? defaults.breadcrumb.hideOnlyOne;

    tabbarEnable.value = data?.tabbar?.enable ?? defaults.tabbar.enable;
    tabbarShowIcon.value = data?.tabbar?.showIcon ?? defaults.tabbar.showIcon;
    tabbarShowMore.value = data?.tabbar?.showMore ?? defaults.tabbar.showMore;
    tabbarShowMaximize.value =
      data?.tabbar?.showMaximize ?? defaults.tabbar.showMaximize;
    tabbarPersist.value = data?.tabbar?.persist ?? defaults.tabbar.persist;
    tabbarDraggable.value =
      data?.tabbar?.draggable ?? defaults.tabbar.draggable;
    tabbarWheelable.value =
      data?.tabbar?.wheelable ?? defaults.tabbar.wheelable;
    tabbarStyleType.value =
      data?.tabbar?.styleType || defaults.tabbar.styleType;
    tabbarMaxCount.value = data?.tabbar?.maxCount || defaults.tabbar.maxCount;
    tabbarMiddleClickToClose.value =
      data?.tabbar?.middleClickToClose ?? defaults.tabbar.middleClickToClose;

    navigationStyleType.value = (data?.navigation?.styleType ||
      defaults.navigation.styleType) as NavigationStyleType;
    navigationSplit.value =
      data?.navigation?.split ?? defaults.navigation.split;
    navigationAccordion.value =
      data?.navigation?.accordion ?? defaults.navigation.accordion;

    widgetGlobalSearch.value =
      data?.widget?.globalSearch ?? defaults.widget.globalSearch;
    widgetFullscreen.value =
      data?.widget?.fullscreen ?? defaults.widget.fullscreen;
    widgetLanguageToggle.value =
      data?.widget?.languageToggle ?? defaults.widget.languageToggle;
    widgetNotification.value =
      data?.widget?.notification ?? defaults.widget.notification;
    widgetThemeToggle.value =
      data?.widget?.themeToggle ?? defaults.widget.themeToggle;
    widgetSidebarToggle.value =
      data?.widget?.sidebarToggle ?? defaults.widget.sidebarToggle;
    widgetLockScreen.value =
      data?.widget?.lockScreen ?? defaults.widget.lockScreen;
    widgetRefresh.value = data?.widget?.refresh ?? defaults.widget.refresh;
  } catch {
    const defaults = getDefaultConfig();
    appLayout.value = defaults.app.layout as LayoutType;
  } finally {
    loading.value = false;
  }
}

function buildConfig(): PreferencesConfig {
  return {
    app: {
      layout: appLayout.value,
      colorGrayMode: appColorGrayMode.value,
      colorWeakMode: appColorWeakMode.value,
      contentCompact: appContentCompact.value,
      preferencesButtonPosition: appPreferencesButtonPosition.value,
    },
    transition: {
      progress: transitionProgress.value,
      name: transitionName.value,
      loading: transitionLoading.value,
      enable: transitionEnable.value,
    },
    theme: {
      colorPrimary: themeColorPrimary.value,
      builtinType: themeBuiltinType.value,
      mode: themeMode.value,
      radius: themeRadius.value,
      semiDarkSidebar: themeSemiDarkSidebar.value,
      semiDarkHeader: themeSemiDarkHeader.value,
    },
    sidebar: {
      enable: sidebarEnable.value,
      width: sidebarWidth.value,
      collapsed: sidebarCollapsed.value,
      collapsedShowTitle: sidebarCollapsedShowTitle.value,
      autoActivateChild: sidebarAutoActivateChild.value,
      expandOnHover: sidebarExpandOnHover.value,
      collapsedButton: sidebarCollapsedButton.value,
      fixedButton: sidebarFixedButton.value,
    },
    header: {
      enable: headerEnable.value,
      mode: headerMode.value,
      menuAlign: headerMenuAlign.value,
    },
    breadcrumb: {
      enable: breadcrumbEnable.value,
      showIcon: breadcrumbShowIcon.value,
      showHome: breadcrumbShowHome.value,
      styleType: breadcrumbStyleType.value,
      hideOnlyOne: breadcrumbHideOnlyOne.value,
    },
    tabbar: {
      enable: tabbarEnable.value,
      showIcon: tabbarShowIcon.value,
      showMore: tabbarShowMore.value,
      showMaximize: tabbarShowMaximize.value,
      persist: tabbarPersist.value,
      draggable: tabbarDraggable.value,
      wheelable: tabbarWheelable.value,
      styleType: tabbarStyleType.value,
      maxCount: tabbarMaxCount.value,
      middleClickToClose: tabbarMiddleClickToClose.value,
    },
    navigation: {
      styleType: navigationStyleType.value,
      split: navigationSplit.value,
      accordion: navigationAccordion.value,
    },
    widget: {
      globalSearch: widgetGlobalSearch.value,
      fullscreen: widgetFullscreen.value,
      languageToggle: widgetLanguageToggle.value,
      notification: widgetNotification.value,
      themeToggle: widgetThemeToggle.value,
      sidebarToggle: widgetSidebarToggle.value,
      lockScreen: widgetLockScreen.value,
      refresh: widgetRefresh.value,
    },
  };
}

function applyPreferences() {
  const config = buildConfig();
  updatePreferences({
    app: config.app,
    transition: config.transition,
    theme: config.theme,
    sidebar: config.sidebar,
    header: config.header,
    breadcrumb: config.breadcrumb,
    tabbar: config.tabbar,
    navigation: config.navigation,
    widget: config.widget,
  });
}

async function save() {
  if (loading.value) return;
  try {
    applyPreferences();

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

onMounted(() => {
  loadConfig();
});
</script>

<template>
  <div v-loading="loading" class="grid grid-cols-3 gap-6 p-4">
    <!-- 外观 -->
    <div class="preferences-column">
      <Block :title="$t('preferences.theme.title')">
        <Theme
          v-model="themeMode"
          v-model:theme-semi-dark-sidebar="themeSemiDarkSidebar"
          v-model:theme-semi-dark-header="themeSemiDarkHeader"
        />
      </Block>

      <Block :title="$t('preferences.theme.builtin.title')">
        <BuiltinTheme
          v-model="themeBuiltinType"
          v-model:theme-color-primary="themeColorPrimary"
          :is-dark="isDark"
        />
      </Block>

      <Block :title="$t('preferences.animation.title')">
        <Animation
          v-model:transition-enable="transitionEnable"
          v-model:transition-loading="transitionLoading"
          v-model:transition-name="transitionName"
          v-model:transition-progress="transitionProgress"
        />
      </Block>

      <Block :title="$t('preferences.theme.radius')">
        <Radius v-model="themeRadius" />
      </Block>

      <Block :title="$t('preferences.other')">
        <ColorMode
          v-model:app-color-gray-mode="appColorGrayMode"
          v-model:app-color-weak-mode="appColorWeakMode"
        />
      </Block>
    </div>

    <!-- 布局 -->
    <div class="preferences-column">
      <Block :title="$t('preferences.layout')">
        <Layout v-model="appLayout" />
      </Block>

      <Block :title="$t('preferences.content')">
        <Content v-model="appContentCompact" />
      </Block>

      <Block :title="$t('preferences.sidebar.title')">
        <Sidebar
          v-model:sidebar-enable="sidebarEnable"
          v-model:sidebar-width="sidebarWidth"
          v-model:sidebar-collapsed="sidebarCollapsed"
          v-model:sidebar-collapsed-show-title="sidebarCollapsedShowTitle"
          v-model:sidebar-auto-activate-child="sidebarAutoActivateChild"
          v-model:sidebar-expand-on-hover="sidebarExpandOnHover"
          v-model:sidebar-collapsed-button="sidebarCollapsedButton"
          v-model:sidebar-fixed-button="sidebarFixedButton"
          :current-layout="appLayout"
          :disabled="!isSideMode"
        />
      </Block>

      <Block :title="$t('preferences.header.title')">
        <Header
          v-model:header-enable="headerEnable"
          v-model:header-mode="headerMode"
          v-model:header-menu-align="headerMenuAlign"
          :disabled="isFullContent"
        />
      </Block>

      <Block :title="$t('preferences.navigationMenu.title')">
        <Navigation
          v-model:navigation-style-type="navigationStyleType"
          v-model:navigation-split="navigationSplit"
          v-model:navigation-accordion="navigationAccordion"
          :disabled="isFullContent"
          :disabled-navigation-split="!isMixedNav"
        />
      </Block>
    </div>

    <!-- 布局（续） -->
    <div class="preferences-column">
      <Block :title="$t('preferences.breadcrumb.title')">
        <Breadcrumb
          v-model:breadcrumb-enable="breadcrumbEnable"
          v-model:breadcrumb-show-icon="breadcrumbShowIcon"
          v-model:breadcrumb-show-home="breadcrumbShowHome"
          v-model:breadcrumb-style-type="breadcrumbStyleType"
          v-model:breadcrumb-hide-only-one="breadcrumbHideOnlyOne"
          :disabled="
            isFullContent || isMixedNav || isHeaderNav || !headerEnable
          "
        />
      </Block>

      <Block :title="$t('preferences.tabbar.title')">
        <Tabbar
          v-model:tabbar-enable="tabbarEnable"
          v-model:tabbar-show-icon="tabbarShowIcon"
          v-model:tabbar-show-more="tabbarShowMore"
          v-model:tabbar-show-maximize="tabbarShowMaximize"
          v-model:tabbar-persist="tabbarPersist"
          v-model:tabbar-draggable="tabbarDraggable"
          v-model:tabbar-wheelable="tabbarWheelable"
          v-model:tabbar-style-type="tabbarStyleType"
          v-model:tabbar-max-count="tabbarMaxCount"
          v-model:tabbar-middle-click-to-close="tabbarMiddleClickToClose"
        />
      </Block>

      <Block :title="$t('preferences.widget.title')">
        <Widget
          v-model:app-preferences-button-position="appPreferencesButtonPosition"
          v-model:widget-fullscreen="widgetFullscreen"
          v-model:widget-global-search="widgetGlobalSearch"
          v-model:widget-language-toggle="widgetLanguageToggle"
          v-model:widget-lock-screen="widgetLockScreen"
          v-model:widget-notification="widgetNotification"
          v-model:widget-refresh="widgetRefresh"
          v-model:widget-sidebar-toggle="widgetSidebarToggle"
          v-model:widget-theme-toggle="widgetThemeToggle"
        />
      </Block>
    </div>
  </div>
</template>

<style scoped>
.preferences-column {
  min-width: 0;
}
</style>
