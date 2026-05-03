import { $t } from '@vben/locales';

export function getMenuTypeOptions() {
  return [
    {
      type: 'info',
      label: $t('menu.typeCatalog'),
      value: 'catalog',
    },
    { type: 'info', label: $t('menu.typeMenu'), value: 'menu' },
    // { type: 'danger', label: $t('menu.typeButton'), value: 'button' },
    {
      type: 'success',
      label: $t('menu.typeEmbedded'),
      value: 'embedded',
    },
    { type: 'warning', label: $t('menu.typeLink'), value: 'link' },
    { type: 'primary', label: $t('menu.typeOnlineForm'), value: 'online_form' },
    { type: 'primary', label: $t('menu.typeOnlinePage'), value: 'online_page' },
    { type: 'success', label: $t('menu.typeAgent'), value: 'agent' },
  ];
}
