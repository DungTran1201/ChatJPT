import os
import shutil
import platform
import ctypes
from typing import Dict, Any

class HardwareInspectionService:
    """Zero-dependency hardware resource inspection service using OS primitives."""

    @classmethod
    def get_hardware_specs(cls) -> Dict[str, Any]:
        """Inspects CPU cores, Total RAM, Available RAM, and Free Disk space."""
        # 1. CPU cores
        cpu_cores = os.cpu_count() or 1

        # 2. Total & Available RAM
        total_ram_gb = 0.0
        avail_ram_gb = 0.0

        if platform.system() == "Windows":
            try:
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                total_ram_gb = round(stat.ullTotalPhys / (1024**3), 2)
                avail_ram_gb = round(stat.ullAvailPhys / (1024**3), 2)
            except Exception:
                # Fallback estimate
                total_ram_gb = 8.0
                avail_ram_gb = 3.0
        else:
            # POSIX / Linux / macOS
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                mem_total = 0
                mem_avail = 0
                for line in meminfo.splitlines():
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1]) * 1024
                    elif line.startswith("MemAvailable:"):
                        mem_avail = int(line.split()[1]) * 1024
                if mem_total:
                    total_ram_gb = round(mem_total / (1024**3), 2)
                if mem_avail:
                    avail_ram_gb = round(mem_avail / (1024**3), 2)
            except Exception:
                total_ram_gb = 8.0
                avail_ram_gb = 3.0

        # 3. Free Disk Space
        try:
            disk = shutil.disk_usage('.')
            free_disk_gb = round(disk.free / (1024**3), 2)
        except Exception:
            free_disk_gb = 10.0

        return {
            "cpu_cores": cpu_cores,
            "total_ram_gb": total_ram_gb,
            "avail_ram_gb": avail_ram_gb,
            "free_disk_gb": free_disk_gb,
            "os_name": f"{platform.system()} {platform.release()}",
            "architecture": platform.machine()
        }

    @classmethod
    def evaluate_eligibility(
        cls,
        min_ram_gb: float = 4.0,
        min_avail_ram_gb: float = 1.5,
        min_disk_gb: float = 1.5,
        min_cpu_cores: int = 2
    ) -> Dict[str, Any]:
        """Evaluates whether current host machine satisfies prerequisites for embedded model."""
        specs = cls.get_hardware_specs()

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
                "passed": cpu_passed
            },
            {
                "id": "total_ram",
                "name": "Total System RAM",
                "required": f">= {min_ram_gb:.1f} GB",
                "actual": f"{specs['total_ram_gb']:.1f} GB",
                "passed": total_ram_passed
            },
            {
                "id": "avail_ram",
                "name": "Available Free RAM",
                "required": f">= {min_avail_ram_gb:.1f} GB",
                "actual": f"{specs['avail_ram_gb']:.1f} GB",
                "passed": avail_ram_passed
            },
            {
                "id": "free_disk",
                "name": "Free Disk Space",
                "required": f">= {min_disk_gb:.1f} GB",
                "actual": f"{specs['free_disk_gb']:.1f} GB",
                "passed": disk_passed
            }
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
                "min_disk_gb": min_disk_gb
            },
            "checks": checks,
            "message": msg
        }
