# -*- coding: utf-8 -*-
"""
Tokenizer, kiểm tra khả năng liên kết và hợp đồng bảo mật có kiểm soát
Xác minh:
  1. Khóa HMAC được mã hóa bằng 0 trong mã token.
  2. Độ phân giải khóa tạm thời và xoay phạm vi phá vỡ khả năng liên kết giữa các phạm vi.
  3. Phân loại nghiêm ngặt RFC1918 và loopback IP (10/8, 172,16/12, 192,168/16, 127/8).
  4. Phân loại thực thể cho IP, đường dẫn, tham số hex.
"""

import pytest
from research_agent.experiments.extractor.tokenizer import PrivacyAwareLogTokenizer

def test_01_zero_hardcoded_keys_and_fingerprint():
    tok1 = PrivacyAwareLogTokenizer(mode="CONTROLLED_LINKABILITY")
    tok2 = PrivacyAwareLogTokenizer(mode="CONTROLLED_LINKABILITY")

    # Khóa tạm thời phải độc lập
    assert tok1.key_fingerprint != tok2.key_fingerprint
    assert len(tok1.key_fingerprint) == 64

def test_02_scope_rotation_breaks_cross_scope_linkage():
    tok = PrivacyAwareLogTokenizer(mode="CONTROLLED_LINKABILITY", active_scope_id="session_A")
    raw_ip = "192.168.1.100"
    
    pseudo_session_a = tok._pseudonymize(raw_ip)

    # Xoay sang session_B với phạm vi mới
    tok.rotate_scope_key("session_B")
    pseudo_session_b = tok._pseudonymize(raw_ip)

    assert pseudo_session_a != pseudo_session_b, "Pseudonyms across rotated scopes must be unlinkable."

def test_03_rfc1918_private_ip_classification():
    tok = PrivacyAwareLogTokenizer(mode="PRIVACY_AWARE_PARAMETERIZED")

    # Các lớp IP riêng
    assert tok._is_private_ip("10.50.100.1") is True
    assert tok._is_private_ip("172.16.0.5") is True
    assert tok._is_private_ip("172.31.255.254") is True
    assert tok._is_private_ip("192.168.1.1") is True
    assert tok._is_private_ip("127.0.0.1") is True  # Quay lại

    # Các lớp IP công cộng
    assert tok._is_private_ip("8.8.8.8") is False
    assert tok._is_private_ip("172.32.0.1") is False  # Bên ngoài /12
    assert tok._is_private_ip("128.55.12.91") is False
    assert tok._is_private_ip("142.250.190.46") is False

def test_04_privacy_aware_tokenization_transformation():
    tok = PrivacyAwareLogTokenizer(mode="PRIVACY_AWARE_PARAMETERIZED")

    line_private = "2026-08-21 10.0.0.5 opened /etc/shadow blk_-9999"
    line_public = "2026-08-21 128.55.12.91 connecting to /tmp/dropper.sh"

    out_private = tok.tokenize_line(line_private)
    out_public = tok.tokenize_line(line_public)

    assert "<IP_INTERNAL:" in out_private
    assert "<PATH_CONFIG>" in out_private
    assert "<BLK:" in out_private

    assert "<IP_EXTERNAL:" in out_public
    assert "<PATH_STAGING>" in out_public
