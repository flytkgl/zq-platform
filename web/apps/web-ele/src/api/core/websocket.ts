/**
 * WebSocket API
 */
import { useAccessStore } from '@vben/stores';

import { refreshTokenApi } from './auth';

export namespace WebSocketApi {
  /** WebSocket消息类型 */
  export interface WebSocketMessage {
    type: string;
    content?: string;
    timestamp?: string;
    data?: any;
    interval?: number;
    [key: string]: any;
  }

  /** WebSocket回调函数 */
  export interface WebSocketCallbacks {
    onOpen?: (event: Event) => void;
    onMessage?: (message: WebSocketMessage) => void;
    onClose?: (event: CloseEvent) => void;
    onError?: (event: Event) => void;
    onReconnect?: (attempt: number) => void;
  }

  /** WebSocket连接状态 */
  export type ConnectionStatus = 'CLOSED' | 'CLOSING' | 'CONNECTING' | 'OPEN';

  /** WebSocket连接配置 */
  export interface WebSocketConfig {
    url: string;
    protocols?: string | string[];
    reconnect?: boolean;
    maxReconnectAttempts?: number;
    reconnectInterval?: number;
    heartbeat?: boolean;
    heartbeatInterval?: number;
  }

  /** 监控数据类型 */
  export interface MonitorMessage {
    type:
      | 'get_overview'
      | 'get_realtime'
      | 'set_interval'
      | 'start_monitor'
      | 'stop_monitor'
      | 'test_connection';
    interval?: number;
    timestamp?: string;
  }

  /** 服务器监控数据 */
  export interface ServerMonitorData {
    basic_info?: any;
    cpu_info?: any;
    memory_info?: any;
    disk_info?: any;
    network_info?: any;
    process_info?: any;
    system_load?: any;
    boot_time?: any;
    users_info?: any;
    timestamp?: string;
  }

  /** Redis监控数据 */
  export interface RedisMonitorData {
    connection_id?: string;
    connection_name?: string;
    status?: string;
    info?: any;
    memory?: any;
    stats?: any;
    keyspace?: any[];
    clients?: any[];
    slow_log?: any[];
    timestamp?: string;
  }
}

/**
 * WebSocket管理类
 */
export class WebSocketManager {
  /**
   * 是否已连接
   */
  get isConnected(): boolean {
    return this.status === 'OPEN';
  }
  /**
   * 获取连接状态
   */
  get status(): WebSocketApi.ConnectionStatus {
    if (!this.ws) return 'CLOSED';

    switch (this.ws.readyState) {
      case WebSocket.CLOSING: {
        return 'CLOSING';
      }
      case WebSocket.CONNECTING: {
        return 'CONNECTING';
      }
      case WebSocket.OPEN: {
        return 'OPEN';
      }
      default: {
        return 'CLOSED';
      }
    }
  }
  private callbacks: WebSocketApi.WebSocketCallbacks;
  private config: WebSocketApi.WebSocketConfig;
  private heartbeatTimer: null | number = null;
  private isManualClose = false;
  private isTokenExpiredClose = false;
  private reconnectAttempts = 0;

  private reconnectTimer: null | number = null;

  private ws: null | WebSocket = null;

  constructor(
    config: WebSocketApi.WebSocketConfig,
    callbacks: WebSocketApi.WebSocketCallbacks = {},
  ) {
    this.config = {
      reconnect: true,
      maxReconnectAttempts: 5,
      reconnectInterval: 3000,
      heartbeat: true,
      heartbeatInterval: 30_000,
      ...config,
    };
    this.callbacks = callbacks;
  }

  /**
   * 关闭连接
   */
  close(code?: number, reason?: string): void {
    this.isManualClose = true;
    this.stopHeartbeat();
    this.clearReconnectTimer();

    if (this.ws) {
      this.ws.close(code, reason);
      this.ws = null;
    }
  }

