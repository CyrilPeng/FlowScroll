import hashlib
import base64
import os
import platform


def _get_machine_key() -> bytes:
    """基于机器特征生成加密密钥"""
    # 收集机器特定信息
    info_parts = [
        platform.node(),  # 计算机名
        os.path.expanduser("~"),  # 用户目录
        platform.platform(),  # 平台信息
    ]
    combined = "|".join(info_parts).encode("utf-8")
    # 使用 SHA-256 生成固定长度的密钥
    return hashlib.sha256(combined).digest()


def _xor_encrypt_decrypt(data: bytes, key: bytes) -> bytes:
    """简单的 XOR 加密/解密"""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def encrypt_password(plaintext: str) -> str:
    """
    加密密码字符串

    Args:
        plaintext: 明文密码

    Returns:
        加密后的字符串，格式为 "encrypted:base64_encoded_data"
    """
    if not plaintext:
        return ""

    try:
        key = _get_machine_key()
        data = plaintext.encode("utf-8")
        encrypted = _xor_encrypt_decrypt(data, key)
        # 添加前缀标识已加密
        return "encrypted:" + base64.b64encode(encrypted).decode("ascii")
    except Exception:
        # 加密失败时返回空字符串，而不是明文
        return ""


def decrypt_password(ciphertext: str) -> str:
    """
    解密密码字符串

    Args:
        ciphertext: 加密后的字符串

    Returns:
        解密后的明文密码
    """
    if not ciphertext:
        return ""

    # 检查是否是加密格式
    if not ciphertext.startswith("encrypted:"):
        # 兼容旧版本的明文密码
        return ciphertext

    try:
        key = _get_machine_key()
        encoded_data = ciphertext[len("encrypted:") :]
        encrypted = base64.b64decode(encoded_data)
        decrypted = _xor_encrypt_decrypt(encrypted, key)
        return decrypted.decode("utf-8")
    except Exception:
        # 解密失败时返回空字符串
        return ""


def is_encrypted(value: str) -> bool:
    """检查值是否已加密"""
    return bool(value and value.startswith("encrypted:"))
