"""
AnyRouter API 服务
"""
from datetime import datetime
import re
import json
import time
import logging
from typing import Optional, Tuple, Dict, Any

import requests

from app.config import settings, SHANGHAI_TZ
from app.utils.platform import (
    DEFAULT_CHECKIN_API,
    DEFAULT_CONSOLE_URL,
    DEFAULT_GROUPS_API,
    DEFAULT_MODELS_API,
    DEFAULT_SIGN_API,
    DEFAULT_STATUS_API,
    DEFAULT_TOKEN_API,
    DEFAULT_USER_API,
)

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
    """平台签到 API 服务"""

    DEFAULT_LOGIN_API = "/api/user/login"
    DEFAULT_LOGIN_PAGE = "/login?expired=true"

    # 不含 referer 的基础请求头（referer 根据平台动态生成）
    BASE_HEADERS = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-store",
        "pragma": "no-cache",
        "priority": "u=1, i",
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

    @staticmethod
    def _parse_setting_value(raw_value: Any) -> Any:
        """解析设置表中的值。"""
        if raw_value is None:
            return None

        try:
            return json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            return raw_value

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        """尽量将任意值转换为整数。"""
        try:
            if value is None or value == "":
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _extract_reward_from_message(message: str) -> int:
        """从老平台的提示文案中提取美元奖励并换算为 quota。"""
        if not message:
            return 0

        match = re.search(r"\$(\d+(?:\.\d+)?)", message)
        if not match:
            return 0

        try:
            usd_value = float(match.group(1))
            return int(usd_value * settings.quota_to_usd_rate)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _is_already_signed_message(message: str) -> bool:
        """判断提示文案是否表示今日已签到。"""
        normalized_message = (message or "").strip().lower()
        if not normalized_message:
            return False

        return (
            "已签到" in message
            or "已经签到" in message
            or "already signed" in normalized_message
            or "already checked in" in normalized_message
        )

    @staticmethod
    def _normalize_user_info_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """标准化用户信息响应。"""
        data = payload.get("data", {})
        if isinstance(data, dict):
            return data
        return {}

    @classmethod
    def _normalize_sign_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """标准化签到响应。"""
        raw_data = payload.get("data", {})
        if not isinstance(raw_data, dict):
            raw_data = {}

        raw_success = bool(payload.get("success"))
        raw_message = payload.get("message", "")
        already_signed = cls._is_already_signed_message(raw_message) or (raw_success and not raw_message)
        reward_quota = cls._safe_int(raw_data.get("quota_awarded"), 0)
        if reward_quota <= 0:
            reward_quota = cls._extract_reward_from_message(raw_message)

        checkin_date = raw_data.get("checkin_date")
        if not checkin_date:
            checkin_date = datetime.now(SHANGHAI_TZ).strftime("%Y-%m-%d")

        message = raw_message or ("今日已签到" if already_signed else "签到成功" if raw_success else "签到失败")

        return {
            "success": raw_success or already_signed,
            "message": message,
            "reward_quota": reward_quota,
            "already_signed": already_signed,
            "checkin_date": checkin_date,
            "raw": payload,
        }

    @classmethod
    def _normalize_checkin_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """标准化签到记录响应。"""
        raw_data = payload.get("data", {})
        if not isinstance(raw_data, dict):
            raw_data = {}

        stats = raw_data.get("stats", {})
        if not isinstance(stats, dict):
            stats = {}

        raw_records = stats.get("records", [])
        records = []
        if isinstance(raw_records, list):
            for item in raw_records:
                if not isinstance(item, dict):
                    continue
                checkin_date = item.get("checkin_date")
                if not checkin_date:
                    continue
                records.append({
                    "checkin_date": str(checkin_date),
                    "quota_awarded": cls._safe_int(item.get("quota_awarded"), 0),
                })

        return {
            "enabled": bool(raw_data.get("enabled")),
            "min_quota": cls._safe_int(raw_data.get("min_quota"), 0),
            "max_quota": cls._safe_int(raw_data.get("max_quota"), 0),
            "checked_in_today": bool(stats.get("checked_in_today")),
            "checkin_count": cls._safe_int(stats.get("checkin_count"), 0),
            "records": records,
            "total_checkins": cls._safe_int(stats.get("total_checkins"), 0),
            "total_quota": cls._safe_int(stats.get("total_quota"), 0),
            "raw": payload,
        }

    @staticmethod
    def _normalize_token_list_payload(payload: Dict[str, Any]) -> list[Dict[str, Any]]:
        """兼容 data 为数组或分页对象的 token 列表。"""
        raw_data = payload.get("data", [])
        if isinstance(raw_data, list):
            return [item for item in raw_data if isinstance(item, dict)]
        if isinstance(raw_data, dict):
            items = raw_data.get("items", [])
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        return []

    @staticmethod
    def _normalize_models_payload(payload: Dict[str, Any]) -> list[Any]:
        """标准化模型列表响应。"""
        data = payload.get("data", [])
        return data if isinstance(data, list) else []

    @staticmethod
    def _normalize_groups_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """标准化分组响应。"""
        data = payload.get("data", {})
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _normalize_status_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """兼容 data 为对象或数组的状态接口响应。"""
        data = payload.get("data", {})
        if isinstance(data, dict):
            api_info = data.get("api_info", [])
            if not isinstance(api_info, list):
                api_info = []
            return {
                **data,
                "api_info": api_info,
            }
        if isinstance(data, list):
            return {"api_info": data}
        return {"api_info": []}

    @staticmethod
    def _find_checkin_reward(records: list[Dict[str, Any]], target_date: str) -> Optional[int]:
        """从月度签到记录中提取指定日期的奖励额度。"""
        for record in records:
            if record.get("checkin_date") == target_date:
                return AnyRouterService._safe_int(record.get("quota_awarded"), 0)
        return None

    def _get_proxy_config(self) -> Dict[str, str]:
        """读取出站代理配置。"""
        proxy_enabled = settings.anyrouter_proxy_enabled
        proxy_url = (settings.anyrouter_proxy_url or "").strip()
        db = None

        try:
            from app.database import SessionLocal
            from app.models.setting import Setting

            db = SessionLocal()
            proxy_settings = db.query(Setting).filter(
                Setting.key.in_([
                    "anyrouter_proxy_enabled",
                    "anyrouter_proxy_url",
                    "anrouter_proxy_enabled",
                    "anrouter_proxy_url",
                ])
            ).all()
            parsed_settings = {
                item.key: self._parse_setting_value(item.value)
                for item in proxy_settings
            }

            if "anyrouter_proxy_enabled" in parsed_settings:
                proxy_enabled = bool(parsed_settings["anyrouter_proxy_enabled"])
            elif "anrouter_proxy_enabled" in parsed_settings:
                proxy_enabled = bool(parsed_settings["anrouter_proxy_enabled"])

            if parsed_settings.get("anyrouter_proxy_url") is not None:
                proxy_url = str(parsed_settings["anyrouter_proxy_url"]).strip()
            elif parsed_settings.get("anrouter_proxy_url") is not None:
                proxy_url = str(parsed_settings["anrouter_proxy_url"]).strip()
        except Exception as e:
            logger.debug(f"加载代理配置失败，继续使用默认配置: {e}")
        finally:
            if db is not None:
                db.close()

        if not proxy_enabled or not proxy_url:
            return {}

        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def _get_session(self) -> requests.Session:
        """
        获取新的 Session 实例
        避免在多线程环境下复用 Session 导致的 SSL 连接问题
        """
        session = requests.Session()
        session.trust_env = False
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
        proxy_config = self._get_proxy_config()
        if proxy_config:
            session.proxies.update(proxy_config)
        return session

    def _get_headers(self, user_id: str, base_url: str, console_url: str = None) -> Dict[str, str]:
        """获取请求头，包含 new-api-user 和动态 referer"""
        if console_url is None:
            console_url = DEFAULT_CONSOLE_URL
        headers = self.BASE_HEADERS.copy()
        headers["new-api-user"] = str(user_id)
        headers["referer"] = f"{base_url}{console_url}"
        return headers

    def _get_base_headers(self, base_url: str, console_url: str = None) -> Dict[str, str]:
        """获取基础请求头（无认证，用于公开接口）"""
        if console_url is None:
            console_url = DEFAULT_CONSOLE_URL
        headers = self.BASE_HEADERS.copy()
        headers["referer"] = f"{base_url}{console_url}"
        return headers

    @staticmethod
    def _extract_session_cookie(response: requests.Response, session: requests.Session) -> Optional[str]:
        """从响应或 Session 中提取 session cookie。"""
        if response.cookies.get("session"):
            return response.cookies.get("session")
        if session.cookies.get("session"):
            return session.cookies.get("session")
        return None

    def _is_anti_crawler_challenge(self, text: str) -> bool:
        """检查是否为反爬虫挑战"""
        return "acw_sc__v2" in text and "var arg1=" in text

    def _get_cookies_with_challenge(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        console_url: str = None,
        session: requests.Session = None
    ) -> Dict[str, str]:
        """获取 Cookies 并处理反爬虫挑战"""
        if console_url is None:
            console_url = DEFAULT_CONSOLE_URL
        cookies = {"session": session_cookie}
        headers = self._get_headers(user_id, base_url, console_url)
        if session is None:
            session = self._get_session()

        try:
            response = session.get(
                f"{base_url}{console_url}",
                headers=headers,
                cookies=cookies,
                timeout=10
            )

            for cookie in response.cookies:
                cookies[cookie.name] = cookie.value

            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)

            return cookies
        except Exception as e:
            logger.error(f"获取 Cookies 失败: {e}")
            return {"session": session_cookie}

    def login(
        self,
        base_url: str,
        username: str,
        password: str,
        login_api: str = None,
        login_page: str = None,
        turnstile: str = "",
    ) -> Tuple[bool, Dict[str, Any]]:
        """使用账号密码登录并提取新的 session cookie。"""
        if login_api is None:
            login_api = self.DEFAULT_LOGIN_API
        if login_page is None:
            login_page = self.DEFAULT_LOGIN_PAGE

        session = self._get_session()
        page_headers = self._get_base_headers(base_url, login_page)
        login_headers = self._get_base_headers(base_url, login_page)
        login_headers["content-type"] = "application/json"
        login_headers["origin"] = base_url

        cookies: Dict[str, str] = {}

        try:
            page_response = session.get(
                f"{base_url}{login_page}",
                headers=page_headers,
                timeout=settings.request_timeout
            )

            for cookie in page_response.cookies:
                cookies[cookie.name] = cookie.value

            if self._is_anti_crawler_challenge(page_response.text):
                result = self.anti_crawler.solve(page_response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)

            response = session.post(
                f"{base_url}{login_api}",
                headers=login_headers,
                cookies=cookies,
                params={"turnstile": turnstile},
                json={"username": username, "password": password},
                timeout=settings.request_timeout
            )

            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies["acw_sc__v2"] = result
                    time.sleep(2)
                    response = session.post(
                        f"{base_url}{login_api}",
                        headers=login_headers,
                        cookies=cookies,
                        params={"turnstile": turnstile},
                        json={"username": username, "password": password},
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if not data.get("success"):
                return False, {"message": data.get("message", "登录失败")}

            session_cookie = self._extract_session_cookie(response, session)
            if not session_cookie:
                return False, {"message": "登录成功，但响应中未返回 session Cookie"}

            user_info = data.get("data") if isinstance(data.get("data"), dict) else {}
            user_id_value = user_info.get("id")
            user_id_str = str(user_id_value) if user_id_value is not None else None

            return True, {
                "message": data.get("message", "登录成功"),
                "session_cookie": session_cookie,
                "user_id": user_id_str,
                "username": user_info.get("username"),
                "display_name": user_info.get("display_name"),
                "raw": data,
            }

        except json.JSONDecodeError:
            return False, {"message": "登录响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"登录请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"登录异常: {str(e)}"}

    def get_user_info(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        user_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取用户信息
        """
        if user_api is None:
            user_api = DEFAULT_USER_API
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
        headers = self._get_headers(user_id, base_url, console_url)

        try:
            url = f"{base_url}{user_api}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

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
                return True, self._normalize_user_info_payload(data)
            else:
                return False, {"message": data.get("message", "获取用户信息失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def get_checkin_records(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        month: str,
        checkin_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """获取指定月份的签到记录。"""
        if checkin_api is None:
            checkin_api = DEFAULT_CHECKIN_API
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
        headers = self._get_headers(user_id, base_url, console_url)

        try:
            url = f"{base_url}{checkin_api}?month={month}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

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
                return True, self._normalize_checkin_payload(data)
            return False, {"message": data.get("message", "获取签到记录失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def sign_in(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        sign_api: str = None,
        checkin_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        执行签到
        """
        if sign_api is None:
            sign_api = DEFAULT_SIGN_API
        if checkin_api is None:
            checkin_api = DEFAULT_CHECKIN_API
        for attempt in range(settings.retry_times):
            if attempt > 0:
                time.sleep(settings.retry_interval)

            session = self._get_session()
            cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
            headers = self._get_headers(user_id, base_url, console_url)

            try:
                response = session.post(
                    f"{base_url}{sign_api}",
                    headers=headers,
                    cookies=cookies,
                    timeout=settings.request_timeout
                )

                if self._is_anti_crawler_challenge(response.text):
                    result = self.anti_crawler.solve(response.text)
                    if result:
                        cookies["acw_sc__v2"] = result
                        time.sleep(2)
                        response = session.post(
                            f"{base_url}{sign_api}",
                            headers=headers,
                            cookies=cookies,
                            timeout=settings.request_timeout
                        )

                if not response.text.strip():
                    continue

                if self._is_anti_crawler_challenge(response.text):
                    continue

                data = response.json()
                result = self._normalize_sign_payload(data)
                raw_sign_data = data.get("data", {})
                should_fetch_checkin_reward = isinstance(raw_sign_data, dict) and bool(raw_sign_data.get("checkin_date"))

                if (
                    should_fetch_checkin_reward
                    and result["success"]
                    and not result["already_signed"]
                    and result["reward_quota"] <= 0
                ):
                    target_date = result["checkin_date"]
                    target_month = target_date[:7]
                    for reward_attempt in range(3):
                        checkin_success, checkin_result = self.get_checkin_records(
                            session_cookie=session_cookie,
                            user_id=user_id,
                            base_url=base_url,
                            month=target_month,
                            checkin_api=checkin_api,
                            console_url=console_url
                        )
                        if checkin_success:
                            reward_quota = self._find_checkin_reward(
                                checkin_result.get("records", []),
                                target_date
                            )
                            if reward_quota is not None:
                                result["reward_quota"] = reward_quota
                                break
                        if reward_attempt < 2:
                            time.sleep(1)

                return True, result

            except json.JSONDecodeError:
                continue
            except requests.RequestException as e:
                logger.error(f"签到请求失败: {e}")
                continue
            except Exception as e:
                logger.error(f"签到异常: {e}")
                continue

        return False, {"success": False, "message": "重试次数已用完"}

    def get_tokens(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        token_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取 API Token 列表
        """
        if token_api is None:
            token_api = DEFAULT_TOKEN_API
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
        headers = self._get_headers(user_id, base_url, console_url)

        try:
            url = f"{base_url}{token_api}?p=0&size=50"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

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
                return True, {"tokens": self._normalize_token_list_payload(data)}
            else:
                return False, {"message": data.get("message", "获取 Token 列表失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def get_models(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        models_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取可用模型列表
        """
        if models_api is None:
            models_api = DEFAULT_MODELS_API
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
        headers = self._get_headers(user_id, base_url, console_url)

        try:
            url = f"{base_url}{models_api}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

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
                return True, {"models": self._normalize_models_payload(data)}
            else:
                return False, {"message": data.get("message", "获取模型列表失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}

    def get_groups(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        groups_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取账号分组列表
        """
        if groups_api is None:
            groups_api = DEFAULT_GROUPS_API
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
        headers = self._get_headers(user_id, base_url, console_url)

        try:
            url = f"{base_url}{groups_api}"
            response = session.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

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
                return True, {"groups": self._normalize_groups_payload(data)}
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
        base_url: str,
        payload: Dict[str, Any],
        token_api: str = None,
        console_url: str = None,
        method: str = "post",
        success_msg: str = "操作成功",
        fail_msg: str = "操作失败"
    ) -> Tuple[bool, Dict[str, Any]]:
        """令牌相关请求的通用方法"""
        if token_api is None:
            token_api = DEFAULT_TOKEN_API
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
        headers = self._get_headers(user_id, base_url, console_url)
        headers["content-type"] = "application/json"

        try:
            url = f"{base_url}{token_api}"
            request_fn = session.post if method == "post" else session.put
            response = request_fn(
                url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=settings.request_timeout
            )

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
        base_url: str,
        name: str,
        remain_quota: int = 500000,
        expired_time: int = -1,
        unlimited_quota: bool = False,
        model_limits_enabled: bool = False,
        model_limits: str = "",
        allow_ips: str = "",
        group: str = "default",
        token_api: str = None,
        console_url: str = None
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
            session_cookie, user_id, base_url, payload,
            token_api=token_api,
            console_url=console_url,
            method="post", success_msg="创建成功", fail_msg="创建令牌失败"
        )

    def update_token(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        token_data: Dict[str, Any],
        token_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """更新访问令牌"""
        return self._token_request(
            session_cookie, user_id, base_url, token_data,
            token_api=token_api,
            console_url=console_url,
            method="put", success_msg="更新成功", fail_msg="更新令牌失败"
        )

    def delete_token(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        token_id: int,
        token_api: str = None,
        console_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        删除访问令牌
        """
        if token_api is None:
            token_api = DEFAULT_TOKEN_API
        session = self._get_session()
        cookies = self._get_cookies_with_challenge(session_cookie, user_id, base_url, console_url)
        headers = self._get_headers(user_id, base_url, console_url)

        try:
            url = f"{base_url}{token_api}/{token_id}"
            response = session.delete(
                url,
                headers=headers,
                cookies=cookies,
                timeout=settings.request_timeout
            )

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

    def get_api_status(self, base_url: str, status_api: str = None, console_url: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        获取 API 节点状态（公开接口，无需认证）
        """
        if status_api is None:
            status_api = DEFAULT_STATUS_API
        session = self._get_session()
        try:
            url = f"{base_url}{status_api}"
            headers = self._get_base_headers(base_url, console_url)
            response = session.get(
                url,
                headers=headers,
                timeout=settings.request_timeout
            )

            if self._is_anti_crawler_challenge(response.text):
                result = self.anti_crawler.solve(response.text)
                if result:
                    cookies = {"acw_sc__v2": result}
                    time.sleep(2)
                    response = session.get(
                        url,
                        headers=headers,
                        cookies=cookies,
                        timeout=settings.request_timeout
                    )

            data = response.json()
            if data.get("success"):
                return True, self._normalize_status_payload(data)
            return False, {"message": data.get("message", "获取状态信息失败")}

        except json.JSONDecodeError:
            return False, {"message": "响应解析失败"}
        except requests.RequestException as e:
            return False, {"message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return False, {"message": f"未知错误: {str(e)}"}


# 单例
anrouter_service = AnyRouterService()
