# -*- coding: utf-8 -*-
"""
GPU and Runtime Smoke Test
Xác minh runtime PyTorch CUDA, PyTorch Geometric và các thao tác tensor CPU/GPU quy mô nhỏ
đối chiếu nghiêm ngặt với experiments/environment/ENVIRONMENT-LOCK.json.
KHÔNG HUẤN LUYỆN MÔ HÌNH, KHÔNG BENCHMARK, KHÔNG TRUY CẬP TẬP DỮ LIỆU.
CHỐT CHẶN PASS/FAIL NGHIÊM NGẶT: Thoát với mã lỗi khác 0 nếu BẤT KỲ kiểm tra nào thất bại.
"""

import os
import sys
import json
from pathlib import Path

# Tự động phát hiện gốc kho lưu trữ
REPO_ROOT = Path(__file__).resolve().parent.parent

def run_smoke_test() -> bool:
    print("=" * 75)
    print("  GPU AND RUNTIME SMOKE TEST (STRICT PASS/FAIL GATE)")
    print("=" * 75)
    print(f"Repository Root: {REPO_ROOT}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version.split()[0]}")
    print("-" * 75)

    checks = []

    # Tải khóa môi trường
    lock_file = REPO_ROOT / "experiments" / "environment" / "ENVIRONMENT-LOCK.json"
    lock_data = {}
    if lock_file.exists():
        try:
            with open(lock_file, "r", encoding="utf-8") as f:
                lock_data = json.load(f)
        except Exception as e:
            print(f"[WARN] Could not parse ENVIRONMENT-LOCK.json: {e}")

    expected_torch = lock_data.get("runtime_stack", {}).get("pytorch_version", "2.6.0+cu124")
    expected_pyg = lock_data.get("runtime_stack", {}).get("pyg_version", "2.6.1")

    # Kiểm tra 1: CUBLAS_WORKSPACE_CONFIG
    cublas_cfg = os.environ.get("CUBLAS_WORKSPACE_CONFIG", "NOT_SET")
    if cublas_cfg == ":4096:8":
        checks.append(("CUBLAS_WORKSPACE_CONFIG", ":4096:8", cublas_cfg, "PASS"))
    else:
        checks.append(("CUBLAS_WORKSPACE_CONFIG", ":4096:8", cublas_cfg, "FAIL"))

    # Kiểm tra 2: Tính khả dụng của Nhập PyTorch & CUDA
    try:
        import torch
        torch_ver = torch.__version__
        cuda_avail = torch.cuda.is_available()
        cuda_ver = torch.version.cuda
    except Exception as e:
        torch = None
        torch_ver = f"ERROR: {e}"
        cuda_avail = False
        cuda_ver = "NONE"

    # Kiểm tra 2a: CUDA Có sẵn
    if cuda_avail:
        dev_name = torch.cuda.get_device_name(0)
        total_vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
        vram_str = f"{dev_name} ({total_vram_mb:.1f} MB)"
        checks.append(("CUDA Availability", "True", f"True ({vram_str})", "PASS"))
    else:
        checks.append(("CUDA Availability", "True", "False (CUDA unavailable)", "FAIL"))

    # Kiểm tra 3: Phiên bản PyTorch phù hợp
    if torch_ver == expected_torch:
        checks.append(("PyTorch Version", expected_torch, torch_ver, "PASS"))
    else:
        checks.append(("PyTorch Version", expected_torch, torch_ver, "FAIL"))

    # Kiểm tra 4: Hình học PyTorch (PyG)
    try:
        import torch_geometric
        pyg_ver = torch_geometric.__version__
        if pyg_ver == expected_pyg:
            checks.append(("PyG (torch_geometric)", expected_pyg, pyg_ver, "PASS"))
        else:
            checks.append(("PyG (torch_geometric)", expected_pyg, pyg_ver, "FAIL"))
    except ImportError:
        checks.append(("PyG (torch_geometric)", expected_pyg, "NOT_INSTALLED", "FAIL"))
    except Exception as e:
        checks.append(("PyG (torch_geometric)", expected_pyg, f"ERROR: {e}", "FAIL"))

    # Kiểm tra 5: Sự phụ thuộc cốt lõi cho huấn luyện thủ công
    hard_deps = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("scikit-learn", "sklearn"),
        ("psutil", "psutil")
    ]
    for pkg_name, mod_name in hard_deps:
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "INSTALLED")
            checks.append((f"Dep: {pkg_name}", "Installed", ver, "PASS"))
        except ImportError:
            checks.append((f"Dep: {pkg_name}", "Installed", "NOT_INSTALLED", "FAIL"))
        except Exception as e:
            checks.append((f"Dep: {pkg_name}", "Installed", f"ERROR: {e}", "FAIL"))

    # Kiểm tra 5b: DOCUMENT_QA_OPTIONAL (Không chặn / chỉ cung cấp thông tin)
    optional_deps = [
        ("pandas", "pandas"),
        ("python-docx", "docx"),
        ("pypdfium2", "pypdfium2"),
        ("pywin32", "win32api")
    ]
    for pkg_name, mod_name in optional_deps:
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "INSTALLED")
            checks.append((f"Opt: {pkg_name}", "Optional (DocQA)", ver, "OPTIONAL"))
        except ImportError:
            checks.append((f"Opt: {pkg_name}", "Optional (DocQA)", "NOT_INSTALLED", "OPTIONAL"))
        except Exception as e:
            checks.append((f"Opt: {pkg_name}", "Optional (DocQA)", f"ERROR: {e}", "OPTIONAL"))

    # Kiểm tra 6: Truyền Tenx GPU và Nhân ma trận (Nghiêm ngặt 1024x1024)
    if cuda_avail and torch is not None:
        try:
            torch.manual_seed(42)
            a = torch.randn(1024, 1024, dtype=torch.float32)
            b = torch.randn(1024, 1024, dtype=torch.float32)
            c_cpu = torch.matmul(a, b)

            a_gpu = a.to("cuda:0")
            b_gpu = b.to("cuda:0")
            c_gpu = torch.matmul(a_gpu, b_gpu)
            c_from_gpu = c_gpu.to("cpu")

            if torch.allclose(c_cpu, c_from_gpu, atol=1e-3):
                checks.append(("GPU matmul (1024x1024)", "allclose == True", "Verified on cuda:0", "PASS"))
            else:
                checks.append(("GPU matmul (1024x1024)", "allclose == True", "Mismatch detected", "FAIL"))
        except Exception as e:
            checks.append(("GPU matmul (1024x1024)", "allclose == True", f"ERROR: {e}", "FAIL"))
    else:
        checks.append(("GPU matmul (1024x1024)", "allclose == True", "SKIPPED (CUDA unavailable)", "FAIL"))

    # Bảng in
    print(f"{'CHECK ITEM':<26} | {'EXPECTED':<16} | {'OBSERVED':<20} | {'STATUS'}")
    print("-" * 75)
    all_passed = True
    for item, expected, observed, status in checks:
        if status == "FAIL":
            all_passed = False
        # Cắt bớt quan sát nếu quá dài
        obs_display = (observed[:18] + "..") if len(observed) > 20 else observed
        exp_display = (expected[:14] + "..") if len(expected) > 16 else expected
        status_display = f"[{status}]"
        print(f"{item:<26} | {exp_display:<16} | {obs_display:<20} | {status_display}")
    print("-" * 75)

    if all_passed:
        print("=" * 75)
        print("[PASS] GPU Smoke Test Passed 100% (Zero Model Training).")
        print("=" * 75)
        return True
    else:
        failed_count = sum(1 for c in checks if c[3] != "PASS")
        print("=" * 75)
        print(f"[FAIL] GPU Smoke Test FAILED ({failed_count} condition(s) unmet).")
        print("=" * 75)
        return False

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
