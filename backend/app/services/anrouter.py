"""
AnyRouter API 服务
"""
from datetime import datetime
import base64
import hashlib
import re
import json
import time
import logging
import uuid
from io import BytesIO
from threading import RLock
from typing import Optional, Tuple, Dict, Any, Iterable, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def _mask_log_value(value: Any, keep: int = 4) -> str:
    text = str(value or "")
    if not text:
        return ""
    if len(text) <= keep * 2:
        return "*" * len(text)
    return f"{text[:keep]}...{text[-keep:]}"


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
    GAME_INTEGRITY_PROTECTED_PATHS = (
        "/slot/",
        "/pet/",
        "/stock/",
        "/market/",
        "/checkin",
        "/aff_transfer",
        "/topup",
        "/pay",
        "/amount",
        "/stripe/",
        "/creem/",
        "/daily-tasks/claim",
        "/quota-grants/claim",
        "/quota-tickets",
        "/resource-security/",
        "/playbook/",
        "/membership/",
        "/tower-defense",
    )

    def __init__(self):
        self.anti_crawler = AntiCrawlerSolver()
        self._captcha_ocr = None
        self._captcha_ocr_lock = RLock()

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
    def _requires_captcha_message(message: str) -> bool:
        """判断响应文案是否表示签到需要验证码。"""
        normalized_message = (message or "").strip().lower()
        if not normalized_message:
            return False

        captcha_keywords = (
            "captcha",
            "verification code",
            "verify code",
            "验证码",
            "验证失败",
            "请完成验证",
            "请先验证",
            "答案错误",
        )
        return any(keyword in normalized_message for keyword in captcha_keywords)

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
        already_signed = cls._is_already_signed_message(raw_message)
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
            "checkin_nonce": str(raw_data.get("checkin_nonce") or ""),
            "nonce_date": str(raw_data.get("nonce_date") or ""),
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

    @staticmethod
    def _should_sign_checkin_request(sign_api: str, checkin_api: str) -> bool:
        """判断当前签到接口是否使用 New API 的 checkin 签名机制。"""
        normalized_sign_api = (sign_api or "").split("?", 1)[0].rstrip("/")
        normalized_checkin_api = (checkin_api or "").split("?", 1)[0].rstrip("/")
        return (
            normalized_sign_api == normalized_checkin_api
            and normalized_sign_api.endswith("/api/user/checkin")
        )

    @staticmethod
    def _build_checkin_signature_headers(user_id: str, checkin_nonce: str) -> Dict[str, str]:
        """生成 New API checkin 签名请求头。"""
        timestamp = str(int(time.time()))
        signature_source = f"{user_id}:{timestamp}:{checkin_nonce}"
        signature = hashlib.sha256(signature_source.encode("utf-8")).hexdigest()
        return {
            "X-Checkin-Timestamp": timestamp,
            "X-Checkin-Signature": signature,
        }

    @staticmethod
    def _append_query_param(url: str, key: str, value: str) -> str:
        """在 URL 上追加查询参数，自动处理已有 query。"""
        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query.append((key, value))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    @staticmethod
    def _solve_pow_challenge(challenge: str, difficulty: int) -> Dict[str, Any]:
        """求解 New API PoW challenge：sha256(challenge + nonce) 前缀匹配 difficulty 个 0。"""
        target = "0" * max(0, difficulty)
        nonce = 0
        started_at = time.perf_counter()
        max_attempts = max(100000, int((16 ** max(0, difficulty)) * 3))

        while nonce <= max_attempts:
            digest = hashlib.sha256(f"{challenge}{nonce}".encode("utf-8")).hexdigest()
            if digest.startswith(target):
                return {
                    "nonce": nonce,
                    "hash": digest,
                    "time": round(time.perf_counter() - started_at, 2),
                }
            nonce += 1

        raise ValueError("POW challenge 求解超时")

    @staticmethod
    def _build_pow_token(challenge: str, pow_result: Dict[str, Any]) -> str:
        """按前端 POWCaptcha token 格式构造 pow_token。"""
        payload = {
            "challenge": challenge,
            "pow": pow_result,
            "fingerprint": {"canvas": 0, "webgl": 0},
            "behavior": {"score": 80, "moves": 12, "dist": 360},
            "automation": [],
            "risk": 0,
            "ts": int(time.time() * 1000),
        }
        token_json = json.dumps(payload, separators=(",", ":"))
        return base64.b64encode(token_json.encode("utf-8")).decode("ascii")

    @classmethod
    def _requires_game_integrity_headers(cls, method: str, url: str) -> bool:
        """判断请求是否命中 New API 前端的游戏/奖励动作完整性拦截器。"""
        if (method or "").upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
            return False
        normalized_url = (url or "").lower()
        return any(path in normalized_url for path in cls.GAME_INTEGRITY_PROTECTED_PATHS)

    @staticmethod
    def _compact_json_bytes(value: Any) -> bytes:
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _coerce_body_bytes(value: Any) -> bytes:
        if value is None:
            return b""
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        return str(value).encode("utf-8")

    @classmethod
    def _build_game_integrity_headers(
        cls,
        body_bytes: bytes,
        session_id: Optional[str] = None,
        seq: int = 1,
    ) -> Dict[str, str]:
        """生成 New API 前端拦截器添加的游戏动作完整性请求头。"""
        user_agent = cls.BASE_HEADERS.get("user-agent", "")
        fingerprint_source = "|".join([user_agent, "zh-CN", "Win32", "Asia/Shanghai", "8", "8"])
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
        return {
            "X-Game-Action-Id": str(uuid.uuid4()),
            "X-Game-Client-Ts": str(int(time.time() * 1000)),
            "X-Game-Session-Id": session_id or str(uuid.uuid4()),
            "X-Game-Client-Seq": str(max(1, seq)),
            "X-Game-Client-Fingerprint": fingerprint,
            "X-Game-Body-SHA256": hashlib.sha256(body_bytes).hexdigest(),
        }

    @classmethod
    def _prepare_game_integrity_request(
        cls,
        method: str,
        url: str,
        headers: Dict[str, str],
        kwargs: Dict[str, Any],
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """按前端 axios 拦截器规则补齐完整性头，并保证 body hash 与实际发送内容一致。"""
        if not cls._requires_game_integrity_headers(method, url):
            return headers, kwargs

        prepared_headers = headers.copy()
        prepared_kwargs = kwargs.copy()
        body_bytes = b""

        if "json" in prepared_kwargs:
            body_bytes = cls._compact_json_bytes(prepared_kwargs.pop("json"))
            prepared_kwargs["data"] = body_bytes
            prepared_headers["Content-Type"] = "application/json"
        elif "data" in prepared_kwargs:
            data_value = prepared_kwargs.get("data")
            if isinstance(data_value, (dict, list, tuple)):
                body_bytes = cls._compact_json_bytes(data_value)
                prepared_kwargs["data"] = body_bytes
                prepared_headers["Content-Type"] = "application/json"
            else:
                body_bytes = cls._coerce_body_bytes(data_value)
                if data_value is not None:
                    prepared_kwargs["data"] = body_bytes

        prepared_headers.update(cls._build_game_integrity_headers(body_bytes))
        return prepared_headers, prepared_kwargs

    @staticmethod
    def _build_proxy_config(proxy_url: str) -> Dict[str, str]:
        """把代理地址转换为 requests 需要的配置。"""
        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def _get_proxy_config(self, proxy_mode: str = "direct", proxy_url: Optional[str] = None) -> Dict[str, str]:
        """按账号代理模式解析本次请求的出站代理。"""
        mode = (proxy_mode or "direct").strip().lower()
        if mode == "direct":
            return {}
        if mode == "custom":
            cleaned_proxy_url = (proxy_url or "").strip()
            return self._build_proxy_config(cleaned_proxy_url) if cleaned_proxy_url else {}
        return {}

    def _get_session(self, proxy_mode: str = "direct", proxy_url: Optional[str] = None) -> requests.Session:
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
        proxy_config = self._get_proxy_config(proxy_mode=proxy_mode, proxy_url=proxy_url)
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

    @staticmethod
    def _get_origin(base_url: str) -> str:
        """从平台根地址生成 Origin 头。"""
        return (base_url or "").rstrip("/")

    @staticmethod
    def _extract_captcha_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        """兼容不同验证码接口返回结构。"""
        raw_data = payload.get("data")
        data = raw_data if isinstance(raw_data, dict) else payload
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _get_captcha_id(captcha_data: Dict[str, Any]) -> Optional[str]:
        """从验证码响应中提取 captcha_id。"""
        for key in ("captcha_id", "captchaId", "id"):
            value = captcha_data.get(key)
            if value:
                return str(value)
        return None

    @staticmethod
    def _normalize_captcha_answer(raw_answer: Any) -> Optional[str]:
        """清洗 OCR 输出。"""
        if raw_answer is None:
            return None
        answer = str(raw_answer).strip()
        expression = (
            answer.replace(" ", "")
            .replace("=", "")
            .replace("＋", "+")
            .replace("－", "-")
            .replace("×", "*")
            .replace("x", "*")
            .replace("X", "*")
            .replace("÷", "/")
        )
        expression_match = re.search(r"(\d{1,2})([+\-*/])(\d{1,2})", expression)
        if expression_match:
            left = int(expression_match.group(1))
            operator = expression_match.group(2)
            right = int(expression_match.group(3))
            if operator == "+":
                return str(left + right)
            if operator == "-":
                return str(left - right)
            if operator == "*":
                return str(left * right)
            if operator == "/" and right != 0 and left % right == 0:
                return str(left // right)

        answer = re.sub(r"[^0-9A-Za-z]", "", answer)
        if not answer:
            return None
        return answer

    @staticmethod
    def _score_captcha_answer(answer: str) -> int:
        """给 OCR 候选答案打分，优先选择常见的 4-6 位字母数字验证码。"""
        if not answer:
            return -100

        length = len(answer)
        score = 0
        if length == 5:
            score += 55
        elif length == 4:
            score += 35
        elif length == 6:
            score += 30
        elif 3 <= length <= 8:
            score += 15
        else:
            score -= 30

        unsigned_answer = answer.lstrip("-")
        if unsigned_answer.isalnum():
            score += 20
        if unsigned_answer.isdigit() and 1 <= len(unsigned_answer) <= 2:
            score += 25
        if unsigned_answer.isdigit() or unsigned_answer.isalpha():
            score += 5
        if any(char.isdigit() for char in unsigned_answer) and any(char.isalpha() for char in unsigned_answer):
            score += 10

        score -= abs(length - 5) * 3
        return score

    @staticmethod
    def _captcha_variant_weight(variant_name: str) -> int:
        """同分时优先保留信息更多的图像版本，避免二值化误伤字符细节。"""
        if variant_name == "gray_autocontrast":
            return 6
        if variant_name == "original":
            return 5
        if variant_name == "contrast_median":
            return 3
        if variant_name.startswith("binary_"):
            return 1
        return 0

    @staticmethod
    def _is_low_fidelity_captcha_variant(variant_name: str) -> bool:
        return variant_name.startswith("binary_")

    def _get_captcha_ocr(self):
        """懒加载并复用 ddddocr 实例，避免每次验证码都重新加载模型。"""
        if self._captcha_ocr is not None:
            return self._captcha_ocr

        with self._captcha_ocr_lock:
            if self._captcha_ocr is not None:
                return self._captcha_ocr
            import ddddocr  # type: ignore

            try:
                self._captcha_ocr = ddddocr.DdddOcr(show_ad=False)
            except TypeError:
                self._captcha_ocr = ddddocr.DdddOcr()
            return self._captcha_ocr

    def _classify_captcha_image(self, image_bytes: bytes) -> Any:
        """串行调用共享 OCR 实例，避免并发签到时模型对象状态互相影响。"""
        with self._captcha_ocr_lock:
            ocr = self._get_captcha_ocr()
            return ocr.classification(image_bytes)

    @staticmethod
    def _image_to_png_bytes(image: Any) -> bytes:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @classmethod
    def _iter_captcha_image_candidates(cls, image_bytes: bytes) -> Iterable[Tuple[str, bytes]]:
        """生成多种验证码图片候选，提升 ddddocr 对噪声、低对比度图片的稳定性。"""
        yield "original", image_bytes

        try:
            from PIL import Image, ImageEnhance, ImageFilter, ImageOps
        except ImportError:
            return

        try:
            with Image.open(BytesIO(image_bytes)) as opened:
                image = opened.convert("RGB")
        except Exception:
            return

        width, height = image.size
        scale = 2 if max(width, height) < 160 else 1
        if scale > 1:
            resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
            image = image.resize((width * scale, height * scale), resampling)

        gray = ImageOps.grayscale(image)
        gray = ImageOps.autocontrast(gray)
        yield "gray_autocontrast", cls._image_to_png_bytes(gray)

        enhanced = ImageEnhance.Contrast(gray).enhance(1.8)
        enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
        yield "contrast_median", cls._image_to_png_bytes(enhanced)

        for threshold in (110, 130, 150, 170):
            binary = enhanced.point(lambda pixel, limit=threshold: 255 if pixel > limit else 0, mode="1")
            yield f"binary_{threshold}", cls._image_to_png_bytes(binary.convert("L"))

    @staticmethod
    def _find_value_by_keys(data: Any, keys: set[str]) -> Optional[str]:
        """递归查找验证码图片字段。"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in keys and isinstance(value, str) and value:
                    return str(value)
            for value in data.values():
                found = AnyRouterService._find_value_by_keys(value, keys)
                if found:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = AnyRouterService._find_value_by_keys(item, keys)
                if found:
                    return found
        return None

    def _extract_captcha_image_bytes(self, captcha_data: Dict[str, Any], session: requests.Session = None) -> Optional[bytes]:
        """从验证码响应中提取图片字节。"""
        image_value = self._find_value_by_keys(
            captcha_data,
            {
                "captcha",
                "captcha_image",
                "captchaimage",
                "image",
                "image_base64",
                "imagebase64",
                "img",
                "img_base64",
                "imgbase64",
                "pic",
                "picture",
                "data",
            },
        )
        if not image_value:
            return None

        image_text = image_value.strip()
        if image_text.startswith("data:image/"):
            _, _, image_text = image_text.partition(",")

        if image_text.startswith("http://") or image_text.startswith("https://"):
            http_session = session or requests.Session()
            response = http_session.get(image_text, timeout=settings.request_timeout)
            response.raise_for_status()
            return response.content

        try:
            padded_image_text = image_text + "=" * (-len(image_text) % 4)
            return base64.b64decode(padded_image_text, validate=False)
        except Exception:
            return None

    def _solve_captcha_with_builtin_ocr(
        self,
        captcha_data: Dict[str, Any],
        session: requests.Session = None,
        trace_id: str = "",
    ) -> Tuple[bool, Dict[str, Any]]:
        """使用内置 OCR 识别图片验证码。"""
        image_bytes = self._extract_captcha_image_bytes(captcha_data, session=session)
        if not image_bytes:
            logger.warning("验证码签到[%s] OCR 图片提取失败: data_keys=%s", trace_id, list(captcha_data.keys()))
            return False, {"message": "验证码响应中未找到可识别的图片字段"}
        logger.info("验证码签到[%s] OCR 图片提取成功: image_bytes=%s", trace_id, len(image_bytes))

        try:
            self._get_captcha_ocr()
        except ImportError:
            logger.error("验证码签到[%s] OCR 依赖缺失: ddddocr 未安装", trace_id)
            return False, {"message": "未安装内置验证码识别依赖，请执行 pip install ddddocr"}

        try:
            candidates: List[Dict[str, Any]] = []
            seen_answers: set[str] = set()

            for variant_name, candidate_bytes in self._iter_captcha_image_candidates(image_bytes):
                try:
                    answer = self._normalize_captcha_answer(self._classify_captcha_image(candidate_bytes))
                except Exception as variant_error:
                    logger.debug(
                        "验证码签到[%s] OCR 候选识别异常: variant=%s error=%s",
                        trace_id,
                        variant_name,
                        variant_error,
                    )
                    continue
                if not answer:
                    continue

                answer_key = answer.upper()
                score = self._score_captcha_answer(answer)
                if answer_key in seen_answers:
                    score += 3 if self._is_low_fidelity_captcha_variant(variant_name) else 8
                else:
                    seen_answers.add(answer_key)
                candidates.append({
                    "answer": answer,
                    "variant": variant_name,
                    "score": score,
                    "variant_weight": self._captcha_variant_weight(variant_name),
                })

            if not candidates:
                logger.warning("验证码签到[%s] OCR 识别失败: 返回空结果", trace_id)
                return False, {"message": "内置 OCR 未识别出验证码"}

            best_candidate = max(candidates, key=lambda item: (item["score"] + item["variant_weight"], item["score"]))
            answer = best_candidate["answer"]
            if not answer:
                logger.warning("验证码签到[%s] OCR 识别失败: 返回空结果", trace_id)
                return False, {"message": "内置 OCR 未识别出验证码"}
            logger.info(
                "验证码签到[%s] OCR 识别成功: answer=%s answer_length=%s variant=%s total_score=%s candidates=%s",
                trace_id,
                _mask_log_value(answer, keep=1),
                len(answer),
                best_candidate["variant"],
                best_candidate["score"] + best_candidate["variant_weight"],
                [
                    f"{item['variant']}:len={len(str(item['answer']))}:score={item['score']}:weight={item['variant_weight']}"
                    for item in candidates
                ],
            )
            return True, {"captcha_answer": answer}
        except Exception as e:
            logger.exception("验证码签到[%s] OCR 识别异常", trace_id)
            return False, {"message": f"内置 OCR 识别失败: {str(e)}"}

    def _solve_checkin_captcha(
        self,
        captcha_data: Dict[str, Any],
        session: requests.Session = None,
        trace_id: str = "",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        识别签到验证码。

        使用内置 ddddocr 直接识别图片验证码。
        """
        return self._solve_captcha_with_builtin_ocr(captcha_data, session=session, trace_id=trace_id)

    def _post_with_anti_crawler_retry(
        self,
        session: requests.Session,
        url: str,
        headers: Dict[str, str],
        cookies: Dict[str, str],
        **kwargs: Any,
    ) -> requests.Response:
        """POST 请求并处理一次阿里云盾挑战。"""
        request_headers, request_kwargs = self._prepare_game_integrity_request(
            "post",
            url,
            headers,
            kwargs,
        )
        response = session.post(
            url,
            headers=request_headers,
            cookies=cookies,
            timeout=settings.request_timeout,
            **request_kwargs,
        )

        if self._is_anti_crawler_challenge(response.text):
            result = self.anti_crawler.solve(response.text)
            if result:
                cookies["acw_sc__v2"] = result
                time.sleep(2)
                response = session.post(
                    url,
                    headers=request_headers,
                    cookies=cookies,
                    timeout=settings.request_timeout,
                    **request_kwargs,
                )

        return response

    def _request_with_anti_crawler_retry(
        self,
        session: requests.Session,
        method: str,
        url: str,
        headers: Dict[str, str],
        cookies: Dict[str, str],
        **kwargs: Any,
    ) -> requests.Response:
        """通用请求并处理一次阿里云盾挑战。"""
        if method.lower() == "post":
            return self._post_with_anti_crawler_retry(
                session,
                url,
                headers,
                cookies,
                **kwargs,
            )

        request_fn = getattr(session, method.lower())
        response = request_fn(
            url,
            headers=headers,
            cookies=cookies,
            timeout=settings.request_timeout,
            **kwargs,
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
                    timeout=settings.request_timeout,
                    **kwargs,
                )

        return response

    def _parse_json_response(self, response: requests.Response, parse_error_message: str) -> Tuple[bool, Dict[str, Any]]:
        """解析 JSON 响应，统一处理空响应和解析错误。"""
        if not response.text.strip():
            return False, {"message": "接口返回为空"}
        if self._is_anti_crawler_challenge(response.text):
            return False, {"message": "接口仍返回反爬挑战"}
        try:
            return True, response.json()
        except json.JSONDecodeError:
            return False, {"message": parse_error_message}

    def _post_json(
        self,
        session: requests.Session,
        url: str,
        headers: Dict[str, str],
        cookies: Dict[str, str],
        parse_error_message: str = "响应解析失败",
        **kwargs: Any,
    ) -> Tuple[bool, Dict[str, Any]]:
        """POST JSON 请求并解析响应。"""
        response = self._post_with_anti_crawler_retry(
            session,
            url,
            headers,
            cookies,
            **kwargs,
        )
        return self._parse_json_response(response, parse_error_message)

    def _json_request(
        self,
        session: requests.Session,
        method: str,
        url: str,
        headers: Dict[str, str],
        cookies: Dict[str, str],
        parse_error_message: str = "响应解析失败",
        **kwargs: Any,
    ) -> Tuple[bool, Dict[str, Any]]:
        """任意 HTTP 方法的 JSON 请求并解析响应。"""
        response = self._request_with_anti_crawler_retry(
            session,
            method,
            url,
            headers,
            cookies,
            **kwargs,
        )
        return self._parse_json_response(response, parse_error_message)

    def _sign_in_with_captcha(
        self,
        session: requests.Session,
        cookies: Dict[str, str],
        headers: Dict[str, str],
        base_url: str,
        sign_api: str,
        captcha_api: str = "",
    ) -> Tuple[bool, Dict[str, Any]]:
        """拉取签到验证码，识别后提交验证码签到请求。"""
        last_result: Dict[str, Any] = {"success": False, "message": "验证码签到失败"}
        total_attempts = settings.retry_times
        trace_id = uuid.uuid4().hex[:8]
        logger.info(
            "验证码签到[%s] 开始: sign_api=%s captcha_api=%s retry_times=%s",
            trace_id,
            sign_api,
            captcha_api or "",
            total_attempts,
        )
        for captcha_attempt in range(settings.retry_times):
            if captcha_attempt > 0:
                time.sleep(settings.retry_interval)
            logger.info("验证码签到[%s] 尝试: attempt=%s/%s", trace_id, captcha_attempt + 1, total_attempts)

            captcha_success, captcha_result = self._sign_in_with_single_captcha(
                session=session,
                cookies=cookies,
                headers=headers,
                base_url=base_url,
                sign_api=sign_api,
                captcha_api=captcha_api,
                trace_id=trace_id,
            )
            if captcha_success:
                logger.info(
                    "验证码签到[%s] 成功: attempt=%s/%s message=%s reward_quota=%s already_signed=%s",
                    trace_id,
                    captcha_attempt + 1,
                    total_attempts,
                    captcha_result.get("message", ""),
                    captcha_result.get("reward_quota", 0),
                    captcha_result.get("already_signed", False),
                )
                return captcha_success, captcha_result

            last_result = captcha_result
            logger.warning(
                "验证码签到[%s] 失败: attempt=%s/%s message=%s",
                trace_id,
                captcha_attempt + 1,
                total_attempts,
                captcha_result.get("message", ""),
            )
            if not self._requires_captcha_message(captcha_result.get("message", "")):
                logger.info("验证码签到[%s] 停止重试: 当前失败原因不属于验证码重试场景", trace_id)
                break

        logger.warning("验证码签到[%s] 结束: success=False message=%s", trace_id, last_result.get("message", ""))
        return False, last_result

    def _sign_in_with_single_captcha(
        self,
        session: requests.Session,
        cookies: Dict[str, str],
        headers: Dict[str, str],
        base_url: str,
        sign_api: str,
        captcha_api: str = "",
        trace_id: str = "",
    ) -> Tuple[bool, Dict[str, Any]]:
        """执行一次验证码获取、识别和签到提交。"""
        resolved_captcha_api = (captcha_api or "").strip()
        if not resolved_captcha_api:
            logger.warning("验证码签到[%s] 缺少 captcha_api: sign_api=%s", trace_id, sign_api)
            return False, {"success": False, "message": "该平台需要验证码，请先在平台配置中填写验证码接口"}
        if not resolved_captcha_api.startswith("/"):
            resolved_captcha_api = f"/{resolved_captcha_api}"
        captcha_url = f"{base_url}{resolved_captcha_api}"
        captcha_headers = headers.copy()
        captcha_headers["origin"] = self._get_origin(base_url)

        logger.info("验证码签到[%s] 请求验证码: url=%s", trace_id, captcha_url)
        captcha_response = self._post_with_anti_crawler_retry(
            session,
            captcha_url,
            captcha_headers,
            cookies,
        )
        logger.info(
            "验证码签到[%s] 验证码接口响应: status_code=%s content_length=%s",
            trace_id,
            captcha_response.status_code,
            len(captcha_response.text or ""),
        )
        if not captcha_response.text.strip():
            logger.warning("验证码签到[%s] 验证码接口返回为空: url=%s", trace_id, captcha_url)
            return False, {"success": False, "message": "验证码接口返回为空"}

        if self._is_anti_crawler_challenge(captcha_response.text):
            logger.warning("验证码签到[%s] 验证码接口返回反爬挑战: url=%s", trace_id, captcha_url)
            return False, {"success": False, "message": "验证码接口仍返回反爬挑战"}

        try:
            captcha_payload = captcha_response.json()
        except json.JSONDecodeError:
            logger.warning("验证码签到[%s] 验证码接口 JSON 解析失败: url=%s", trace_id, captcha_url)
            return False, {"success": False, "message": "验证码接口响应解析失败"}
        logger.info(
            "验证码签到[%s] 验证码接口 JSON: success=%s message=%s keys=%s",
            trace_id,
            captcha_payload.get("success", False),
            captcha_payload.get("message", ""),
            list(captcha_payload.keys()),
        )
        if not captcha_payload.get("success", False):
            logger.warning(
                "验证码签到[%s] 获取验证码失败: message=%s",
                trace_id,
                captcha_payload.get("message", "获取验证码失败"),
            )
            return False, {
                "success": False,
                "message": captcha_payload.get("message", "获取验证码失败"),
                "raw": captcha_payload,
            }

        captcha_data = self._extract_captcha_data(captcha_payload)
        captcha_id = self._get_captcha_id(captcha_data)
        if not captcha_id:
            logger.warning("验证码签到[%s] 验证码接口未返回 captcha_id: data_keys=%s", trace_id, list(captcha_data.keys()))
            return False, {
                "success": False,
                "message": "验证码接口未返回 captcha_id",
                "raw": captcha_payload,
            }
        logger.info(
            "验证码签到[%s] 验证码数据提取成功: captcha_id=%s data_keys=%s",
            trace_id,
            _mask_log_value(captcha_id),
            list(captcha_data.keys()),
        )

        solve_success, solve_result = self._solve_checkin_captcha(captcha_data, session=session, trace_id=trace_id)
        if not solve_success:
            logger.warning("验证码签到[%s] 识别失败: message=%s", trace_id, solve_result.get("message", "验证码识别失败"))
            return False, {
                "success": False,
                "message": solve_result.get("message", "验证码识别失败"),
                "raw": captcha_payload,
            }

        sign_headers = headers.copy()
        sign_headers["content-type"] = "application/json"
        sign_headers["origin"] = self._get_origin(base_url)
        sign_payload = {
            "captcha_id": captcha_id,
            "captcha_answer": solve_result["captcha_answer"],
        }
        logger.info(
            "验证码签到[%s] 提交签到: url=%s captcha_id=%s captcha_answer=%s answer_length=%s",
            trace_id,
            f"{base_url}{sign_api}",
            _mask_log_value(captcha_id),
            _mask_log_value(solve_result["captcha_answer"], keep=1),
            len(str(solve_result["captcha_answer"])),
        )
        parsed, sign_data = self._post_json(
            session,
            f"{base_url}{sign_api}",
            sign_headers,
            cookies,
            json=sign_payload,
        )
        if not parsed:
            logger.warning("验证码签到[%s] 提交响应解析失败: message=%s", trace_id, sign_data.get("message", "签到响应解析失败"))
            return False, {
                "success": False,
                "message": sign_data.get("message", "签到响应解析失败"),
            }
        normalized = self._normalize_sign_payload(sign_data)
        logger.info(
            "验证码签到[%s] 提交完成: success=%s message=%s reward_quota=%s already_signed=%s",
            trace_id,
            normalized.get("success", False),
            normalized.get("message", ""),
            normalized.get("reward_quota", 0),
            normalized.get("already_signed", False),
        )
        if not normalized.get("success", False):
            return False, normalized
        return True, normalized

    def _get_base_headers(self, base_url: str, console_url: str = None) -> Dict[str, str]:
        """获取基础请求头（无认证，用于公开接口）"""
        if console_url is None:
            console_url = DEFAULT_CONSOLE_URL
        headers = self.BASE_HEADERS.copy()
        headers["referer"] = f"{base_url}{console_url}"
        return headers

    @staticmethod
    def _extract_session_cookie(response: Optional[requests.Response], session: requests.Session) -> Optional[str]:
        """从响应或 Session 中提取 session cookie。"""
        if response is not None and response.cookies.get("session"):
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
        session: requests.Session = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None
    ) -> Dict[str, str]:
        """获取 Cookies 并处理反爬虫挑战"""
        if console_url is None:
            console_url = DEFAULT_CONSOLE_URL
        cookies = {"session": session_cookie}
        headers = self._get_headers(user_id, base_url, console_url)
        if session is None:
            session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)

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

    def _get_checkin_pow_token(
        self,
        session: requests.Session,
        base_url: str,
        headers: Dict[str, str],
        cookies: Dict[str, str],
    ) -> Optional[str]:
        """尝试获取并求解签到 PoW token；站点未启用时返回 None。"""
        try:
            response = self._request_with_anti_crawler_retry(
                session,
                "get",
                f"{base_url}/api/pow/challenge",
                headers,
                cookies,
            )
            parsed, data = self._parse_json_response(response, "PoW challenge 响应解析失败")
            if not parsed or not data.get("success"):
                return None

            raw_data = data.get("data", {})
            if not isinstance(raw_data, dict) or not raw_data.get("enabled"):
                return None

            challenge = str(raw_data.get("challenge") or "")
            difficulty = self._safe_int(raw_data.get("difficulty"), 0)
            if not challenge or difficulty <= 0:
                return ""

            pow_result = self._solve_pow_challenge(challenge, difficulty)
            return self._build_pow_token(challenge, pow_result)
        except Exception as e:
            logger.debug("获取签到 PoW token 失败，继续普通签到: %s", e)
            return None

    def login(
        self,
        base_url: str,
        username: str,
        password: str,
        login_api: str = None,
        login_page: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """使用账号密码登录并提取新的 session cookie。"""
        if login_api is None:
            login_api = self.DEFAULT_LOGIN_API
        if login_page is None:
            login_page = self.DEFAULT_LOGIN_PAGE

        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
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

            login_kwargs: Dict[str, Any] = {
                "json": {"username": username, "password": password},
            }

            parsed, data = self._post_json(
                session,
                f"{base_url}{login_api}",
                login_headers,
                cookies,
                parse_error_message="登录响应解析失败",
                **login_kwargs,
            )
            if not parsed:
                return False, {"message": data.get("message", "登录响应解析失败")}

            if not data.get("success"):
                return False, {"message": data.get("message", "登录失败")}

            session_cookie = self._extract_session_cookie(None, session)
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
                "checked_in": user_info.get("checked_in"),
                "quota": self._safe_int(user_info.get("quota"), 0),
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
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取用户信息
        """
        if user_api is None:
            user_api = DEFAULT_USER_API
        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
        cookies = self._get_cookies_with_challenge(
            session_cookie,
            user_id,
            base_url,
            console_url,
            session=session,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
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
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """获取指定月份的签到记录。"""
        if checkin_api is None:
            checkin_api = DEFAULT_CHECKIN_API
        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
        cookies = self._get_cookies_with_challenge(
            session_cookie,
            user_id,
            base_url,
            console_url,
            session=session,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
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
        console_url: str = None,
        captcha_api: str = "",
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        执行签到
        """
        if sign_api is None:
            sign_api = DEFAULT_SIGN_API
        if checkin_api is None:
            checkin_api = DEFAULT_CHECKIN_API
        should_try_captcha_first = bool((captcha_api or "").strip())
        for attempt in range(settings.retry_times):
            if attempt > 0:
                time.sleep(settings.retry_interval)

            session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
            cookies = self._get_cookies_with_challenge(
                session_cookie,
                user_id,
                base_url,
                console_url,
                session=session,
                proxy_mode=proxy_mode,
                proxy_url=proxy_url,
            )
            headers = self._get_headers(user_id, base_url, console_url)

            try:
                if should_try_captcha_first:
                    captcha_success, result = self._sign_in_with_captcha(
                        session=session,
                        cookies=cookies,
                        headers=headers,
                        base_url=base_url,
                        sign_api=sign_api,
                        captcha_api=captcha_api,
                    )
                    if not captcha_success:
                        return False, result
                    data = result.get("raw", {}) if isinstance(result.get("raw"), dict) else {}
                else:
                    sign_headers = headers
                    sign_kwargs: Dict[str, Any] = {}
                    sign_url = f"{base_url}{sign_api}"
                    if self._should_sign_checkin_request(sign_api, checkin_api):
                        month = datetime.now(SHANGHAI_TZ).strftime("%Y-%m")
                        checkin_url = f"{base_url}{checkin_api}?month={month}"
                        checkin_response = self._request_with_anti_crawler_retry(
                            session,
                            "get",
                            checkin_url,
                            headers,
                            cookies,
                        )
                        parsed_checkin, checkin_data = self._parse_json_response(
                            checkin_response,
                            "签到状态响应解析失败",
                        )
                        if parsed_checkin and checkin_data.get("success"):
                            raw_checkin_data = checkin_data.get("data", {})
                            checkin_nonce = raw_checkin_data.get("checkin_nonce") if isinstance(raw_checkin_data, dict) else ""
                            if checkin_nonce:
                                sign_headers = headers.copy()
                                sign_headers["content-type"] = "application/json"
                                sign_headers.update(self._build_checkin_signature_headers(user_id, str(checkin_nonce)))
                                sign_kwargs["json"] = {}

                        pow_token = self._get_checkin_pow_token(
                            session=session,
                            base_url=base_url,
                            headers=headers,
                            cookies=cookies,
                        )
                        if pow_token is not None:
                            sign_url = self._append_query_param(sign_url, "pow_token", pow_token)

                    parsed, data = self._post_json(
                        session,
                        sign_url,
                        sign_headers,
                        cookies,
                        **sign_kwargs,
                    )
                    if not parsed:
                        if data.get("message") == "接口返回为空":
                            continue
                        if data.get("message") == "接口仍返回反爬挑战":
                            continue
                        return False, {"success": False, "message": data.get("message", "签到响应解析失败")}

                    if not data:
                        continue

                    result = self._normalize_sign_payload(data)

                    if not result["success"] and self._requires_captcha_message(result.get("message", "")):
                        captcha_success, result = self._sign_in_with_captcha(
                            session=session,
                            cookies=cookies,
                            headers=headers,
                            base_url=base_url,
                            sign_api=sign_api,
                            captcha_api=captcha_api,
                        )
                        if not captcha_success:
                            return False, result
                        data = result.get("raw", {}) if isinstance(result.get("raw"), dict) else data

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
                            console_url=console_url,
                            proxy_mode=proxy_mode,
                            proxy_url=proxy_url,
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
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取 API Token 列表
        """
        if token_api is None:
            token_api = DEFAULT_TOKEN_API
        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
        cookies = self._get_cookies_with_challenge(
            session_cookie,
            user_id,
            base_url,
            console_url,
            session=session,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
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
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取可用模型列表
        """
        if models_api is None:
            models_api = DEFAULT_MODELS_API
        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
        cookies = self._get_cookies_with_challenge(
            session_cookie,
            user_id,
            base_url,
            console_url,
            session=session,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
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
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        获取账号分组列表
        """
        if groups_api is None:
            groups_api = DEFAULT_GROUPS_API
        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
        cookies = self._get_cookies_with_challenge(
            session_cookie,
            user_id,
            base_url,
            console_url,
            session=session,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
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
        fail_msg: str = "操作失败",
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """令牌相关请求的通用方法"""
        if token_api is None:
            token_api = DEFAULT_TOKEN_API
        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
        cookies = self._get_cookies_with_challenge(
            session_cookie,
            user_id,
            base_url,
            console_url,
            session=session,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
        headers = self._get_headers(user_id, base_url, console_url)
        headers["content-type"] = "application/json"

        try:
            url = f"{base_url}{token_api}"
            parsed, data = self._json_request(
                session,
                method,
                url,
                headers,
                cookies,
                json=payload,
            )

            if not parsed:
                return False, {"message": data.get("message", "响应解析失败")}

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
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
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
            method="post", success_msg="创建成功", fail_msg="创建令牌失败",
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )

    def update_token(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        token_data: Dict[str, Any],
        token_api: str = None,
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """更新访问令牌"""
        return self._token_request(
            session_cookie, user_id, base_url, token_data,
            token_api=token_api,
            console_url=console_url,
            method="put", success_msg="更新成功", fail_msg="更新令牌失败",
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )

    def delete_token(
        self,
        session_cookie: str,
        user_id: str,
        base_url: str,
        token_id: int,
        token_api: str = None,
        console_url: str = None,
        proxy_mode: str = "direct",
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        删除访问令牌
        """
        if token_api is None:
            token_api = DEFAULT_TOKEN_API
        session = self._get_session(proxy_mode=proxy_mode, proxy_url=proxy_url)
        cookies = self._get_cookies_with_challenge(
            session_cookie,
            user_id,
            base_url,
            console_url,
            session=session,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
        headers = self._get_headers(user_id, base_url, console_url)

        try:
            url = f"{base_url}{token_api}/{token_id}"
            parsed, data = self._json_request(
                session,
                "delete",
                url,
                headers,
                cookies,
            )
            if not parsed:
                return False, {"message": data.get("message", "响应解析失败")}

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
