#!/bin/bash
set -e

host="$1"
port="$2"
timeout="${3:-60}"

if [ -z "$host" ] || [ -z "$port" ]; then
    echo "用法: $0 <host> <port> [timeout]"
    exit 1
fi

echo "等待 $host:$port (超时: ${timeout}s)..."

end_time=$(($(date +%s) + timeout))
while [ $(date +%s) -lt $end_time ]; do
    if timeout 1 bash -c "echo > /dev/tcp/${host}/${port}" 2>/dev/null; then
        echo "$host:$port 已可用"
        exit 0
    fi
    sleep 2
done

echo "错误: $host:$port 在 ${timeout} 秒内未能连接"
exit 1
