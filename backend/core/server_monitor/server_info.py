#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器信息收集器
"""
import platform
import socket
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import psutil


class ServerInfoCollector:
    """服务器信息收集器，支持Linux、Windows、macOS"""

    def __init__(self):
        self.system_name = platform.system()
        self.is_windows = self.system_name == 'Windows'
        self.is_linux = self.system_name == 'Linux'
        self.is_macos = self.system_name == 'Darwin'

        # 用于计算实时速度的缓存数据
        self._last_network_io = None
        self._last_network_time = None
        self._last_disk_io = None
        self._last_disk_time = None

        # 用于CPU使用率的缓存数据
        self._last_cpu_times = None
        self._last_cpu_time = None

        # 初始化CPU使用率监控
        try:
            psutil.cpu_percent(interval=None)
        except:
            pass

    def get_all_info(self) -> Dict[str, Any]:
        """获取所有服务器监控信息"""
        return {
            'basic_info': self.get_basic_info(),
            'cpu_info': self.get_cpu_info(),
            'memory_info': self.get_memory_info(),
            'disk_info': self.get_disk_info(),
            'network_info': self.get_network_info(),
            'process_info': self.get_process_info(),
            'system_load': self.get_system_load(),
            'boot_time': self.get_boot_time(),
            'users_info': self.get_users_info(),
            'timestamp': datetime.now().isoformat()
        }

    def get_basic_info(self) -> Dict[str, Any]:
        """获取基础系统信息"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except:
            hostname = "unknown"
            ip_address = "unknown"

        try:
            return {
                'hostname': hostname,
                'ip_address': ip_address,
                'system': platform.system(),
                'platform': platform.platform(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor() or "Unknown",
                'python_version': platform.python_version(),
                'machine': platform.machine(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
            }
        except Exception as e:
            print(f"Error getting basic info: {e}")
            return {
                'hostname': hostname,
                'ip_address': ip_address,
                'system': "Unknown",
                'platform': "Unknown",
                'architecture': "Unknown",
                'processor': "Unknown",
                'python_version': "Unknown",
                'machine': "Unknown",
                'node': "Unknown",
                'release': "Unknown",
                'version': "Unknown",
            }

    def get_cpu_info(self) -> Dict[str, Any]:
        """获取CPU信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            overall_cpu_percent = psutil.cpu_percent(interval=1)

            try:
                cpu_freq = psutil.cpu_freq()
            except (FileNotFoundError, OSError):
                cpu_freq = None

            return {
                'physical_cores': psutil.cpu_count(logical=False) or 0,
                'total_cores': psutil.cpu_count(logical=True) or 0,
                'cpu_percent': round(overall_cpu_percent, 2),
                'cpu_percent_per_core': [round(x, 2) for x in cpu_percent] if cpu_percent else [],
                'max_frequency': round(cpu_freq.max, 2) if cpu_freq and cpu_freq.max else 0,
                'min_frequency': round(cpu_freq.min, 2) if cpu_freq and cpu_freq.min else 0,
                'current_frequency': round(cpu_freq.current, 2) if cpu_freq and cpu_freq.current else 0,
                'cpu_times': dict(psutil.cpu_times()._asdict()),
                'cpu_stats': dict(psutil.cpu_stats()._asdict()) if hasattr(psutil, 'cpu_stats') else {}
            }
        except Exception as e:
            print(f"Error getting CPU info: {e}")
            return {
                'physical_cores': 0,
                'total_cores': 0,
                'cpu_percent': 0.0,
                'cpu_percent_per_core': [],
                'max_frequency': 0.0,
                'min_frequency': 0.0,
                'current_frequency': 0.0,
                'cpu_times': {},
                'cpu_stats': {}
            }

    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息"""
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()

        return {
            'virtual': {
                'total': self._bytes_to_gb(virtual_mem.total),
                'available': self._bytes_to_gb(virtual_mem.available),
                'used': self._bytes_to_gb(virtual_mem.used),
                'free': self._bytes_to_gb(virtual_mem.free),
                'percent': round(virtual_mem.percent, 2),
                'active': self._bytes_to_gb(getattr(virtual_mem, 'active', 0)),
                'inactive': self._bytes_to_gb(getattr(virtual_mem, 'inactive', 0)),
                'buffers': self._bytes_to_gb(getattr(virtual_mem, 'buffers', 0)),
                'cached': self._bytes_to_gb(getattr(virtual_mem, 'cached', 0)),
                'shared': self._bytes_to_gb(getattr(virtual_mem, 'shared', 0)),
            },
            'swap': {
                'total': self._bytes_to_gb(swap_mem.total),
                'used': self._bytes_to_gb(swap_mem.used),
                'free': self._bytes_to_gb(swap_mem.free),
                'percent': round(swap_mem.percent, 2),
                'sin': self._bytes_to_mb(swap_mem.sin),
                'sout': self._bytes_to_mb(swap_mem.sout),
            }
        }

    def get_disk_info(self) -> Dict[str, Any]:
        """获取磁盘信息"""
        partitions = psutil.disk_partitions()
        disk_info = {
            'partitions': [],
            'total_read_bytes': 0,
            'total_write_bytes': 0,
            'total_read_count': 0,
            'total_write_count': 0,
        }

        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_info.update({
                    'total_read_bytes': self._bytes_to_gb(disk_io.read_bytes),
                    'total_write_bytes': self._bytes_to_gb(disk_io.write_bytes),
                    'total_read_count': disk_io.read_count,
                    'total_write_count': disk_io.write_count,
                    'total_read_time': disk_io.read_time,
                    'total_write_time': disk_io.write_time,
                })
        except:
            pass

        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                disk_info['partitions'].append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'file_system': partition.fstype,
                    'total_size': self._bytes_to_gb(partition_usage.total),
                    'used': self._bytes_to_gb(partition_usage.used),
                    'free': self._bytes_to_gb(partition_usage.free),
                    'percent': round(partition_usage.percent, 2),
                })
            except PermissionError:
                continue

        return disk_info

    def get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        network_io = psutil.net_io_counters()
        per_nic = psutil.net_io_counters(pernic=True)

        connections = []
        try:
            for conn in psutil.net_connections():
                if conn.status == 'LISTEN':
                    connections.append({
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                        'status': conn.status,
                        'pid': conn.pid
                    })
        except:
            pass

        addresses = psutil.net_if_addrs()
        interface_stats = psutil.net_if_stats()

        interfaces = {}
        for interface_name, interface_addresses in addresses.items():
            interfaces[interface_name] = {
                'addresses': [],
                'stats': {
                    'is_up': False,
                    'duplex': 'unknown',
                    'speed': 0,
                    'mtu': 0
                }
            }

            for addr in interface_addresses:
                interfaces[interface_name]['addresses'].append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast,
                })

            if interface_name in interface_stats:
                stat = interface_stats[interface_name]
                interfaces[interface_name]['stats'] = {
                    'is_up': stat.isup,
                    'duplex': str(stat.duplex),
                    'speed': stat.speed,
                    'mtu': stat.mtu,
                }

        return {
            'total': {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv,
                'errin': network_io.errin,
                'errout': network_io.errout,
                'dropin': network_io.dropin,
                'dropout': network_io.dropout,
            },
            'per_interface': {
                name: {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errin': stats.errin,
                    'errout': stats.errout,
                    'dropin': stats.dropin,
                    'dropout': stats.dropout,
                }
                for name, stats in per_nic.items()
            },
            'interfaces': interfaces,
            'connections': connections[:50]
        }

    def get_process_info(self) -> Dict[str, Any]:
        """获取进程信息"""
        processes = []
        total_processes = 0
        running_processes = 0
        sleeping_processes = 0

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
                try:
                    process_info = proc.info
                    total_processes += 1

                    status = process_info.get('status', '')
                    if status == psutil.STATUS_RUNNING:
                        running_processes += 1
                    elif status == psutil.STATUS_SLEEPING:
                        sleeping_processes += 1

                    cpu_percent = process_info.get('cpu_percent', 0.0)
                    memory_percent = process_info.get('memory_percent', 0.0)

                    if cpu_percent is None:
                        cpu_percent = 0.0
                    if memory_percent is None:
                        memory_percent = 0.0

                    if cpu_percent > 1.0 or memory_percent > 1.0:
                        create_time = process_info.get('create_time')
                        if create_time:
                            create_time_str = datetime.fromtimestamp(create_time).isoformat()
                        else:
                            create_time_str = datetime.now().isoformat()

                        processes.append({
                            'pid': process_info.get('pid', 0),
                            'name': process_info.get('name', 'Unknown'),
                            'cpu_percent': round(float(cpu_percent), 2),
                            'memory_percent': round(float(memory_percent), 2),
                            'status': status or 'Unknown',
                            'create_time': create_time_str,
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError, ValueError):
                    continue

            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

        except Exception as e:
            print(f"Error getting process info: {e}")

        return {
            'total_processes': total_processes,
            'top_processes': processes[:20],
            'running_processes': running_processes,
            'sleeping_processes': sleeping_processes,
        }

    def get_system_load(self) -> Dict[str, Any]:
        """获取系统负载信息"""
        try:
            if hasattr(psutil, 'getloadavg'):
                try:
                    load_avg = psutil.getloadavg()
                    return {
                        'load_1min': round(load_avg[0], 2),
                        'load_5min': round(load_avg[1], 2),
                        'load_15min': round(load_avg[2], 2),
                        'cpu_count': psutil.cpu_count() or 1
                    }
                except:
                    pass

            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count() or 1
            return {
                'load_1min': round(cpu_percent / 100 * cpu_count, 2),
                'load_5min': round(cpu_percent / 100 * cpu_count, 2),
                'load_15min': round(cpu_percent / 100 * cpu_count, 2),
                'cpu_count': cpu_count
            }
        except Exception as e:
            print(f"Error getting system load: {e}")
            return {
                'load_1min': 0.0,
                'load_5min': 0.0,
                'load_15min': 0.0,
                'cpu_count': 1
            }

    def get_boot_time(self) -> Dict[str, Any]:
        """获取系统启动时间信息"""
        try:
            boot_timestamp = psutil.boot_time()
            boot_datetime = datetime.fromtimestamp(boot_timestamp)
            uptime_seconds = int(time.time() - boot_timestamp)

            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60

            return {
                'boot_time': boot_datetime.isoformat(),
                'uptime_seconds': uptime_seconds,
                'uptime_formatted': f"{days}天 {hours}小时 {minutes}分钟",
                'uptime_days': days,
                'uptime_hours': hours,
                'uptime_minutes': minutes,
            }
        except Exception as e:
            print(f"Error getting boot time: {e}")
            return {
                'boot_time': datetime.now().isoformat(),
                'uptime_seconds': 0,
                'uptime_formatted': "0天 0小时 0分钟",
                'uptime_days': 0,
                'uptime_hours': 0,
                'uptime_minutes': 0,
            }

    def get_users_info(self) -> List[Dict[str, Any]]:
        """获取用户信息"""
        users = []
        try:
            for user in psutil.users():
                users.append({
                    'name': user.name,
                    'terminal': user.terminal,
                    'host': user.host,
                    'started': datetime.fromtimestamp(user.started).isoformat() if user.started else None,
                    'pid': getattr(user, 'pid', None),
                })
        except:
            pass

        return users

    def get_temperature_info(self) -> Dict[str, Any]:
        """获取温度信息（如果支持的话）"""
        temps = {}
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                sensors = psutil.sensors_temperatures()
                for name, entries in sensors.items():
                    temps[name] = []
                    for entry in entries:
                        temps[name].append({
                            'label': entry.label,
                            'current': entry.current,
                            'high': entry.high,
                            'critical': entry.critical,
                        })
        except:
            pass

        return temps

    def get_battery_info(self) -> Optional[Dict[str, Any]]:
        """获取电池信息（适用于笔记本电脑）"""
        try:
            if hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    return {
                        'percent': battery.percent,
                        'power_plugged': battery.power_plugged,
                        'seconds_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
                    }
        except:
            pass

        return None

    def _bytes_to_gb(self, bytes_value: int) -> float:
        """将字节转换为GB"""
        return round(bytes_value / (1024 ** 3), 2)

    def _bytes_to_mb(self, bytes_value: int) -> float:
        """将字节转换为MB"""
        return round(bytes_value / (1024 ** 2), 2)

    def get_realtime_stats(self) -> Dict[str, Any]:
        """获取实时统计信息（用于实时更新）"""
        current_time = time.time()

        # 获取当前网络IO统计
        current_network_io = psutil.net_io_counters()
        upload_speed = 0.0
        download_speed = 0.0

        if (self._last_network_io is not None and
                self._last_network_time is not None and
                current_network_io is not None):
            time_diff = current_time - self._last_network_time
            if time_diff > 0:
                bytes_sent_diff = current_network_io.bytes_sent - self._last_network_io.bytes_sent
                bytes_recv_diff = current_network_io.bytes_recv - self._last_network_io.bytes_recv

                upload_speed = max(0, bytes_sent_diff / time_diff)
                download_speed = max(0, bytes_recv_diff / time_diff)

        if current_network_io:
            self._last_network_io = current_network_io
            self._last_network_time = current_time

        # 获取当前磁盘IO统计
        current_disk_io = psutil.disk_io_counters()
        read_speed = 0.0
        write_speed = 0.0

        if (self._last_disk_io is not None and
                self._last_disk_time is not None and
                current_disk_io is not None):
            time_diff = current_time - self._last_disk_time
            if time_diff > 0:
                read_bytes_diff = current_disk_io.read_bytes - self._last_disk_io.read_bytes
                write_bytes_diff = current_disk_io.write_bytes - self._last_disk_io.write_bytes

                read_speed = max(0, read_bytes_diff / time_diff)
                write_speed = max(0, write_bytes_diff / time_diff)

        if current_disk_io:
            self._last_disk_io = current_disk_io
            self._last_disk_time = current_time

        # 获取CPU详细信息
        cpu_percent_per_core = psutil.cpu_percent(interval=None, percpu=True)
        overall_cpu_percent = psutil.cpu_percent(interval=None)

        if overall_cpu_percent == 0.0 and cpu_percent_per_core and not all(
                core == 0.0 for core in cpu_percent_per_core):
            overall_cpu_percent = sum(cpu_percent_per_core) / len(cpu_percent_per_core)

        elif overall_cpu_percent == 0.0 and all(core == 0.0 for core in cpu_percent_per_core):
            try:
                overall_cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            except:
                pass

        try:
            cpu_freq = psutil.cpu_freq()
        except (FileNotFoundError, OSError):
            cpu_freq = None

        # 获取内存详细信息
        virtual_mem = psutil.virtual_memory()

        # 获取系统负载
        load_info = {}
        try:
            if hasattr(psutil, 'getloadavg'):
                try:
                    load_avg = psutil.getloadavg()
                    load_info = {
                        'load_1min': round(load_avg[0], 2),
                        'load_5min': round(load_avg[1], 2),
                        'load_15min': round(load_avg[2], 2),
                    }
                except:
                    pass

            if not load_info:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count() or 1
                load_info = {
                    'load_1min': round(cpu_percent / 100 * cpu_count, 2),
                    'load_5min': round(cpu_percent / 100 * cpu_count, 2),
                    'load_15min': round(cpu_percent / 100 * cpu_count, 2),
                }
        except:
            load_info = {
                'load_1min': 0.0,
                'load_5min': 0.0,
                'load_15min': 0.0,
            }

        # 获取进程统计信息
        total_processes = 0
        running_processes = 0
        sleeping_processes = 0
        top_processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
                try:
                    process_info = proc.info
                    total_processes += 1

                    status = process_info.get('status', '')
                    if status == psutil.STATUS_RUNNING:
                        running_processes += 1
                    elif status == psutil.STATUS_SLEEPING:
                        sleeping_processes += 1

                    cpu_percent = process_info.get('cpu_percent', 0.0)
                    memory_percent = process_info.get('memory_percent', 0.0)

                    if cpu_percent is None:
                        cpu_percent = 0.0
                    if memory_percent is None:
                        memory_percent = 0.0

                    if cpu_percent > 0.5 or memory_percent > 0.5:
                        create_time = process_info.get('create_time')
                        if create_time:
                            create_time_str = datetime.fromtimestamp(create_time).isoformat()
                        else:
                            create_time_str = datetime.now().isoformat()

                        top_processes.append({
                            'pid': process_info.get('pid', 0),
                            'name': process_info.get('name', 'Unknown'),
                            'cpu_percent': round(float(cpu_percent), 2),
                            'memory_percent': round(float(memory_percent), 2),
                            'status': status or 'Unknown',
                            'create_time': create_time_str,
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError, ValueError):
                    continue

            top_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_processes = top_processes[:15]

        except Exception as e:
            print(f"Error getting process info in realtime: {e}")

        # 获取网络接口详细统计
        per_nic = psutil.net_io_counters(pernic=True)
        per_interface_stats = {}
        for name, stats in per_nic.items():
            per_interface_stats[name] = {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin,
                'errout': stats.errout,
                'dropin': stats.dropin,
                'dropout': stats.dropout,
            }

        # 获取网络连接
        connections = []
        try:
            for conn in psutil.net_connections():
                if conn.status == 'LISTEN':
                    connections.append({
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                        'status': conn.status,
                        'pid': conn.pid
                    })
                    if len(connections) >= 50:
                        break
        except:
            pass

        return {
            'cpu_percent': round(overall_cpu_percent, 2),
            'memory_percent': round(virtual_mem.percent, 2),
            'disk_io': {
                'read_speed': read_speed,
                'write_speed': write_speed,
            },
            'network_io': {
                'upload_speed': upload_speed,
                'download_speed': download_speed,
            },
            'network_total': {
                'bytes_sent': current_network_io.bytes_sent if current_network_io else 0,
                'bytes_recv': current_network_io.bytes_recv if current_network_io else 0,
                'packets_sent': current_network_io.packets_sent if current_network_io else 0,
                'packets_recv': current_network_io.packets_recv if current_network_io else 0,
            },
            'disk_total': {
                'read_bytes': current_disk_io.read_bytes if current_disk_io else 0,
                'write_bytes': current_disk_io.write_bytes if current_disk_io else 0,
                'read_count': current_disk_io.read_count if current_disk_io else 0,
                'write_count': current_disk_io.write_count if current_disk_io else 0,
            },
            'cpu_details': {
                'current_frequency': round(cpu_freq.current, 2) if cpu_freq and cpu_freq.current else 0,
                'cpu_percent_per_core': [round(x, 2) for x in cpu_percent_per_core] if cpu_percent_per_core else [],
            },
            'memory_details': {
                'total': self._bytes_to_gb(virtual_mem.total),
                'available': self._bytes_to_gb(virtual_mem.available),
                'used': self._bytes_to_gb(virtual_mem.used),
                'free': self._bytes_to_gb(virtual_mem.free),
            },
            'system_load': load_info,
            'process_stats': {
                'total_processes': total_processes,
                'running_processes': running_processes,
                'sleeping_processes': sleeping_processes,
            },
            'process_info': {
                'total_processes': total_processes,
                'top_processes': top_processes,
                'running_processes': running_processes,
                'sleeping_processes': sleeping_processes,
            },
            'network_interfaces': per_interface_stats,
            'network_connections': connections,
            'timestamp': datetime.now().isoformat()
        }
