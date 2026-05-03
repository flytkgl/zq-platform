<script lang="ts" setup>
import type { OAuthApi } from '#/api/core';

import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useAccessStore, useUserStore } from '@vben/stores';

import { ElMessage } from 'element-plus';

import { getAccessCodesApi, oauthCallbackApi } from '#/api/core';

defineOptions({ name: 'OAuthCallback' });

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const accessStore = useAccessStore();

const loading = ref(true);
const errorMessage = ref('');

onMounted(async () => {
  try {
    // 从路由参数获取 provider
    const provider = route.params.provider as OAuthApi.OAuthProvider;

    if (
      !provider ||
      ![
        'dingtalk',
        'feishu',
        'gitee',
        'github',
        'google',
        'microsoft',
        'qq',
        'wechat',
        'wecom',
      ].includes(provider)
    ) {
      errorMessage.value = '不支持的 OAuth 提供商';
      loading.value = false;
      return;
    }

    // 从 URL 获取参数
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state') || undefined;

    if (!code) {
      errorMessage.value = '授权失败：未获取到授权码';
      loading.value = false;
      return;
    }

    // 调用后端接口处理 OAuth 登录
    const data = await oauthCallbackApi(provider, { code, state });

    if (data) {
      const { access_token, refresh_token, user_info } = data;

      // 保存 token
      accessStore.setAccessToken(access_token);
      accessStore.setRefreshToken(refresh_token);

      // 保存用户信息
      userStore.setUserInfo({
        userId: user_info.id,
        username: user_info.username,
        realName: user_info.name || user_info.username,
        avatar: user_info.avatar || '',
        roles: user_info.is_superuser ? ['super'] : ['user'],
      });

      // 获取权限码
      try {
        const accessCodes = await getAccessCodesApi();
        accessStore.setAccessCodes(accessCodes);
      } catch (error) {
        console.warn('获取权限码失败:', error);
      }

      ElMessage.success('登录成功');

      // 解析 state 中的 redirect 参数
      // state 格式: {"csrf":"...","payload":"..."}，payload 是前端传入的原始 state
      let redirectPath = '/';
      if (state) {
        try {
          const stateData = JSON.parse(state);
          // 从 payload 中提取前端传入的原始 state（如 redirect 信息）
          const payload = stateData.payload;
          if (payload) {
            try {
              const payloadData = JSON.parse(payload);
              if (payloadData.redirect) {
                redirectPath = decodeURIComponent(payloadData.redirect);
              }
            } catch {
              // payload 不是 JSON，忽略
            }
          }
        } catch {
          // state 解析失败，使用默认路径
        }
      }

      // 跳转到目标页面
      setTimeout(() => {
        router.replace(redirectPath);
      }, 500);
    } else {
      errorMessage.value = '登录失败';
      loading.value = false;
    }
  } catch (error: any) {
    console.error('OAuth 登录失败:', error);
    errorMessage.value = error.message || '登录失败，请重试';
    loading.value = false;
  }
});

const backToLogin = () => {
  router.replace('/auth/login');
};
</script>

<template>
  <div class="flex min-h-screen items-center justify-center">
    <div class="bg-background min-w-80 rounded-xl p-12 text-center">
      <div
        v-if="loading"
        class="flex flex-col items-center justify-center py-4"
      >
        <!-- 动画容器 -->
        <div class="relative flex size-20 items-center justify-center">
          <!-- 外层扩散波纹 -->
          <div
            class="bg-primary/20 absolute h-full w-full animate-ping rounded-full opacity-75"
          ></div>
          <!-- 中层静态光晕 -->
          <div class="bg-primary/10 absolute size-14 rounded-full"></div>
          <!-- 内层旋转圆环 -->
          <div
            class="border-primary size-10 animate-spin rounded-full border-4 border-t-transparent"
          ></div>
        </div>

        <p class="text-muted-foreground mt-6 animate-pulse text-sm font-medium">
          正在处理登录...
        </p>
      </div>

      <div v-else class="flex flex-col items-center gap-5">
        <div class="text-5xl">⚠️</div>
        <p class="text-destructive m-0 text-base">{{ errorMessage }}</p>
        <button
          class="hover:bg-primary/90 bg-primary text-primary-foreground cursor-pointer rounded-md border-none px-6 py-2.5 text-sm transition-colors"
          @click="backToLogin"
        >
          返回登录
        </button>
      </div>
    </div>
  </div>
</template>
