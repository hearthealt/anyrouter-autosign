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