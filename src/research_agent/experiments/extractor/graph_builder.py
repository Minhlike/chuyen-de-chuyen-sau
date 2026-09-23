# -*- coding: utf-8 -*-
"""
Trình xây dựng đồ thị thực thể - sự kiện nhân quả chuẩn HDFS và Engine hiện thực hóa dữ liệu (Contract V1.2).
Ràng buộc chặt chẽ với SPL-HDFS-001 Canonical Split Authority và ngữ nghĩa thời gian chính xác tới mili giây:
  - Nguồn chân lý duy nhất cho Split Authority: HDFSSplitAuthority
  - Bảo toàn mili giây: parse_hdfs_line_timestamp (UTC epoch + ms / 1000.0)
  - Khóa sắp xếp chuẩn (Canonical Sort Key): (event_timestamp_utc_exact, raw_line_index)
  - Các thực thể có thể trích xuất: DATA_BLOCK (0), STORAGE_NODE (1), MANAGEMENT_SYSTEM (2), EXECUTION_THREAD (3)
  - Các quan hệ có căn cứ thực nghiệm (Grounded Relations):
      1. RECEIVES_BLOCK (dfs.DataNode$DataXceiver)
      2. TRANSMITS_BLOCK (dfs.DataNode$PacketResponder)
      3. ALLOCATES_BLOCK (dfs.FSNamesystem)
      4. MONITORS_BLOCK (dfs.DataNode$PacketResponder)
      5. SERVES_BLOCK (dfs.DataNode$DataXceiver)
      6. UPDATES_BLOCK_MAP (dfs.FSNamesystem)
      7. COMMANDS_REPLICATION (dfs.FSNamesystem)
      8. DELETES_BLOCK (dfs.FSNamesystem / dfs.FSDataset)
  - Mục tiêu nút cố định: x_v_fixed_priv in R^6 (4-dim one-hot type + 2-dim log1p causal in/out degrees)
  - Tường lửa kiểm thử nghiêm ngặt (Strict Test Firewall): TestSetSealedError kích hoạt khi có bất kỳ thao tác hiện thực hóa (materialization) hoặc trích xuất đặc trưng nào trên tập Test.
  - Định luật bảo toàn: eligible_split_records = materialized_graph_records + explicitly_rejected_records
"""

import os
import re
import tarfile
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

from research_agent.experiments.data.hdfs_split_authority import (
    parse_hdfs_line_timestamp,
    HDFSSplitAuthority
)


class TestSetSealedError(Exception):
    """Xảy ra khi bất kỳ mã nào cố gắng truy cập vào phần phân chia Kiểm tra hoặc nhãn kiểm tra đã được niêm phong."""
    __test__ = False


# Quy tắc trích xuất ràng buộc thành phần chính tắc cho HDFS
HDFS_RELATION_RULES = [
    # 1. RECEIVES_BLOCK: StorageNode (đích) -> DataBlock
    {
        "relation_id": 1,
        "relation_name": "RECEIVES_BLOCK",
        "component_regex": re.compile(r"DataNode|DataXceiver", re.IGNORECASE),
        "message_regex": re.compile(r"Receiving block (blk_[-0-9]+) src: (/?[0-9\.:]+) dest: (/?[0-9\.:]+)"),
        "rule_type": "RECEIVES"
    },
    # 2. TRANSMITS_BLOCK: StorageNode (src) -> DataBlock (có kích thước khối)
    {
        "relation_id": 2,
        "relation_name": "TRANSMITS_BLOCK",
        "component_regex": re.compile(r"DataNode|PacketResponder", re.IGNORECASE),
        "message_regex": re.compile(r"Received block (blk_[-0-9]+) of size (\d+) from (/?[0-9\.:]+)"),
        "rule_type": "TRANSMITS"
    },
    # 3. ALLOCATES_BLOCK: FSNamesystem -> DataBlock
    {
        "relation_id": 3,
        "relation_name": "ALLOCATES_BLOCK",
        "component_regex": re.compile(r"FSNamesystem|NameSystem", re.IGNORECASE),
        "message_regex": re.compile(r"BLOCK\* NameSystem\.allocateBlock: (.*)\. (blk_[-0-9]+)"),
        "rule_type": "ALLOCATES"
    },
    # 4. MONITORS_BLOCK: Phản hồi gói -> DataBlock
    {
        "relation_id": 4,
        "relation_name": "MONITORS_BLOCK",
        "component_regex": re.compile(r"DataNode|PacketResponder", re.IGNORECASE),
        "message_regex": re.compile(r"PacketResponder (\d+) for block (blk_[-0-9]+) terminating"),
        "rule_type": "MONITORS"
    },
    # 5. SERVES_BLOCK: StorageNode (máy chủ) -> DataBlock
    {
        "relation_id": 5,
        "relation_name": "SERVES_BLOCK",
        "component_regex": re.compile(r"DataNode|DataXceiver", re.IGNORECASE),
        "message_regex": re.compile(r"(?:([0-9\.:]+) )?Served block (blk_[-0-9]+) to (/?[0-9\.:]+)"),
        "rule_type": "SERVES"
    },
    # 6. UPDATES_BLOCK_MAP: StorageNode -> DataBlock (có kích thước khối)
    {
        "relation_id": 6,
        "relation_name": "UPDATES_BLOCK_MAP",
        "component_regex": re.compile(r"FSNamesystem|NameSystem", re.IGNORECASE),
        "message_regex": re.compile(r"BLOCK\* NameSystem\.addStoredBlock: blockMap updated: ([0-9\.:]+) is added to (blk_[-0-9]+) size (\d+)"),
        "rule_type": "UPDATES_MAP"
    },
    # 7. COMMANDS_REPLICATION: FSNamesystem -> DataBlock
    {
        "relation_id": 7,
        "relation_name": "COMMANDS_REPLICATION",
        "component_regex": re.compile(r"FSNamesystem|NameSystem", re.IGNORECASE),
        "message_regex": re.compile(r"BLOCK\* ask ([0-9\.:]+) to replicate (blk_[-0-9]+) to datanode\(s\) (.*)"),
        "rule_type": "REPLICATES"
    },
    # 8. DELETES_BLOCK: FSNamesystem -> DataBlock
    {
        "relation_id": 8,
        "relation_name": "DELETES_BLOCK",
        "component_regex": re.compile(r"FSNamesystem|FSDataset|DataNode", re.IGNORECASE),
        "message_regex": re.compile(r"(?:BLOCK\* ask ([0-9\.:]+) to delete (blk_[-0-9]+)|Deleting block (blk_[-0-9]+) file (.*))"),
        "rule_type": "DELETES"
    }
]


