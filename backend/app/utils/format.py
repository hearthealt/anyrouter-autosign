"""
格式化工具
"""
from app.config import settings


def format_quota(quota: int) -> str:
    """
    将配额转换为美元显示

    Args:
        quota: 原始配额值

    Returns:
        str: 格式化后的美元字符串
    """
    usd = quota / settings.quota_to_usd_rate

    if usd < 0.01:
        return f"${usd:.4f}"
    elif usd < 1000:
        return f"${usd:.2f}"
    else:
        return f"${usd:,.2f}"


def format_quota_percent(remain_quota: int, total_quota: int) -> str:
    """
    计算剩余额度百分比

    Args:
        remain_quota: 剩余额度
        total_quota: 总额度（剩余+已用）

    Returns:
        str: 格式化后的百分比字符串，如 "10.23%"
    """
    if total_quota <= 0:
        return "0.00%"
    percent = (remain_quota / total_quota) * 100
    return f"{percent:.2f}%"