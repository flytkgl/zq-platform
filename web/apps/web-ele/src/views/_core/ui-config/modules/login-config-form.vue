<script lang="ts" setup>
import type { PreferencesConfig } from '#/api/core/ui-config';

import { onMounted, ref } from 'vue';

import { Block, SwitchItem } from '@vben/layouts/preferences-blocks';
import { $t } from '@vben/locales';

import { ElMessage } from 'element-plus';

import {
  getPreferencesConfigApi,
  updatePreferencesConfigApi,
} from '#/api/core/ui-config';
import { useAppContextStore } from '#/store/app-context';

defineOptions({ name: 'LoginConfigForm' });

const appContextStore = useAppContextStore();

function getCurrentApplicationId(): string | undefined {
  return appContextStore.currentApp?.id;
}

const loading = ref(false);

const loginEnableThirdParty = ref(false);
const loginEnabledProviders = ref<string[]>([]);

interface ProviderInfo {
  key: string;
  color: string;
  iconViewBox: string;
  iconPaths: string[];
  pathColors?: string[];
  isRect?: boolean;
}

const microsoftRects = [
  { x: 0, y: 0, width: 10.66, height: 10.66 },
  { x: 12.34, y: 0, width: 10.66, height: 10.66 },
  { x: 0, y: 12.34, width: 10.66, height: 10.66 },
  { x: 12.34, y: 12.34, width: 10.66, height: 10.66 },
];

