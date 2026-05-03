import { defineOverridesPreferences } from '@vben/preferences';

import Logo from '#/assets/logo.png';

/**
 * @description 项目配置文件
 * 只需要覆盖项目中的一部分配置，不需要的配置不用覆盖，会自动使用默认配置
 * !!! 更改配置后请清空缓存，否则可能不生效
 */
export const overridesPreferences = defineOverridesPreferences({
  // overrides
  app: {
    name: import.meta.env.VITE_APP_TITLE,
    enableRefreshToken: true,
    accessMode: 'mixed',
    authPageLayout: 'panel-center',
    layout: 'header-sidebar-nav',
  },
  theme: {
    mode: 'light',
  },
  copyright: {
    companyName: 'ZQ-Platform',
    companySiteLink: 'https://zq-platform.com',
    date: '2025',
    enable: true,
    icp: '',
    icpLink: '',
    loginOnly: true,
    policeIcp: '',
    policeIcpLink: '',
    settingShow: true,
  },
  logo: {
    enable: true,
    fit: 'contain',
    source: Logo,
  },
});
