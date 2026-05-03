<script setup lang="ts">
import type { DashboardWidget } from '../../store/dashboardDesignStore';

import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudRain,
  CloudSnow,
  CloudSun,
  Sun,
  Zap,
} from '@vben/icons';
import { $t } from '@vben/locales';

const props = defineProps<{
  widget: DashboardWidget;
}>();

// 实时天气数据
const weatherData = ref<null | {
  humidity: number;
  temperature: number;
  weatherCode: number;
  windDirection: number;
  windSpeed: number;
}>(null);
const error = ref(false);
const locatedCityName = ref('');
let timer: null | ReturnType<typeof setInterval> = null;

// 显示的城市名：优先手动配置，其次自动定位
const displayCityName = computed(() => {
  return props.widget.props.cityName || locatedCityName.value || '-';
});

// 反向地理编码获取城市名
async function reverseGeocode(lat: number, lon: number) {
  try {
    const res = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=zh`,
    );
    if (!res.ok) return;
    const data = await res.json();
    locatedCityName.value =
      data?.city || data?.locality || data?.principalSubdivision || '';
  } catch {
    // 反向编码失败不影响天气显示
  }
}

// WMO Weather Code 映射
function getWeatherInfo(code: number): {
  color: string;
  icon: any;
  label: string;
} {
  // 晴天
  if (code === 0)
    return {
      icon: Sun,
      color: '#f59e0b',
      label: $t('dashboard-design.widgets.weather.codes.clear'),
    };
  // 少云/多云
  if (code === 1)
    return {
      icon: CloudSun,
      color: '#60a5fa',
      label: $t('dashboard-design.widgets.weather.codes.mainlyClear'),
    };
  if (code === 2)
    return {
      icon: CloudSun,
      color: '#60a5fa',
      label: $t('dashboard-design.widgets.weather.codes.partlyCloudy'),
    };
  if (code === 3)
    return {
      icon: Cloud,
      color: '#9ca3af',
      label: $t('dashboard-design.widgets.weather.codes.overcast'),
    };
  // 雾
  if (code === 45 || code === 48)
    return {
      icon: CloudFog,
      color: '#9ca3af',
      label: $t('dashboard-design.widgets.weather.codes.fog'),
    };
  // 毛毛雨
  if (code >= 51 && code <= 57)
    return {
      icon: CloudDrizzle,
      color: '#60a5fa',
      label: $t('dashboard-design.widgets.weather.codes.drizzle'),
    };
  // 雨
  if (code >= 61 && code <= 67)
    return {
      icon: CloudRain,
      color: '#3b82f6',
      label: $t('dashboard-design.widgets.weather.codes.rain'),
    };
  // 雪
  if (code >= 71 && code <= 77)
    return {
      icon: CloudSnow,
      color: '#a5b4fc',
      label: $t('dashboard-design.widgets.weather.codes.snow'),
    };
  // 阵雨
  if (code >= 80 && code <= 82)
    return {
      icon: CloudRain,
      color: '#3b82f6',
      label: $t('dashboard-design.widgets.weather.codes.showers'),
    };
  // 阵雪
  if (code >= 85 && code <= 86)
    return {
      icon: CloudSnow,
      color: '#a5b4fc',
      label: $t('dashboard-design.widgets.weather.codes.snowShowers'),
    };
  // 雷暴
  if (code >= 95 && code <= 99)
    return {
      icon: Zap,
      color: '#eab308',
      label: $t('dashboard-design.widgets.weather.codes.thunderstorm'),
    };
  return {
    icon: Sun,
    color: '#f59e0b',
    label: $t('dashboard-design.widgets.weather.codes.clear'),
  };
}

// 风向角度转文字
function getWindDirection(degree: number): string {
  const dirs = [
    $t('dashboard-design.widgets.weather.windDir.n'),
    $t('dashboard-design.widgets.weather.windDir.ne'),
    $t('dashboard-design.widgets.weather.windDir.e'),
    $t('dashboard-design.widgets.weather.windDir.se'),
    $t('dashboard-design.widgets.weather.windDir.s'),
    $t('dashboard-design.widgets.weather.windDir.sw'),
    $t('dashboard-design.widgets.weather.windDir.w'),
    $t('dashboard-design.widgets.weather.windDir.nw'),
  ];
  const index = Math.round(degree / 45) % 8;
  return dirs[index] || '';
}

// 当前天气信息
const currentWeather = computed(() => {
  if (!weatherData.value) return null;
  const info = getWeatherInfo(weatherData.value.weatherCode);
  return {
    ...info,
    temperature: Math.round(weatherData.value.temperature),
    humidity: weatherData.value.humidity,
    wind: `${getWindDirection(weatherData.value.windDirection)} ${weatherData.value.windSpeed.toFixed(0)} km/h`,
  };
});

// 获取天气数据
async function fetchWeather() {
  const lat = props.widget.props.latitude;
  const lon = props.widget.props.longitude;
  if (!lat || !lon) return;

  try {
    error.value = false;
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m&timezone=auto`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('API error');
    const data = await res.json();
    if (data.current) {
      weatherData.value = {
        temperature: data.current.temperature_2m,
        humidity: data.current.relative_humidity_2m,
        weatherCode: data.current.weather_code,
        windSpeed: data.current.wind_speed_10m,
        windDirection: data.current.wind_direction_10m,
      };
    }
  } catch {
    error.value = true;
    console.error('Failed to fetch weather data');
  }
}

