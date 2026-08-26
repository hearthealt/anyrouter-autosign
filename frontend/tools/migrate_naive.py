"""
Naive UI → 自建 UI 原语库的机械迁移。

只做**能确定安全**的三件事：
1. 1:1 标签重命名（n-button → UiButton 之类）
2. 解开 <n-icon :size="N"><Foo /></n-icon> → <Foo :size="N" />
3. 重写 @vicons/ionicons5 和 naive-ui 的 import 语句

需要人工判断的（n-form / n-tabs / n-card / n-spin / n-radio-group / n-drawer-content 等
结构会变的）一律**不动**，只在报告里列出来，由人逐个处理。

用法：
    python tools/migrate_naive.py            # 预演，只报告
    python tools/migrate_naive.py --write    # 实际写入
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import Counter

SRC = pathlib.Path('src')

# ── 可安全自动替换的标签
SAFE_TAGS = {
    'n-button': 'UiButton',
    'n-input': 'UiInput',
    'n-input-number': 'UiNumberInput',
    'n-select': 'UiSelect',
    'n-checkbox': 'UiCheckbox',
    'n-switch': 'UiSwitch',
    'n-tag': 'UiTag',
    'n-badge': 'UiBadge',
    'n-divider': 'UiDivider',
    'n-skeleton': 'UiSkeleton',
    'n-popover': 'UiPopover',
    'n-tooltip': 'UiTooltip',
    'n-dropdown': 'UiDropdown',
    'n-popconfirm': 'UiConfirm',
    'n-data-table': 'DataGrid',
    'n-pagination': 'UiPagination',
    'n-date-picker': 'UiDateRange',
    'n-time-picker': 'UiTimeField',
    'n-modal': 'UiModal',
}

# ── 结构会变，必须人工处理
MANUAL_TAGS = {
    'n-form', 'n-form-item', 'n-card', 'n-spin', 'n-tabs', 'n-tab-pane',
    'n-radio-group', 'n-radio-button', 'n-drawer', 'n-drawer-content',
    'n-upload', 'n-config-provider', 'n-message-provider', 'n-dialog-provider',
    'n-collapse', 'n-collapse-item', 'n-alert', 'n-empty', 'n-scrollbar',
}

# ── ionicons5 → lucide
ICONS = {
    'AddOutline': 'Plus',
    'AlertCircleOutline': 'AlertCircle',
    'ArrowBackOutline': 'ArrowLeft',
    'ChatbubbleOutline': 'MessageCircle',
    'CheckmarkCircleOutline': 'CircleCheck',
    'CheckmarkOutline': 'Check',
    'ChevronBackOutline': 'ChevronLeft',
    'ChevronForwardOutline': 'ChevronRight',
    'ChevronDownOutline': 'ChevronDown',
    'CloseCircleOutline': 'CircleX',
    'CloseOutline': 'X',
    'CloudDownloadOutline': 'CloudDownload',
    'CloudUploadOutline': 'CloudUpload',
    'CopyOutline': 'Copy',
    'CreateOutline': 'Pencil',
    'DocumentTextOutline': 'FileText',
    'DownloadOutline': 'Download',
    'EyeOffOutline': 'EyeOff',
    'EyeOutline': 'Eye',
    'FlashOutline': 'Zap',
    'FolderOpenOutline': 'FolderOpen',
    'GridOutline': 'LayoutDashboard',
    'InformationCircleOutline': 'Info',
    'KeyOutline': 'KeyRound',
    'LockClosedOutline': 'Lock',
    'LogoWechat': 'MessageSquare',
    'MailOutline': 'Mail',
    'MenuOutline': 'Menu',
    'MoonOutline': 'Moon',
    'NotificationsOffOutline': 'BellOff',
    'NotificationsOutline': 'Bell',
    'PaperPlaneOutline': 'Send',
    'PeopleOutline': 'Users',
    'PersonOutline': 'User',
    'PulseOutline': 'Activity',
    'RefreshOutline': 'RefreshCw',
    'SearchOutline': 'Search',
    'SendOutline': 'Send',
    'ServerOutline': 'Server',
    'SettingsOutline': 'Settings',
    'StatsChartOutline': 'BarChart3',
    'SunnyOutline': 'Sun',
    'SyncOutline': 'RefreshCcw',
    'TimeOutline': 'Clock',
    'TrashOutline': 'Trash2',
    'WalletOutline': 'Wallet',
    'WarningOutline': 'TriangleAlert',
    'HelpCircleOutline': 'CircleHelp',
    'LogOutOutline': 'LogOut',
}

# ── naive-ui 的具名导入（render 函数里用）
NAIVE_IMPORTS = {
    'NButton': 'UiButton',
    'NTag': 'UiTag',
    'NIcon': None,          # 直接删掉，图标自带 size
    'NPopconfirm': 'UiConfirm',
    'NModal': 'UiModal',
    'NInput': 'UiInput',
    'NCheckbox': 'UiCheckbox',
    'NSelect': 'UiSelect',
    'NDivider': 'UiDivider',
    'NSwitch': 'UiSwitch',
    'NTooltip': 'UiTooltip',
    'NForm': None,
    'NFormItem': None,
    'NCard': None,          # 结构变成 div.card，人工处理
    'NSpin': None,          # 人工处理
}

# ── 从 ui/ 导入的组件名（用于自动补 import）
UI_EXPORTS = set(SAFE_TAGS.values()) | {'UiSpinner', 'UiSegment', 'UiDrawer', 'UiFileDrop'}


def unwrap_icons(text: str) -> tuple[str, int]:
    """<n-icon :size="14"><Foo /></n-icon> → <Foo :size="14" />"""
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        attrs, inner = m.group(1) or '', m.group(2).strip()
        # 取出 n-icon 上的 size
        size_m = re.search(r':size="([^"]+)"', attrs)
        size = size_m.group(1) if size_m else None
        # 内部必须是单个自闭合组件标签
        tag_m = re.fullmatch(r'<([A-Z][A-Za-z0-9]*)\s*/>', inner)
        if not tag_m:
            return m.group(0)  # 结构复杂，留给人工
        count += 1
        icon = tag_m.group(1)
        return f'<{icon}{f" :size=\"{size}\"" if size else ""} />'

    text = re.sub(r'<n-icon([^>]*?)>(.*?)</n-icon>', repl, text, flags=re.S)
    return text, count


def rewrite_vicons_import(text: str) -> tuple[str, list[str]]:
    """把 @vicons/ionicons5 的 import 改写成 lucide-vue-next。"""
    unknown: list[str] = []

    def repl(m: re.Match[str]) -> str:
        names = [n.strip() for n in m.group(1).split(',') if n.strip()]
        mapped: list[str] = []
        for n in names:
            target = ICONS.get(n)
            if target is None:
                unknown.append(n)
                continue
            if target not in mapped:
                mapped.append(target)
        if not mapped:
            return ''
        return 'import { ' + ', '.join(sorted(mapped)) + " } from 'lucide-vue-next'"

    text = re.sub(r"import\s*\{([^}]+)\}\s*from\s*'@vicons/ionicons5'", repl, text, flags=re.S)
    return text, unknown


def rewrite_naive_import(text: str, rel_ui: str) -> tuple[str, list[str]]:
    """把 naive-ui 的具名导入改写成从 ui/ 导入；类型导入直接删。"""
    unhandled: list[str] = []

    # 纯类型导入：import type { X } from 'naive-ui'
    text = re.sub(r"import\s+type\s*\{[^}]+\}\s*from\s*'naive-ui'\s*\n", '', text)

    def repl(m: re.Match[str]) -> str:
        raw = m.group(1)
        mapped: list[str] = []
        for part in raw.split(','):
            n = part.strip()
            if not n:
                continue
            # 处理 `type DataTableColumns` 这类内联类型导入
            if n.startswith('type '):
                continue
            target = NAIVE_IMPORTS.get(n, '?')
            if target == '?':
                unhandled.append(n)
            elif target and target not in mapped:
                mapped.append(target)
        if not mapped:
            return ''
        return 'import { ' + ', '.join(sorted(mapped)) + f" }} from '{rel_ui}'"

    text = re.sub(r"import\s*\{([^}]+)\}\s*from\s*'naive-ui'", repl, text, flags=re.S)
    return text, unhandled


def rel_ui_path(path: pathlib.Path) -> str:
    """算出该文件到 src/ui 的相对导入路径。"""
    depth = len(path.relative_to(SRC).parts) - 1
    return ('../' * depth if depth else './') + 'ui'


def used_ui_components(text: str) -> list[str]:
    found = {t for t in re.findall(r'<(Ui[A-Z][A-Za-z0-9]*|DataGrid)\b', text)}
    return sorted(found & UI_EXPORTS)


def ensure_ui_import(text: str, rel_ui: str) -> str:
    """确保用到的 Ui* 组件都从 ui/ 导入。已有该 import 则合并。"""
    needed = used_ui_components(text)
    if not needed:
        return text

    existing = re.search(rf"import\s*\{{([^}}]+)\}}\s*from\s*'{re.escape(rel_ui)}'", text)
    if existing:
        have = {n.strip() for n in existing.group(1).split(',') if n.strip()}
        merged = sorted(have | set(needed))
        return text[:existing.start()] + 'import { ' + ', '.join(merged) + f" }} from '{rel_ui}'" + text[existing.end():]

    # 插到 <script setup> 里第一个 import 之前
    m = re.search(r"(<script setup[^>]*>\s*\n)", text)
    if not m:
        return text
    line = 'import { ' + ', '.join(needed) + f" }} from '{rel_ui}'\n"
    return text[:m.end()] + line + text[m.end():]


def migrate(path: pathlib.Path) -> dict:
    original = path.read_text(encoding='utf-8')
    text = original
    report: dict = {'file': str(path), 'tags': Counter(), 'icons': 0, 'manual': set(), 'unknown_icons': [], 'unhandled_naive': []}

    # 记录需要人工处理的标签
    for tag in MANUAL_TAGS:
        if re.search(rf'<{tag}[\s>/]', text):
            report['manual'].add(tag)

    # 1) 图标解包（必须在标签重命名之前，否则 n-icon 已被改名）
    text, icon_count = unwrap_icons(text)
    report['icons'] = icon_count

    # 2) 安全标签重命名
    for old, new in SAFE_TAGS.items():
        n = len(re.findall(rf'<{old}[\s>/]', text))
        if n:
            report['tags'][old] = n
            text = re.sub(rf'<{old}(?=[\s>/])', f'<{new}', text)
            text = text.replace(f'</{old}>', f'</{new}>')

    # 3) import 改写
    text, unknown = rewrite_vicons_import(text)
    report['unknown_icons'] = unknown

    rel = rel_ui_path(path)
    text, unhandled = rewrite_naive_import(text, rel)
    report['unhandled_naive'] = unhandled

    text = ensure_ui_import(text, rel)

    report['changed'] = text != original
    report['text'] = text
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true', help='实际写入文件')
    parser.add_argument('paths', nargs='*', help='只处理指定文件（默认全 src）')
    args = parser.parse_args()

    targets = [pathlib.Path(p) for p in args.paths] if args.paths else sorted(SRC.rglob('*.vue'))
    # src/ui 是自建原语库，不参与迁移（它的注释里提到过 n-tabs，会被误判）
    targets = [p for p in targets if p.suffix == '.vue' and 'ui' not in p.relative_to(SRC).parts[:1]]

    total_tags = Counter()
    total_icons = 0
    needs_manual: dict[str, set] = {}
    problems: list[str] = []

    for path in targets:
        r = migrate(path)
        if not r['changed'] and not r['manual']:
            continue

        if r['changed'] and args.write:
            path.write_text(r['text'], encoding='utf-8')

        total_tags.update(r['tags'])
        total_icons += r['icons']
        if r['manual']:
            needs_manual[str(path)] = r['manual']
        if r['unknown_icons']:
            problems.append(f"{path}: 未映射图标 {', '.join(r['unknown_icons'])}")
        if r['unhandled_naive']:
            problems.append(f"{path}: 未处理的 naive 导入 {', '.join(r['unhandled_naive'])}")

        flag = '写入' if args.write else '预演'
        print(f"[{flag}] {path}  标签 {sum(r['tags'].values())}  图标 {r['icons']}")

    print()
    print('=' * 62)
    print(f"自动替换标签合计: {sum(total_tags.values())}")
    for tag, n in total_tags.most_common():
        print(f"  {tag:20s} {n}")
    print(f"图标解包合计: {total_icons}")

    if needs_manual:
        print()
        print('需要人工处理的文件与标签:')
        for f, tags in sorted(needs_manual.items()):
            print(f"  {f}")
            print(f"      {', '.join(sorted(tags))}")

    if problems:
        print()
        print('遗留问题:')
        for p in problems:
            print(f"  {p}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
