"""
Cấu hình Pytest cho bộ kiểm thử khoa học
"""

import sys
from pathlib import Path

# Đảm bảo src nằm trong sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