const allProviders: ProviderInfo[] = [
  {
    key: 'gitee',
    color: '#C71D23',
    iconViewBox: '0 0 1024 1024',
    iconPaths: [
      'M512 1024C229.222 1024 0 794.778 0 512S229.222 0 512 0s512 229.222 512 512-229.222 512-512 512z m259.149-568.883h-290.74a25.293 25.293 0 0 0-25.292 25.293l-0.026 63.206c0 13.952 11.315 25.293 25.267 25.293h177.024c13.978 0 25.293 11.315 25.293 25.267v12.646a75.853 75.853 0 0 1-75.853 75.853h-240.23a25.293 25.293 0 0 1-25.267-25.293V417.203a75.853 75.853 0 0 1 75.827-75.853h353.946a25.293 25.293 0 0 0 25.267-25.292l0.077-63.207a25.293 25.293 0 0 0-25.268-25.293H417.152a189.62 189.62 0 0 0-189.62 189.645V771.15c0 13.977 11.316 25.293 25.294 25.293h372.94a170.65 170.65 0 0 0 170.65-170.65V480.384a25.293 25.293 0 0 0-25.293-25.267z',
    ],
  },
  {
    key: 'github',
    color: '#24292e',
    iconViewBox: '0 0 1024 1024',
    iconPaths: [
      'M512 42.666667A464.64 464.64 0 0 0 42.666667 502.186667 460.373333 460.373333 0 0 0 363.52 938.666667c23.466667 4.266667 32-9.813333 32-22.186667v-78.08c-130.56 27.733333-158.293333-61.44-158.293333-61.44a122.026667 122.026667 0 0 0-52.053334-67.413333c-42.666667-28.16 3.413333-27.733333 3.413334-27.733334a98.56 98.56 0 0 1 71.68 47.36 101.12 101.12 0 0 0 136.533333 37.973334 99.413333 99.413333 0 0 1 29.866667-61.44c-104.106667-11.52-213.333333-50.773333-213.333334-226.986667a177.066667 177.066667 0 0 1 47.36-124.16 161.28 161.28 0 0 1 4.693334-121.173333s39.68-12.373333 128 46.933333a455.68 455.68 0 0 1 234.666666 0c89.6-59.306667 128-46.933333 128-46.933333a161.28 161.28 0 0 1 4.693334 121.173333A177.066667 177.066667 0 0 1 810.666667 477.866667c0 176.64-110.08 215.466667-213.333334 226.986666a106.666667 106.666667 0 0 1 32 85.333334v125.866666c0 14.933333 8.533333 26.88 32 22.186667A460.8 460.8 0 0 0 981.333333 502.186667 464.64 464.64 0 0 0 512 42.666667',
    ],
  },
  {
    key: 'google',
    color: '#4285F4',
    iconViewBox: '0 0 24 24',
    iconPaths: [
      'M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z',
      'M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z',
      'M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z',
      'M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z',
    ],
    pathColors: ['#4285F4', '#34A853', '#FBBC05', '#EA4335'],
  },
  {
    key: 'microsoft',
    color: '#00A4EF',
    iconViewBox: '0 0 23 23',
    iconPaths: [
      'M0 0h10.66v10.66H0z',
      'M12.34 0h10.66v10.66H12.34z',
      'M0 12.34h10.66v10.66H0z',
      'M12.34 12.34h10.66v10.66H12.34z',
    ],
    pathColors: ['#F25022', '#7FBA00', '#00A4EF', '#FFB900'],
    isRect: true,
  },
  {
    key: 'qq',
    color: '#12B7F5',
    iconViewBox: '0 0 1024 1024',
    iconPaths: [
      'M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 689.3 112 511.5 112 331.7 112 256.2 265.2 261 447.9c-28.4 70.8-46.7 113.7-62.7 165.3-34 109.5-23 154.8-14.6 155.8 18 2.2 70.1-82.4 70.1-82.4 0 49 25.2 112.9 79.8 159-26.4 8.1-85.7 29.9-71.6 53.8 11.4 19.3 196.2 12.3 249.5 6.3 53.3 6 238.1 13 249.5-6.3 14.1-23.8-45.3-45.7-71.6-53.8 54.6-46.2 79.8-110.1 79.8-159 0 0 52.1 84.6 70.1 82.4 8.5-1.1 19.5-46.4-14.5-155.8z',
    ],
  },
  {
    key: 'wechat',
    color: '#07C160',
    iconViewBox: '0 0 1024 1024',
    iconPaths: [
      'M664.250054 368.541681c10.015098 0 19.892049 0.732687 29.67281 1.795902-26.647917-122.810047-159.358451-214.077703-310.826188-214.077703-169.353083 0-308.085774 114.232694-308.085774 259.274068 0 83.708494 46.165436 152.460344 123.281791 205.78483l-30.80868 91.730191 107.688651-53.455469c38.558178 7.53665 69.459978 15.308661 107.924012 15.308661 9.66308 0 19.230993-0.470721 28.752858-1.225921-6.025227-20.36584-9.521864-41.723264-9.521864-63.862493C402.328693 476.632491 517.908058 368.541681 664.250054 368.541681zM498.62897 285.87389c23.200398 0 38.557154 15.120372 38.557154 38.061874 0 22.846334-15.356756 38.156018-38.557154 38.156018-23.107277 0-46.260603-15.309684-46.260603-38.156018C452.368366 300.994262 475.522716 285.87389 498.62897 285.87389zM283.016307 362.090758c-23.107277 0-46.402843-15.309684-46.402843-38.156018 0-22.941502 23.295566-38.061874 46.402843-38.061874 23.081695 0 38.46301 15.120372 38.46301 38.061874C321.479317 346.782098 306.098002 362.090758 283.016307 362.090758zM945.448458 606.151333c0-121.888048-123.258255-221.236753-261.683954-221.236753-146.57838 0-262.015505 99.348706-262.015505 221.236753 0 122.06508 115.437126 221.200938 262.015505 221.200938 30.66644 0 61.617359-7.609305 92.423993-15.262612l84.513836 45.786813-23.178909-76.17082C899.379213 735.776599 945.448458 674.90216 945.448458 606.151333zM598.803483 567.994292c-15.332197 0-30.807656-15.096836-30.807656-30.501688 0-15.190981 15.47546-30.477129 30.807656-30.477129 23.295566 0 38.558178 15.286148 38.558178 30.477129C637.361661 552.897456 622.099049 567.994292 598.803483 567.994292zM768.25071 567.994292c-15.213493 0-30.594809-15.096836-30.594809-30.501688 0-15.190981 15.381315-30.477129 30.594809-30.477129 23.107277 0 38.558178 15.286148 38.558178 30.477129C806.808888 552.897456 791.357987 567.994292 768.25071 567.994292z',
    ],
  },
  {
    key: 'wecom',
    color: '#07C160',
    iconViewBox: '0 0 1024 1024',
    iconPaths: [
      'M679.872 348.064c10.688 0 21.184 0.768 31.552 1.92C684.48 221.312 545.408 124.48 383.488 124.48c-180.16 0-327.68 121.536-327.68 275.84 0 89.088 49.088 162.176 131.2 218.88l-32.768 97.6 114.56-56.896c41.024 8.064 73.92 16.32 114.816 16.32 10.304 0 20.48-0.512 30.592-1.28-6.4-21.696-10.112-44.416-10.112-67.968 0-139.264 122.88-258.912 275.776-258.912zM505.152 270.528c16.384 0 27.264 10.688 27.264 26.88 0 16.128-10.88 26.944-27.264 26.944-16.32 0-32.704-10.816-32.704-26.944 0-16.192 16.384-26.88 32.704-26.88zM276.416 324.352c-16.384 0-32.832-10.816-32.832-26.944 0-16.192 16.448-26.88 32.832-26.88 16.32 0 27.2 10.688 27.2 26.88 0 16.128-10.88 26.944-27.2 26.944z',
      'M968.064 604.864c0-137.344-131.072-249.024-278.208-249.024-155.904 0-278.528 111.68-278.528 249.024 0 137.472 122.624 249.024 278.528 249.024 32.64 0 65.536-8.128 98.304-16.256l89.856 48.768-24.64-81.024c65.536-65.472 114.688-137.344 114.688-200.512zM614.208 578.176c-10.816 0-21.824-10.688-21.824-21.568 0-10.752 11.008-21.568 21.824-21.568 16.512 0 27.328 10.816 27.328 21.568 0 10.88-10.816 21.568-27.328 21.568z m196.416 0c-10.752 0-21.696-10.688-21.696-21.568 0-10.752 10.944-21.568 21.696-21.568 16.384 0 27.328 10.816 27.328 21.568 0 10.88-10.944 21.568-27.328 21.568z',
    ],
  },
  {
    key: 'dingtalk',
    color: '#0089FF',
    iconViewBox: '0 0 1024 1024',
    iconPaths: [
      'M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64z m244.5 558.4l-106.1-17s87.5-98.1 34.1-184.8c-53.4-86.7-151.5-51.4-151.5-51.4s-100.1 34.1-132.2 134.2c-32.1 100.1 34.1 184.8 34.1 184.8l-106.1 17s-17-68.2 17-151.5c34.1-83.3 100.1-132.2 100.1-132.2s-17-34.1-51.4-34.1c-34.1 0-68.2 17-68.2 17s-17-51.4 17-100.1c34.1-48.7 100.1-68.2 100.1-68.2s184.8-34.1 285 100.1c100.1 134.2 28.1 285.2 28.1 285.2z',
    ],
  },
  {
    key: 'feishu',
    color: '#00D6B9',
    iconViewBox: '0 0 1024 1024',
    iconPaths: [
      'M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64z m213.3 512H298.7c-17.7 0-32-14.3-32-32V298.7c0-17.7 14.3-32 32-32h426.6c17.7 0 32 14.3 32 32V544c0 17.7-14.3 32-32 32z',
      'M426.7 469.3h170.6c17.7 0 32 14.3 32 32v42.7c0 17.7-14.3 32-32 32H426.7c-17.7 0-32-14.3-32-32v-42.7c0-17.7 14.3-32 32-32z',
    ],
  },
];