// 自动刷新
function startAutoRefresh() {
  stopAutoRefresh();
  const interval = (props.widget.props.refreshInterval || 30) * 60 * 1000; // 分钟转毫秒
  timer = setInterval(fetchWeather, interval);
}

function stopAutoRefresh() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

// 监听经纬度变化重新获取
watch(
  () => [props.widget.props.latitude, props.widget.props.longitude],
  () => {
    fetchWeather();
  },
);

onMounted(async () => {
  // 如果开启自动定位且没有经纬度
  if (props.widget.props.autoLocate && !props.widget.props.latitude) {
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          timeout: 5000,
        });
      });
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      // 并行获取天气数据和城市名
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m&timezone=auto`;
      const [res] = await Promise.all([fetch(url), reverseGeocode(lat, lon)]);
      const data = await res.json();
      if (data.current) {
        weatherData.value = {
          temperature: data.current.temperature_2m,
          humidity: data.current.relative_humidity_2m,
          weatherCode: data.current.weather_code,
          windSpeed: data.current.wind_speed_10m,
          windDirection: data.current.wind_direction_10m,
        };
      }
    } catch {
      // 定位失败，使用默认经纬度
      await fetchWeather();
    }
  } else {
    await fetchWeather();
  }
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>

<template>
  <div class="weather-widget flex h-full flex-col p-3">
    <div
      v-if="widget.props.title"
      class="text-muted-foreground mb-2 text-sm font-medium"
    >
      {{ widget.props.title }}
    </div>

    <!-- 加载/错误状态 -->
    <div
      v-if="!currentWeather && !error"
      class="flex flex-1 items-center justify-center"
    >
      <span class="text-muted-foreground text-xs">{{
        $t('dashboard-design.widgets.weather.loading')
      }}</span>
    </div>
    <div
      v-else-if="error && !currentWeather"
      class="flex flex-1 items-center justify-center"
    >
      <span class="text-muted-foreground text-xs">{{
        $t('dashboard-design.widgets.weather.error')
      }}</span>
    </div>

    <!-- 天气数据 -->
    <div v-else-if="currentWeather" class="flex flex-1 items-center gap-4">
      <!-- 天气图标和温度 -->
      <div class="flex items-center gap-3">
        <component
          :is="currentWeather.icon"
          class="h-12 w-12"
          :style="{ color: currentWeather.color }"
        />
        <div>
          <div class="temperature">{{ currentWeather.temperature }}°</div>
          <div class="weather-text">
            {{ currentWeather.label }}
          </div>
        </div>
      </div>

      <!-- 详细信息 -->
      <div class="weather-details">
        <div class="detail-item">
          <span class="detail-label">{{
            $t('dashboard-design.widgets.weather.city')
          }}</span>
          <span class="detail-value">{{ displayCityName }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">{{
            $t('dashboard-design.widgets.weather.humidity')
          }}</span>
          <span class="detail-value">{{ currentWeather.humidity }}%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">{{
            $t('dashboard-design.widgets.weather.wind')
          }}</span>
          <span class="detail-value">{{ currentWeather.wind }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.temperature {
  font-size: 2rem;
  font-weight: 600;
  line-height: 1;
  color: var(--el-text-color-primary);
}

.weather-text {
  margin-top: 4px;
  font-size: 0.875rem;
  color: var(--el-text-color-secondary);
}

.weather-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 16px;
  border-left: 1px solid var(--el-border-color-lighter);
}

.detail-item {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 0.75rem;
}

.detail-label {
  min-width: 32px;
  color: var(--el-text-color-secondary);
}

.detail-value {
  color: var(--el-text-color-primary);
}
</style>