  /**
   * 连接WebSocket
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.isManualClose = false;

        // 获取访问令牌
        const accessStore = useAccessStore();
        const token = accessStore.accessToken;

        if (!token) {
          reject(new Error('未找到访问令牌'));
          return;
        }

        // 构建带token的URL
        const separator = this.config.url.includes('?') ? '&' : '?';
        const wsUrl = `${this.config.url}${separator}token=${encodeURIComponent(token)}`;

        console.log(
          'Connecting to WebSocket:',
          wsUrl.replace(/token=[^&]+/, 'token=***'),
        );
        console.log('WebSocket URL详情:', {
          originalUrl: this.config.url,
          finalUrl: wsUrl.replace(/token=[^&]+/, 'token=***'),
          isDev: import.meta.env.DEV,
        });

        this.ws = new WebSocket(wsUrl, this.config.protocols);

        this.ws.addEventListener('open', (event) => {
          console.log('WebSocket连接已建立');
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.callbacks.onOpen?.(event);
          resolve();
        });

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketApi.WebSocketMessage = JSON.parse(
              event.data,
            );

            // 处理心跳响应
            if (message.type === 'pong') {
              return;
            }

            // 处理token过期通知：刷新token后自动重连
            if (message.type === 'token_expired') {
              console.warn(
                '[WebSocket] 收到token_expired，准备刷新token并重连',
              );
              this.isTokenExpiredClose = true;
              return;
            }

            this.callbacks.onMessage?.(message);
          } catch (error) {
            console.error('解析WebSocket消息失败:', error);
          }
        };

        this.ws.addEventListener('close', (event) => {
          console.log('WebSocket连接已关闭', event.code, event.reason);
          this.stopHeartbeat();
          this.callbacks.onClose?.(event);

          // token过期关闭：刷新token后立即重连（不计入重连次数）
          if (this.isTokenExpiredClose || event.code === 4002) {
            this.isTokenExpiredClose = false;
            this.handleTokenExpiredReconnect();
            return;
          }

          // 如果不是手动关闭且启用了重连，则尝试重连
          if (!this.isManualClose && this.config.reconnect) {
            this.handleReconnect();
          }
        });

        this.ws.onerror = (event) => {
          console.error('WebSocket连接错误', event);
          this.callbacks.onError?.(event);
          reject(new Error('WebSocket连接失败'));
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 发送消息
   */
  send(message: WebSocketApi.WebSocketMessage): boolean {
    if (!this.isConnected) {
      console.warn('WebSocket未连接，无法发送消息');
      return false;
    }

    try {
      this.ws!.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
      return false;
    }
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 确保accessToken有效，如果无效则用refreshToken刷新
   * 用于普通重连场景
   */
  private async ensureFreshToken(): Promise<void> {
    const accessStore = useAccessStore();

    // 如果没有refreshToken，无法刷新
    if (!accessStore.refreshToken) {
      throw new Error('No refresh token available');
    }

    // 如果已有accessToken，先尝试使用（可能还没过期）
    if (accessStore.accessToken) {
      return;
    }

    // accessToken为空，需要刷新
    await this.forceRefreshToken();
  }

  /**
   * 强制刷新token，用于后端明确通知token_expired的场景
   */
  private async forceRefreshToken(): Promise<void> {
    const accessStore = useAccessStore();

    if (!accessStore.refreshToken) {
      throw new Error('No refresh token available');
    }

    console.log('[WebSocket] 使用refreshToken刷新accessToken...');
    const resp = await refreshTokenApi(accessStore.refreshToken);
    const newToken = resp.data?.accessToken || '';
    if (!newToken) {
      throw new Error('Token refresh returned empty token');
    }
    accessStore.setAccessToken(newToken);
    if (typeof resp.data === 'object' && resp.data?.refreshToken) {
      accessStore.setRefreshToken(resp.data.refreshToken);
    }
  }

  /**
   * 处理重连
   */
  private handleReconnect(): void {
    if (
      this.reconnectAttempts >= (this.config.maxReconnectAttempts || 5) ||
      this.isManualClose
    ) {
      console.log('WebSocket重连次数已达上限或手动关闭');
      return;
    }

    this.reconnectAttempts++;
    console.log(
      `WebSocket重连中... (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`,
    );

    this.callbacks.onReconnect?.(this.reconnectAttempts);

    this.reconnectTimer = window.setTimeout(async () => {
      try {
        // 重连前确保token有效
        await this.ensureFreshToken();
        this.ws = null;
        await this.connect();
      } catch (error) {
        console.error('WebSocket重连失败:', error);
      }
    }, this.config.reconnectInterval || 3000);
  }

  /**
   * 处理token过期后的重连：先刷新token再重连，不计入重连次数
   */
  private handleTokenExpiredReconnect(): void {
    if (this.isManualClose) return;

    console.log('[WebSocket] Token过期，尝试刷新token后重连...');

    this.forceRefreshToken()
      .then(() => {
        console.log('[WebSocket] Token刷新成功，重新连接...');
        this.ws = null;
        return this.connect();
      })
      .catch((error) => {
        console.error('[WebSocket] Token刷新失败，无法重连:', error);
      });
  }

  /**
   * 开始心跳检测
   */
  private startHeartbeat(): void {
    if (!this.config.heartbeat) return;

    this.heartbeatTimer = window.setInterval(() => {
      if (this.isConnected) {
        this.send({
          type: 'ping',
          timestamp: new Date().toISOString(),
        });
      }
    }, this.config.heartbeatInterval || 30_000);
  }

  /**
   * 停止心跳检测
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

/**
 * 创建WebSocket连接
 */
export function createWebSocket(
  endpoint: string,
  callbacks?: WebSocketApi.WebSocketCallbacks,
): WebSocketManager {
  // 构建WebSocket URL
  let wsUrl: string;

  if (import.meta.env.DEV) {
    // 开发环境：直接连接到后端服务器
    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl = `${wsProtocol}//localhost:8000${endpoint}`;
  } else {
    // 生产环境：使用当前域名
    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = location.host;
    wsUrl = `${wsProtocol}//${wsHost}${endpoint}`;
  }

  const config: WebSocketApi.WebSocketConfig = {
    url: wsUrl,
    reconnect: true,
    maxReconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeat: true,
    heartbeatInterval: 30_000,
  };

  return new WebSocketManager(config, callbacks);
}

/**
 * 创建测试WebSocket连接
 */
export function createTestWebSocket(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): WebSocketManager {
  return createWebSocket('/ws/test/', callbacks);
}

/**
 * 创建通知WebSocket连接
 */
export function createNotificationWebSocket(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): WebSocketManager {
  return createWebSocket('/ws/notifications/', callbacks);
}

/**
 * 创建服务器监控WebSocket连接
 */
export function createServerMonitorWebSocket(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): WebSocketManager {
  return createWebSocket('/ws/server-monitor/', callbacks);
}

/**
 * 创建Redis监控WebSocket连接
 */
export function createRedisMonitorWebSocket(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): WebSocketManager {
  return createWebSocket('/ws/redis-monitor/', callbacks);
}

/**
 * 创建数据库监控WebSocket连接
 */
export function createDatabaseMonitorWebSocket(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): WebSocketManager {
  return createWebSocket('/ws/database-monitor/', callbacks);
}

/**
 * 监控WebSocket管理器类
 */
export class MonitorWebSocketManager extends WebSocketManager {
  /**
   * 获取概览信息
   */
  getOverview(): boolean {
    return this.send({
      type: 'get_overview',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 获取实时统计
   */
  getRealtime(): boolean {
    return this.send({
      type: 'get_realtime',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 开始监控
   */
  startMonitoring(): boolean {
    return this.send({
      type: 'start_monitor',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 停止监控
   */
  stopMonitoring(): boolean {
    return this.send({
      type: 'stop_monitor',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 测试连接（适用于Redis监控）
   */
  testConnection(): boolean {
    return this.send({
      type: 'test_connection',
      timestamp: new Date().toISOString(),
    });
  }
}

/**
 * 创建服务器监控WebSocket管理器
 */
export function createServerMonitorManager(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): MonitorWebSocketManager {
  const wsManager = createServerMonitorWebSocket(callbacks);
  // 创建增强版管理器
  return Object.setPrototypeOf(wsManager, MonitorWebSocketManager.prototype);
}

/**
 * 创建Redis监控WebSocket管理器
 */
export function createRedisMonitorManager(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): MonitorWebSocketManager {
  const wsManager = createRedisMonitorWebSocket(callbacks);
  // 创建增强版管理器
  return Object.setPrototypeOf(wsManager, MonitorWebSocketManager.prototype);
}

/**
 * 数据库监控WebSocket管理器类
 */
export class DatabaseMonitorWebSocketManager extends WebSocketManager {
  /**
   * 获取数据库配置列表
   */
  getConfigs(): boolean {
    return this.send({
      type: 'get_configs',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 获取概览信息
   */
  getOverview(dbName: string): boolean {
    return this.send({
      type: 'get_overview',
      db_name: dbName,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 获取实时统计
   */
  getRealtime(dbName: string): boolean {
    return this.send({
      type: 'get_realtime',
      db_name: dbName,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 开始监控
   */
  startMonitoring(dbName: string): boolean {
    return this.send({
      type: 'start_monitor',
      db_name: dbName,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 停止监控
   */
  stopMonitoring(): boolean {
    return this.send({
      type: 'stop_monitor',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * 测试连接
   */
  testConnection(dbName: string): boolean {
    return this.send({
      type: 'test_connection',
      db_name: dbName,
      timestamp: new Date().toISOString(),
    });
  }
}

/**
 * 创建聊天WebSocket连接
 */
export function createChatWebSocket(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): WebSocketManager {
  return createWebSocket('/ws/chat/', callbacks);
}

/**
 * 创建数据库监控WebSocket管理器
 */
export function createDatabaseMonitorManager(
  callbacks?: WebSocketApi.WebSocketCallbacks,
): DatabaseMonitorWebSocketManager {
  const wsManager = createDatabaseMonitorWebSocket(callbacks);
  // 创建增强版管理器
  return Object.setPrototypeOf(
    wsManager,
    DatabaseMonitorWebSocketManager.prototype,
  );
}