function isProviderSelected(key: string): boolean {
  return loginEnabledProviders.value.includes(key);
}

function toggleProvider(key: string) {
  const index = loginEnabledProviders.value.indexOf(key);
  if (index >= 0) {
    loginEnabledProviders.value.splice(index, 1);
  } else {
    loginEnabledProviders.value.push(key);
  }
}

async function loadConfig() {
  loading.value = true;
  try {
    const applicationId = getCurrentApplicationId();
    const data = await getPreferencesConfigApi(applicationId);

    loginEnableThirdParty.value =
      data?.loginConfig?.enableThirdPartyLogin ?? false;
    loginEnabledProviders.value =
      data?.loginConfig?.enabledProviders ?? [];
  } catch {
    loginEnableThirdParty.value = false;
    loginEnabledProviders.value = [];
  } finally {
    loading.value = false;
  }
}

function buildConfig(): PreferencesConfig {
  return {
    loginConfig: {
      enableThirdPartyLogin: loginEnableThirdParty.value,
      enabledProviders: loginEnabledProviders.value,
    },
  };
}

async function save() {
  if (loading.value) return;
  try {
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
  <div v-loading="loading" class="p-6">
    <Block :title="$t('ui-config.loginConfig.title')">
      <SwitchItem v-model="loginEnableThirdParty">
        {{ $t('ui-config.loginConfig.enableThirdPartyLogin') }}
      </SwitchItem>

      <template v-if="loginEnableThirdParty">
        <div class="mt-4">
          <div class="text-muted-foreground mb-1 text-sm">
            {{ $t('ui-config.loginConfig.enabledProviders') }}
          </div>
          <div class="text-muted-foreground mb-4 text-xs">
            {{ $t('ui-config.loginConfig.enabledProvidersTip') }}
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div
              v-for="provider in allProviders"
              :key="provider.key"
              class="provider-card"
              :class="{ 'provider-card--selected': isProviderSelected(provider.key) }"
              @click="toggleProvider(provider.key)"
            >
              <div class="provider-card__icon" :style="{ backgroundColor: provider.color + '14' }">
                <svg
                  class="size-5"
                  :viewBox="provider.iconViewBox"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <template v-if="provider.isRect">
                    <rect
                      v-for="(rect, idx) in microsoftRects"
                      :key="idx"
                      :x="rect.x"
                      :y="rect.y"
                      :width="rect.width"
                      :height="rect.height"
                      :fill="provider.pathColors?.[idx] || provider.color"
                    />
                  </template>
                  <template v-else>
                    <path
                      v-for="(pathD, idx) in provider.iconPaths"
                      :key="idx"
                      :d="pathD"
                      :fill="provider.pathColors?.[idx] || provider.color"
                    />
                  </template>
                </svg>
              </div>
              <span class="provider-card__name">
                {{ $t(`ui-config.loginConfig.providers.${provider.key}`) }}
              </span>
              <div class="provider-card__check">
                <svg
                  v-if="isProviderSelected(provider.key)"
                  class="size-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M20 6L9 17L4 12"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Block>
  </div>
</template>

<style scoped>
.provider-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 2px solid hsl(var(--border));
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  position: relative;
}

.provider-card:hover {
  border-color: hsl(var(--primary) / 0.5);
  background-color: hsl(var(--accent) / 0.3);
}

.provider-card--selected {
  border-color: hsl(var(--primary));
  background-color: hsl(var(--primary) / 0.06);
}

.provider-card--selected:hover {
  border-color: hsl(var(--primary));
}

.provider-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  flex-shrink: 0;
}

.provider-card__name {
  font-size: 14px;
  font-weight: 500;
  color: hsl(var(--foreground));
  flex: 1;
}

.provider-card__check {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: hsl(var(--primary));
}
</style>