class HDFSGraphBuilder:
    def __init__(
        self,
        base_dir: Path,
        split_authority: Optional[HDFSSplitAuthority] = None,
        raw_tar_path: Optional[Path] = None,
        max_audit_events: Optional[int] = None
    ):
        self.base_dir = base_dir
        self.raw_tar_path = raw_tar_path or (self.base_dir / "datasets" / "raw" / "hdfs" / "HDFS_1.tar.gz")
        self.split_authority = split_authority or HDFSSplitAuthority(base_dir=self.base_dir, raw_tar_path=self.raw_tar_path)
        self.split_id = "SPL-HDFS-001"
        self.max_audit_events = max_audit_events

        self.node_to_id: Dict[str, int] = {"<UNK_NODE>": 0}
        self.node_to_type: Dict[str, int] = {"<UNK_NODE>": 0}

    def parse_raw_line(self, line_str: str, line_idx: int) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """
        Phân tích một dòng nhật ký HDFS thô thành một sự kiện biểu đồ được nhập bằng cách sử dụng dấu thời gian chính xác đến mili giây
        và trích xuất quan hệ ràng buộc thành phần.
        Trả về (event_dict, reject_reason, block_id).
        """
        parts = line_str.strip().split(" ", 5)
        if len(parts) < 6:
            return None, "MALFORMED_HEADER", None

        d_str, t_str, ms_str, level, comp, msg = parts
        ts_epoch = parse_hdfs_line_timestamp(d_str, t_str, ms_str)
        if ts_epoch is None:
            return None, "TIMESTAMP_PARSE_ERROR", None

        # Trích xuất block_id
        blk_m = re.search(r"(blk_[-0-9]+)", msg)
        if not blk_m:
            return None, "NO_BLOCK_ID_IN_MESSAGE", None
        blk_id = blk_m.group(1)

        # So khớp với các quy tắc quan hệ bị ràng buộc bởi thành phần
        for rule in HDFS_RELATION_RULES:
            if not rule["component_regex"].search(comp):
                continue
            
            m = rule["message_regex"].search(msg)
            if not m:
                continue

            rel_id = rule["relation_id"]
            rel_name = rule["relation_name"]
            rule_type = rule["rule_type"]
            size_bytes = 0.0

            if rule_type == "RECEIVES":
                # StorageNode (đích) -> DataBlock
                dest_storage = m.group(3).lstrip("/")
                src_node = dest_storage
                src_type = 1  # STORAGE_NODE
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            elif rule_type == "TRANSMITS":
                # StorageNode (src) -> DataBlock
                src_storage = m.group(3).lstrip("/")
                size_bytes = float(m.group(2))
                src_node = src_storage
                src_type = 1  # STORAGE_NODE
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            elif rule_type == "ALLOCATES":
                # Hệ thống tên FS -> DataBlock
                src_node = "FSNamesystem"
                src_type = 2  # MANAGEMENT_SYSTEM
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            elif rule_type == "MONITORS":
                # PacketResponder_<ID> -> DataBlock
                thread_id = m.group(1)
                src_node = f"PacketResponder_{thread_id}"
                src_type = 3  # EXECUTION_THREAD
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            elif rule_type == "SERVES":
                # Nút lưu trữ máy chủ -> DataBlock
                server_ip = m.group(1)
                src_node = server_ip.lstrip("/") if server_ip else "10.250.0.1:50010"
                src_type = 1  # STORAGE_NODE
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            elif rule_type == "UPDATES_MAP":
                # Nút lưu trữ -> DataBlock
                storage_ip = m.group(1).lstrip("/")
                size_bytes = float(m.group(3))
                src_node = storage_ip
                src_type = 1  # STORAGE_NODE
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            elif rule_type == "REPLICATES":
                # Hệ thống tên FS -> DataBlock
                src_node = "FSNamesystem"
                src_type = 2  # MANAGEMENT_SYSTEM
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            elif rule_type == "DELETES":
                # Hệ thống tên FS -> DataBlock
                src_node = "FSNamesystem"
                src_type = 2  # MANAGEMENT_SYSTEM
                dest_node = blk_id
                dest_type = 0  # DATA_BLOCK
            else:
                return None, "UNSUPPORTED_RULE_TYPE", blk_id

            event = {
                "raw_line_index": line_idx,
                "event_timestamp_utc_exact": ts_epoch,
                "relation_id": rel_id,
                "relation_name": rel_name,
                "source_node": src_node,
                "source_type": src_type,
                "dest_node": dest_node,
                "dest_type": dest_type,
                "block_id": blk_id,
                "size_bytes": size_bytes
            }
            return event, None, blk_id

        return None, "UNMATCHED_RELATION_TEMPLATE", blk_id

    def materialize_split(self, split_name: str, use_execution_subset: bool = True) -> Dict[str, Any]:
        """
        Cụ thể hóa các sự kiện biểu đồ được ràng buộc chặt chẽ với quyền phân chia SPL-HDFS-001.
        Tăng TestSetSealedError nếu split_name == 'TEST'.
        """
        if split_name.upper() == "TEST":
            raise TestSetSealedError("Attempted to access or materialize sealed Test graph split!")

        split_data = self.split_authority.get_split()
        if split_name.upper() == "TRAIN":
            if use_execution_subset:
                authorized_block_ids: Set[str] = set(split_data["selected_train_block_ids"])
            else:
                authorized_block_ids: Set[str] = set(split_data["train_block_ids"])
        elif split_name.upper() == "VAL":
            if use_execution_subset:
                authorized_block_ids: Set[str] = set(split_data["selected_val_block_ids"])
            else:
                authorized_block_ids: Set[str] = set(split_data["val_block_ids"])
        else:
            raise ValueError(f"Unknown split name: {split_name}")

        events: List[Dict[str, Any]] = []
        rejection_counts: Dict[str, int] = {}
        relation_counts: Dict[str, int] = {}
        eligible_records_count = 0
        total_scanned_lines = 0

        with tarfile.open(self.raw_tar_path, "r:gz") as tar:
            log_member = None
            for m in tar.getmembers():
                if m.name.endswith("HDFS.log") or m.name.endswith(".log"):
                    log_member = m
                    break
            if not log_member:
                raise FileNotFoundError("HDFS.log not found inside archive")

            f_obj = tar.extractfile(log_member)
            line_idx = 0

            for line_bytes in f_obj:
                line_idx += 1
                total_scanned_lines += 1

                line_str = line_bytes.decode("utf-8", errors="ignore").strip()
                event, reject_reason, blk_id = self.parse_raw_line(line_str, line_idx)

                if blk_id is None or blk_id not in authorized_block_ids:
                    # Dòng không thuộc phân vùng phiên khối được ủy quyền
                    continue

                eligible_records_count += 1

                if event is not None:
                    events.append(event)
                    relation_counts[event["relation_name"]] = relation_counts.get(event["relation_name"], 0) + 1
                    if self.max_audit_events and len(events) >= self.max_audit_events:
                        break
                else:
                    rejection_counts[reject_reason] = rejection_counts.get(reject_reason, 0) + 1

        # Phân loại thời gian nhân quả
        events.sort(key=lambda e: (e["event_timestamp_utc_exact"], e["raw_line_index"]))

        # Xây dựng vốn từ vựng nghiêm ngặt trên Train
        if split_name.upper() == "TRAIN":
            for e in events:
                src, s_type = e["source_node"], e["source_type"]
                dst, d_type = e["dest_node"], e["dest_type"]
                if src not in self.node_to_id:
                    self.node_to_id[src] = len(self.node_to_id)
                    self.node_to_type[src] = s_type
                if dst not in self.node_to_id:
                    self.node_to_id[dst] = len(self.node_to_id)
                    self.node_to_type[dst] = d_type

        return {
            "split": split_name.upper(),
            "total_scanned_lines": total_scanned_lines,
            "eligible_records_scanned": eligible_records_count,
            "materialized_events": len(events),
            "total_rejected": sum(rejection_counts.values()),
            "rejection_counts": rejection_counts,
            "relation_counts": relation_counts,
            "events": events
        }
