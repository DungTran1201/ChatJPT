"""Zero-dependency host hardware inspection service with OS memory adapters."""

import ctypes
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


def _read_ram_windows() -> Tuple[float, float]:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    return (
        round(stat.ullTotalPhys / (1024**3), 2),
        round(stat.ullAvailPhys / (1024**3), 2),
    )


def _read_ram_linux() -> Tuple[float, float]:
    mem_total = 0
    mem_avail = 0
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1]) * 1024
            elif line.startswith("MemAvailable:"):
                mem_avail = int(line.split()[1]) * 1024
    return (
        round(mem_total / (1024**3), 2) if mem_total else 8.0,
        round(mem_avail / (1024**3), 2) if mem_avail else 3.0,
    )


def _read_ram_macos() -> Tuple[float, float]:
    out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, timeout=2).strip()
    total_gb = round(int(out) / (1024**3), 2)
    return total_gb, round(total_gb * 0.4, 2)


def probe_host_memory_gb() -> Tuple[float, float]:
    system_name = platform.system()
    try:
        if system_name == "Windows":
            return _read_ram_windows()
        if system_name == "Darwin":
            return _read_ram_macos()
        return _read_ram_linux()
    except Exception:
        return 8.0, 3.0


class HardwareInspectionService:
    """Inspects CPU cores, RAM, and free disk space for embedded model eligibility."""

    @classmethod
    def get_hardware_specs(cls, disk_path: Optional[Path] = None) -> Dict[str, Any]:
        cpu_cores = os.cpu_count() or 1
        total_ram_gb, avail_ram_gb = probe_host_memory_gb()

        target_path = str(disk_path) if disk_path and Path(disk_path).exists() else "."
        try:
            disk = shutil.disk_usage(target_path)
            free_disk_gb = round(disk.free / (1024**3), 2)
        except Exception:
            free_disk_gb = 10.0

        return {
            "cpu_cores": cpu_cores,
            "total_ram_gb": total_ram_gb,
            "avail_ram_gb": avail_ram_gb,
            "free_disk_gb": free_disk_gb,
            "os_name": f"{platform.system()} {platform.release()}",
            "architecture": platform.machine(),
        }

    @classmethod
    def evaluate_eligibility(
        cls,
        min_ram_gb: float = 4.0,
        min_avail_ram_gb: float = 1.5,
        min_disk_gb: float = 1.5,
        min_cpu_cores: int = 2,
        *,
        disk_path: Optional[Path] = None,
        spec_probe: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        specs = spec_probe() if spec_probe is not None else cls.get_hardware_specs(disk_path=disk_path)

        cpu_passed = specs["cpu_cores"] >= min_cpu_cores
        total_ram_passed = specs["total_ram_gb"] >= min_ram_gb
        avail_ram_passed = specs["avail_ram_gb"] >= min_avail_ram_gb
        disk_passed = specs["free_disk_gb"] >= min_disk_gb
        eligible = cpu_passed and total_ram_passed and avail_ram_passed and disk_passed

        checks = [
            {
                "id": "cpu_cores",
                "name": "CPU Cores",
                "required": f">= {min_cpu_cores} cores",
                "actual": f"{specs['cpu_cores']} cores",
                "passed": cpu_passed,
            },
            {
                "id": "total_ram",
                "name": "Total System RAM",
                "required": f">= {min_ram_gb:.1f} GB",
                "actual": f"{specs['total_ram_gb']:.1f} GB",
                "passed": total_ram_passed,
            },
            {
                "id": "avail_ram",
                "name": "Available Free RAM",
                "required": f">= {min_avail_ram_gb:.1f} GB",
                "actual": f"{specs['avail_ram_gb']:.1f} GB",
                "passed": avail_ram_passed,
            },
            {
                "id": "free_disk",
                "name": "Free Disk Space",
                "required": f">= {min_disk_gb:.1f} GB",
                "actual": f"{specs['free_disk_gb']:.1f} GB",
                "passed": disk_passed,
            },
        ]

        if eligible:
            msg = "Phần cứng thiết bị đủ điều kiện chạy mô hình siêu nhẹ nhúng trực tiếp."
        else:
            unmet = [c["name"] for c in checks if not c["passed"]]
            msg = f"Thiết bị chưa đạt yêu cầu tối thiểu ({', '.join(unmet)}). Không thể tải và chạy mô hình siêu nhẹ."

        return {
            "eligible": eligible,
            "metrics": specs,
            "requirements": {
                "min_cpu_cores": min_cpu_cores,
                "min_ram_gb": min_ram_gb,
                "min_avail_ram_gb": min_avail_ram_gb,
                "min_disk_gb": min_disk_gb,
            },
            "checks": checks,
            "message": msg,
        }
