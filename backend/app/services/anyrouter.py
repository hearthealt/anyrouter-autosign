"""
AnyRouter API 服务
"""
import re
import json
import time
import logging
from typing import Optional, Tuple, Dict, Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class AntiCrawlerSolver:
    """阿里云盾反爬虫挑战解决器"""

    def __init__(self):
        self.mask = settings.anti_crawler_mask
        self.pos_list = settings.anti_crawler_pos_list

    def solve(self, html_content: str) -> Optional[str]:
        """解决反爬虫挑战"""
        try:
            arg1_match = re.search(r"var arg1='([^']+)'", html_content)
            if not arg1_match:
                return None

            arg1 = arg1_match.group(1)
            arg2 = self._reorder_string(arg1)
            result = self._xor_decrypt(arg2)
            return result
        except Exception as e:
            logger.error(f"解决反爬虫挑战失败: {e}")
            return None

    def _reorder_string(self, input_str: str) -> str:
        """根据位置列表重排序字符串"""
        output_list = [''] * len(self.pos_list)
        for i, char in enumerate(input_str):
            for j, pos in enumerate(self.pos_list):
                if pos == i + 1:
                    output_list[j] = char
                    break
        return ''.join(output_list)

    def _xor_decrypt(self, input_str: str) -> str:
        """XOR 解密"""
        result = ''
        mask = self.mask
        for i in range(0, min(len(input_str), len(mask)), 2):
            if i + 1 < len(input_str) and i + 1 < len(mask):
                str_char = int(input_str[i:i + 2], 16)
                mask_char = int(mask[i:i + 2], 16)
                xor_char = hex(str_char ^ mask_char)[2:].zfill(2)
                result += xor_char
        return result


