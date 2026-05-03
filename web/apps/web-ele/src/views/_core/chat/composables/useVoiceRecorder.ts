import { onBeforeUnmount, ref } from 'vue';

export function useVoiceRecorder() {
  const isRecording = ref(false);
  const duration = ref(0);
  const isPaused = ref(false);

  let mediaRecorder: MediaRecorder | null = null;
  let audioChunks: Blob[] = [];
  let stream: MediaStream | null = null;
  let timer: null | ReturnType<typeof setInterval> = null;
  let startTime = 0;

  function startTimer() {
    startTime = Date.now();
    duration.value = 0;
    timer = setInterval(() => {
      duration.value = Math.floor((Date.now() - startTime) / 1000);
    }, 200);
  }

  function stopTimer() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  async function startRecording(): Promise<boolean> {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      return false;
    }

    audioChunks = [];

    // 优先使用 webm/opus，兼容性好
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : (MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : '');

    mediaRecorder = mimeType
      ? new MediaRecorder(stream, { mimeType })
      : new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data);
      }
    };

    mediaRecorder.start(100); // 每 100ms 收集一次数据
    isRecording.value = true;
    isPaused.value = false;
    startTimer();
    return true;
  }

  function stopRecording(): Promise<null | { blob: Blob; duration: number }> {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        cleanup();
        resolve(null);
        return;
      }

      const finalDuration = Math.max(
        1,
        Math.round((Date.now() - startTime) / 1000),
      );

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, {
          type: mediaRecorder?.mimeType || 'audio/webm',
        });
        cleanup();
        resolve({ blob, duration: finalDuration });
      };

      mediaRecorder.stop();
    });
  }

  function cancelRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.onstop = null;
      mediaRecorder.stop();
    }
    cleanup();
  }

  function cleanup() {
    stopTimer();
    isRecording.value = false;
    isPaused.value = false;
    duration.value = 0;
    audioChunks = [];
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    mediaRecorder = null;
  }

  onBeforeUnmount(() => {
    if (isRecording.value) {
      cancelRecording();
    }
  });

  return {
    isRecording,
    duration,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}

/**
 * 格式化录音时长为 mm:ss
 */
export function formatVoiceDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
