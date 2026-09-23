# -*- coding: utf-8 -*-
"""
Cơ quan phân chia HDFS Canonical (Mô-đun chia sẻ SPL-HDFS-001).
Cung cấp khả năng trích xuất khoảng thời gian phiên một nguồn tin cậy, ranh giới phân vùng nguyên nhân,
các xác nhận rời rạc và phân tích cú pháp dấu thời gian chính xác đến từng mili giây cho nhật ký HDFS.
Được chia sẻ trên HDFSRealDataAdapter và HDFSGraphBuilder để ngăn chặn tình trạng lệch logic phân tách.
"""

import re
import json
import tarfile
import calendar
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set


def parse_hdfs_line_timestamp(date_str: str, time_str: str, ms_str: str) -> Optional[float]:
    """
    Chuyển đổi epoch số UTC nhanh chóng, mang tính xác định, đảm bảo độ chính xác đến từng mili giây.
    Công thức: UTC giây epoch + (ms/1000.0)
    """
    try:
        year = 2000 + int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        sec = int(time_str[4:6])
        ms = int(ms_str)
        base_epoch = calendar.timegm((year, month, day, hour, minute, sec, 0, 0, 0))
        return float(base_epoch) + (float(ms) / 1000.0)
    except Exception:
        return None


class HDFSSplitAuthority:
    """
    Cơ quan phân vùng nhân quả nguồn tin cậy duy nhất cho SPL-HDFS-001.
    """
    def __init__(
        self,
        base_dir: Path,
        raw_tar_path: Optional[Path] = None,
        max_train_sessions: int = 35000,
        max_val_sessions: int = 7500,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15
    ):
        self.base_dir = base_dir
        self.raw_tar_path = raw_tar_path or (self.base_dir / "datasets" / "raw" / "hdfs" / "HDFS_1.tar.gz")
        self.cache_dir = self.base_dir / "experiments" / "runs" / "data" / "hdfs"
        self.cache_path = self.cache_dir / "hdfs_split_authority_cache.json"
        
        self.max_train_sessions = max_train_sessions
        self.max_val_sessions = max_val_sessions
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio

        self._split_data: Optional[Dict[str, Any]] = None

    def get_split(self) -> Dict[str, Any]:
        """Tải siêu dữ liệu về quyền phân chia được lưu trong bộ nhớ đệm hoặc tính toán từ tarball thô."""
        if self._split_data is not None:
            return self._split_data

        if self.cache_path.exists():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                # Chuyển đổi danh sách trở lại bộ để kiểm tra thành viên
                data["train_block_ids"] = set(data["train_block_ids"])
                data["val_block_ids"] = set(data["val_block_ids"])
                data["test_block_ids"] = set(data["test_block_ids"])
                data["purged_train_val_ids"] = set(data["purged_train_val_ids"])
                data["purged_val_test_ids"] = set(data["purged_val_test_ids"])
                self._split_data = data
                return self._split_data
            except Exception:
                pass

        return self.compute_and_cache_split()

    def compute_and_cache_split(self) -> Dict[str, Any]:
        """Tính toán các khoảng thời gian phiên chính xác trên toàn bộ 11,17 triệu dòng thô và thực thi việc xóa ranh giới."""
        if not self.raw_tar_path.exists():
            raise FileNotFoundError(f"Raw HDFS tarball missing at {self.raw_tar_path}")

        session_intervals: Dict[str, Tuple[float, float, int]] = {}
        raw_total_lines = 0
        block_associated_events = 0
        malformed_lines = 0

        with tarfile.open(self.raw_tar_path, "r:gz") as tar:
            log_member = None
            for m in tar.getmembers():
                if m.name.endswith("HDFS.log") or m.name.endswith(".log"):
                    log_member = m
                    break
            if not log_member:
                raise FileNotFoundError("HDFS.log not found inside archive")

            f_obj = tar.extractfile(log_member)
            for line_bytes in f_obj:
                raw_total_lines += 1
                try:
                    line_str = line_bytes.decode("utf-8", errors="ignore").strip()
                    parts = line_str.split(" ", 5)
                    if len(parts) < 6:
                        malformed_lines += 1
                        continue
                    d_str, t_str, ms_str, level, component, content = parts
                    ts = parse_hdfs_line_timestamp(d_str, t_str, ms_str)
                    if ts is None:
                        malformed_lines += 1
                        continue

                    blk_m = re.search(r"(blk_[-0-9]+)", content)
                    if not blk_m:
                        continue
                    blk_id = blk_m.group(1)
                    block_associated_events += 1

                    if blk_id not in session_intervals:
                        session_intervals[blk_id] = (ts, ts, 1)
                    else:
                        s_ts, e_ts, cnt = session_intervals[blk_id]
                        session_intervals[blk_id] = (min(s_ts, ts), max(e_ts, ts), cnt + 1)
                except Exception:
                    malformed_lines += 1

        # Phân loại nhân quả
        sorted_sessions = sorted(
            session_intervals.keys(),
            key=lambda b: (session_intervals[b][0], b)
        )
        total_unique_sessions = len(sorted_sessions)
        
        train_idx_end = int(total_unique_sessions * self.train_ratio)
        val_idx_end = int(total_unique_sessions * (self.train_ratio + self.val_ratio))

        raw_train_ids = set(sorted_sessions[:train_idx_end])
        raw_val_ids = set(sorted_sessions[train_idx_end:val_idx_end])
        raw_test_ids = set(sorted_sessions[val_idx_end:])

        train_start_cutoff = min(session_intervals[b][0] for b in raw_train_ids)
        val_start_cutoff = min(session_intervals[b][0] for b in raw_val_ids)
        test_start_cutoff = min(session_intervals[b][0] for b in raw_test_ids)

        train_block_ids: Set[str] = set()
        val_block_ids: Set[str] = set()
        test_block_ids: Set[str] = set()
        purged_train_val_ids: Set[str] = set()
        purged_val_test_ids: Set[str] = set()

        for blk_id in sorted_sessions:
            start_ts, end_ts, _ = session_intervals[blk_id]
            if start_ts < val_start_cutoff:
                if end_ts < val_start_cutoff:
                    train_block_ids.add(blk_id)
                else:
                    purged_train_val_ids.add(blk_id)
            elif start_ts < test_start_cutoff:
                if end_ts < test_start_cutoff:
                    val_block_ids.add(blk_id)
                else:
                    purged_val_test_ids.add(blk_id)
            else:
                test_block_ids.add(blk_id)

        train_min_start = min(session_intervals[b][0] for b in train_block_ids) if train_block_ids else 0.0
        train_max_end = max(session_intervals[b][1] for b in train_block_ids) if train_block_ids else 0.0
        val_min_start = min(session_intervals[b][0] for b in val_block_ids) if val_block_ids else 0.0
        val_max_end = max(session_intervals[b][1] for b in val_block_ids) if val_block_ids else 0.0
        test_min_start = min(session_intervals[b][0] for b in test_block_ids) if test_block_ids else 0.0
        test_max_end = max(session_intervals[b][1] for b in test_block_ids) if test_block_ids else 0.0

        # Kiểm tra bất biến
        assert train_max_end < val_min_start, "Train-Val boundary causal violation!"
        assert val_max_end < test_min_start, "Val-Test boundary causal violation!"
        assert train_block_ids.isdisjoint(val_block_ids), "Train and Val block IDs overlap!"
        assert train_block_ids.isdisjoint(test_block_ids), "Train and Test block IDs overlap!"
        assert val_block_ids.isdisjoint(test_block_ids), "Val and Test block IDs overlap!"
        assert purged_train_val_ids.isdisjoint(train_block_ids), "Purged sessions leaked into Train!"
        assert purged_val_test_ids.isdisjoint(val_block_ids), "Purged sessions leaked into Val!"

        # Lựa chọn ngân sách nhân quả (35.000 phiên Train sớm nhất, 7.500 phiên Val sớm nhất)
        selected_train_block_ids = sorted(
            train_block_ids,
            key=lambda b: (session_intervals[b][0], b)
        )[:self.max_train_sessions]

        selected_val_block_ids = sorted(
            val_block_ids,
            key=lambda b: (session_intervals[b][0], b)
        )[:self.max_val_sessions]

        selected_train_sha256 = hashlib.sha256("\n".join(selected_train_block_ids).encode()).hexdigest()
        selected_val_sha256 = hashlib.sha256("\n".join(selected_val_block_ids).encode()).hexdigest()
        population_train_sha256 = hashlib.sha256("\n".join(sorted(list(train_block_ids))).encode()).hexdigest()
        population_val_sha256 = hashlib.sha256("\n".join(sorted(list(val_block_ids))).encode()).hexdigest()

        split_dict = {
            "split_id": "SPL-HDFS-001",
            "raw_total_lines": raw_total_lines,
            "block_associated_events": block_associated_events,
            "malformed_lines": malformed_lines,
            "total_unique_sessions": total_unique_sessions,
            "train_session_count": len(train_block_ids),
            "val_session_count": len(val_block_ids),
            "test_session_count": len(test_block_ids),
            "purged_train_val_count": len(purged_train_val_ids),
            "purged_val_test_count": len(purged_val_test_ids),
            "authorized_train_session_count": len(selected_train_block_ids),
            "authorized_val_session_count": len(selected_val_block_ids),
            "train_min_start": train_min_start,
            "train_max_end": train_max_end,
            "val_min_start": val_min_start,
            "val_max_end": val_max_end,
            "test_min_start": test_min_start,
            "test_max_end": test_max_end,
            "selected_train_block_ids_sha256": selected_train_sha256,
            "selected_val_block_ids_sha256": selected_val_sha256,
            "population_train_block_ids_sha256": population_train_sha256,
            "population_val_block_ids_sha256": population_val_sha256,
            "train_block_ids": train_block_ids,
            "val_block_ids": val_block_ids,
            "test_block_ids": test_block_ids,
            "purged_train_val_ids": purged_train_val_ids,
            "purged_val_test_ids": purged_val_test_ids,
            "selected_train_block_ids": selected_train_block_ids,
            "selected_val_block_ids": selected_val_block_ids
        }

        # Bộ đệm có thể tuần tự hóa JSON
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        serializable = dict(split_dict)
        serializable["train_block_ids"] = sorted(list(train_block_ids))
        serializable["val_block_ids"] = sorted(list(val_block_ids))
        serializable["test_block_ids"] = sorted(list(test_block_ids))
        serializable["purged_train_val_ids"] = sorted(list(purged_train_val_ids))
        serializable["purged_val_test_ids"] = sorted(list(purged_val_test_ids))
        
        self.cache_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        self._split_data = split_dict
        return self._split_data
