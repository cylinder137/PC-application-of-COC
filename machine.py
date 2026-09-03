# -*- coding: utf-8 -*-
"""机器码采集（v0.1 简化版）

⚠️ TODO(v1.0)：与 coBrain 桌面端统一为稳定硬件指纹算法
（主板序列号 + 磁盘序列号 + 网卡 MAC 的组合哈希），保证换网络/重装系统不变。
当前版本：主板序列号 + 磁盘序列号组合（缺失时回退 MAC+主机名），用于联调与页面演示。
"""
import hashlib
import platform
import socket
import subprocess
import uuid


def _wmic(cmd: str) -> str:
    """尝试用 wmic 取硬件序列号（失败返回空串）"""
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, timeout=6)
        text = out.stdout.decode('utf-8', errors='ignore').strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines[-1] if lines else ''
    except Exception:
        return ''


def _collect_fingerprint_parts() -> list:
    """采集稳定硬件指纹片段（主板/磁盘序列号）"""
    parts = []
    mb = _wmic('wmic baseboard get serialnumber')
    if mb and mb.upper() not in ('SERIALNUMBER', 'TO BE FILLED BY O.E.M.', 'DEFAULT STRING', 'NONE'):
        parts.append('MB:' + mb)
    disk = _wmic('wmic diskdrive get serialnumber')
    if disk and disk.upper() not in ('SERIALNUMBER', 'NONE'):
        parts.append('DISK:' + disk)
    return parts


def get_fingerprint_source() -> str:
    """指纹源描述（调试用）"""
    parts = _collect_fingerprint_parts()
    if parts:
        return '硬件指纹: ' + ' | '.join(parts)
    return '回退指纹: MAC + 主机名 + 系统信息'


def get_machine_code() -> str:
    """生成机器码：优先硬件指纹，缺失时回退 MAC+主机名（sha256 摘要）"""
    parts = _collect_fingerprint_parts()
    if parts:
        raw = '|'.join(parts)
    else:
        mac = uuid.getnode()
        mac_hex = ':'.join(f'{(mac >> bits) & 0xff:02x}' for bits in range(40, -1, -8))
        raw = f'{mac_hex}|{socket.gethostname()}|{platform.system()}|{platform.release()}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


if __name__ == '__main__':
    print('机器码:', get_machine_code())
    print('指纹源:', get_fingerprint_source())
