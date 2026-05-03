<script lang="ts" setup>
interface Props {
  companyName?: string;
  companySiteLink?: string;
  date?: string;
  icp?: string;
  icpLink?: string;
  policeIcp?: string;
  policeIcpLink?: string;
}

defineOptions({
  name: 'Copyright',
});

withDefaults(defineProps<Props>(), {
  companyName: 'ZQ-Platform',
  companySiteLink: '',
  date: '2025',
  icp: '',
  icpLink: '',
  policeIcp: '',
  policeIcpLink: '',
});
</script>

<template>
  <div class="text-md flex-center flex-wrap gap-x-1">
    <!-- Copyright Text -->
    Copyright © {{ date }}

    <!-- Company Link -->
    <a
      v-if="companyName"
      :href="companySiteLink || 'javascript:void(0)'"
      class="hover:text-primary-hover"
      target="_blank"
    >
      {{ companyName }}
    </a>

    <!-- ICP Link -->
    <a
      v-if="icp"
      :href="icpLink || 'javascript:void(0)'"
      class="hover:text-primary-hover"
      target="_blank"
    >
      {{ icp }}
    </a>

    <!-- Police ICP Link -->
    <a
      v-if="policeIcp"
      :href="policeIcpLink || 'javascript:void(0)'"
      class="hover:text-primary-hover"
      target="_blank"
    >
      {{ policeIcp }}
    </a>
  </div>
</template>