class AnyRouterService:
    """AnyRouter API 服务"""

    BASE_HEADERS = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-store",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://anyrouter.top/console",
        "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
    }

    def __init__(self):
        self.anti_crawler = AntiCrawlerSolver()
        self.base_url = settings.anyrouter_base_url

    def _get_session(self) -> requests.Session:
        """
        获取新的 Session 实例
        避免在多线程环境下复用 Session 导致的 SSL 连接问题
        """
        session = requests.Session()
        # 配置重试适配器，增强连接稳定性
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _get_headers(self, user_id: str) -> Dict[str, str]:
        """获取请求头，包含 new-api-user"""
        headers = self.BASE_HEADERS.copy()
        headers["new-api-user"] = str(user_id)
        return headers

    def _is_anti_crawler_challenge(self, text: str) -> bool:
        """检查是否为反爬虫挑战"""
        return "acw_sc__v2" in text and "var arg1=" in text

    def _get_cookies_with_challenge(self, session_cookie: str, user_id: str, session: requests.Session = None) -> Dict[str, str]:
        """获取 Cookies 并处理反爬虫挑战"""
        cookies = {"session": session_cookie}
        headers = self._get_headers(user_id)
        if session is None:
            session = self._get_session()

        try:
            response = session.get(
                f"{self.base_url}{settings.anyrouter_console_url}",
                headers=headers,
                cookies=cookies,
                timeout=10
            )

            # 收集返回的 cookies
            for cookie in response.cookies:
                cookies[cookie.name] = cookie.value

            # 检查并解决反爬虫挑战
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)

            return cookies
        except Exception as e:
            logger.error(f"获取 Cookies 失败: {e}")
            return {"session": session_cookie}

    def get_user_info(self, session_cookie: str, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        获取用户信息

        Args:
            session_cookie: Session Cookie
            user_id: 用户 ID (new-api-user)

        Returns:
            Tuple[bool, Dict]: (是否成功, 用户信息或错误消息)
        """
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, session)
        headers = self._get_headers(user_id)

        try:
            url = f"{self.base_url}{settings.anyrouter_user_api}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

            # 如果还是反爬虫挑战，再次处理
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)
                    response = session.get(
                        url,
                        headers=headers,
                        cookies=cookies,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if data.get("success"):
                return True, data.get("data", {})
            else:
                return False, {"message": data.get("message", "获取用户信息失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def sign_in(self, session_cookie: str, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        执行签到

        Args:
            session_cookie: Session Cookie
            user_id: 用户 ID (new-api-user)

        Returns:
            Tuple[bool, Dict]: (是否成功, 签到结果或错误消息)
        """
        for attempt in range(settings.retry_times):
            if attempt > 0:
                time.sleep(settings.retry_interval)

            session = self._get_session()
            cookies = self._get_cookies_with_challenge(session_cookie, user_id, session)
            headers = self._get_headers(user_id)

            try:
                response = session.post(
                    f"{self.base_url}{settings.anyrouter_sign_api}",
                    headers=headers,
                    cookies=cookies,
                    timeout=settings.request_timeout
                )

                # 处理反爬虫挑战
                if self._is_anti_crawler_challenge(response.text):
                    result = self.anti_crawler.solve(response.text)
                    if result:
                        cookies["acw_sc__v2"] = result
                        time.sleep(2)
                        response = session.post(
                            f"{self.base_url}{settings.anyrouter_sign_api}",
                            headers=headers,
                            cookies=cookies,
                            timeout=settings.request_timeout
                        )

                if not response.text.strip():
                    continue

                if self._is_anti_crawler_challenge(response.text):
                    continue

                data = response.json()
                return True, data

            except json.JSONDecodeError:
                continue
            except requests.RequestException as e:
                logger.error(f"签到请求失败: {e}")
                continue
            except Exception as e:
                logger.error(f"签到异常: {e}")
                continue

        return False, {"success": False, "message": "重试次数已用完"}

    def get_tokens(self, session_cookie: str, user_id: str, page: int = 0, size: int = 50) -> Tuple[bool, Dict[str, Any]]:
        """
        获取 API Token 列表

        Args:
            session_cookie: Session Cookie
            user_id: 用户 ID (new-api-user)
            page: 页码
            size: 每页数量

        Returns:
            Tuple[bool, Dict]: (是否成功, Token 列表或错误消息)
        """
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, session)
        headers = self._get_headers(user_id)

        try:
            url = f"{self.base_url}{settings.anyrouter_token_api}?p={page}&size={size}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

            # 处理反爬虫挑战
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)
                    response = session.get(
                        url,
                        headers=headers,
                        cookies=cookies,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if data.get("success"):
                return True, {"tokens": data.get("data", [])}
            else:
                return False, {"message": data.get("message", "获取 Token 列表失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def get_models(self, session_cookie: str, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        获取可用模型列表

        Args:
            session_cookie: Session Cookie
            user_id: 用户 ID (new-api-user)

        Returns:
            Tuple[bool, Dict]: (是否成功, 模型列表或错误消息)
        """
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, session)
        headers = self._get_headers(user_id)

        try:
            url = f"{self.base_url}{settings.anyrouter_models_api}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

            # 处理反爬虫挑战
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)
                    response = session.get(
                        url,
                        headers=headers,
                        cookies=cookies,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if data.get("success"):
                return True, {"models": data.get("data", [])}
            else:
                return False, {"message": data.get("message", "获取模型列表失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def get_groups(self, session_cookie: str, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        获取账号分组列表

        Args:
            session_cookie: Session Cookie
            user_id: 用户 ID (new-api-user)

        Returns:
            Tuple[bool, Dict]: (是否成功, 分组列表或错误消息)
        """
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, session)
        headers = self._get_headers(user_id)

        try:
            url = f"{self.base_url}{settings.anyrouter_groups_api}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

            # 处理反爬虫挑战
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)
                    response = session.get(
                        url,
                        headers=headers,
                        cookies=cookies,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if data.get("success"):
                return True, {"groups": data.get("data", {})}
            else:
                return False, {"message": data.get("message", "获取分组列表失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def _token_request(
        self,
        session_cookie: str,
        user_id: str,
        payload: Dict[str, Any],
        method: str = "post",
        success_msg: str = "操作成功",
        fail_msg: str = "操作失败"
    ) -> Tuple[bool, Dict[str, Any]]:
        """令牌相关请求的通用方法"""
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, session)
        headers = self._get_headers(user_id)
        headers["content-type"] = "application/json"

        try:
            url = f"{self.base_url}{settings.anyrouter_token_api}"
            request_fn = session.post if method == "post" else session.put
            response = request_fn(
                url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=settings.request_timeout
            )

            # 处理反爬虫挑战
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)
                    response = request_fn(
                        url,
                        headers=headers,
                        cookies=cookies,
                        json=payload,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if data.get("success"):
                return True, {"message": data.get("message", success_msg)}
            else:
                return False, {"message": data.get("message", fail_msg)}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def create_token(
        self,
        session_cookie: str,
        user_id: str,
        name: str,
        remain_quota: int = 500000,
        expired_time: int = -1,
        unlimited_quota: bool = False,
        model_limits_enabled: bool = False,
        model_limits: str = "",
        allow_ips: str = "",
        group: str = "default"
    ) -> Tuple[bool, Dict[str, Any]]:
        """创建访问令牌"""
        payload = {
            "name": name,
            "remain_quota": remain_quota,
            "expired_time": expired_time,
            "unlimited_quota": unlimited_quota,
            "model_limits_enabled": model_limits_enabled,
            "model_limits": model_limits,
            "allow_ips": allow_ips,
            "group": group
        }
        return self._token_request(
            session_cookie, user_id, payload,
            method="post", success_msg="创建成功", fail_msg="创建令牌失败"
        )

    def update_token(
        self,
        session_cookie: str,
        user_id: str,
        token_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """更新访问令牌"""
        return self._token_request(
            session_cookie, user_id, token_data,
            method="put", success_msg="更新成功", fail_msg="更新令牌失败"
        )

    def delete_token(self, session_cookie: str, user_id: str, token_id: int) -> Tuple[bool, Dict[str, Any]]:
        """
        删除访问令牌

        Args:
            session_cookie: Session Cookie
            user_id: 用户 ID (new-api-user)
            token_id: 令牌 ID

        Returns:
            Tuple[bool, Dict]: (是否成功, 结果或错误消息)
        """
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, session)
        headers = self._get_headers(user_id)

        try:
            url = f"{self.base_url}{settings.anyrouter_token_api}/{token_id}"
            response = session.delete(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

            # 处理反爬虫挑战
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)
                    response = session.delete(
                        url,
                        headers=headers,
                        cookies=cookies,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if data.get("success"):
                return True, {"message": data.get("message", "删除成功")}
            else:
                return False, {"message": data.get("message", "删除令牌失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def get_api_status(self) -> Tuple[bool, Dict[str, Any]]:
        """
        获取 API 节点状态（公开接口，无需认证）

        Returns:
            Tuple[bool, Dict]: (是否成功, API 状态信息或错误消息)
        """
        session = self._get_session()
        try:
            url = f"{self.base_url}{settings.anyrouter_status_api}"
            response = session.get(
                url,
                headers=self.BASE_HEADERS,
                timeout=settings.request_timeout
            )

            # 处理反爬虫挑战
            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies = {"acw_sc__v2": result}
                    time.sleep(2)
                    response = session.get(
                        url,
                        headers=self.BASE_HEADERS,
                        cookies=cookies,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            return True, data.get("data", {})

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}


# 单例
anyrouter_service = AnyRouterService()
