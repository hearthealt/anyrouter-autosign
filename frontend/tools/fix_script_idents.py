"""
第三轮修正：script 块里残留的 Naive 标识符与类型名。

migrate_naive.py 只改了 import 语句，render 函数体里的 h(NButton, ...) 之类没动。
这里补上：

1. h(NIcon, null, { default: () => h(Foo) })  →  h(Foo, { size: 14 })
2. NButton / NTag / NSwitch / NTooltip / NPopconfirm  →  对应 Ui* 组件
3. DataTableColumns / DataTableSortState / DataTableSortOrder  →  GridColumn / GridSortState / SortOrder
   并确保这些类型从 ui/ 导入

用法：
    python tools/fix_script_idents.py --write
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

SRC = pathlib.Path('src')

COMPONENTS = {
    'NButton': 'UiButton',
    'NTag': 'UiTag',
    'NSwitch': 'UiSwitch',
    'NTooltip': 'UiTooltip',
    'NPopconfirm': 'UiConfirm',
    'NInput': 'UiInput',
    'NSelect': 'UiSelect',
    'NCheckbox': 'UiCheckbox',
    'NDivider': 'UiDivider',
}

TYPES = {
    'DataTableColumns': 'GridColumn',
    'DataTableSortState': 'GridSortState',
    'DataTableSortOrder': 'SortOrder',
}


def unwrap_h_icon(text: str) -> tuple[str, int]:
    """h(NIcon, ...{ default: () => h(Foo) }) → h(Foo, { size: N })

    Naive 的 NIcon 是个尺寸容器；lucide 图标自带 size prop，容器可以整层去掉。
    """
    count = 0

    # h(NIcon, { size: 14 }, { default: () => h(Foo) })  或  h(NIcon, null, {...})
    pattern = re.compile(
        r'h\(\s*NIcon\s*,\s*(null|\{[^{}]*\})\s*,\s*\{\s*default:\s*\(\)\s*=>\s*h\(\s*([A-Z][A-Za-z0-9]*)\s*\)\s*,?\s*\}\s*\)',
        re.S,
    )

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        props, icon = m.group(1), m.group(2)
        size_m = re.search(r'size:\s*(\d+)', props)
        size = size_m.group(1) if size_m else '14'
        return f'h({icon}, {{ size: {size} }})'

    return pattern.sub(repl, text), count


def ensure_type_import(text: str, path: pathlib.Path, needed: set[str]) -> str:
    """把 Grid* 类型加到从 ui/ 的导入里。"""
    if not needed:
        return text
    depth = len(path.relative_to(SRC).parts) - 1
    rel = ('../' * depth if depth else './') + 'ui'

    m = re.search(rf"import\s*\{{([^}}]+)\}}\s*from\s*'{re.escape(rel)}'", text)
    type_specs = [f'type {t}' for t in sorted(needed)]

    if m:
        have = [n.strip() for n in m.group(1).split(',') if n.strip()]
        for spec in type_specs:
            if spec not in have and spec.replace('type ', '') not in [h.replace('type ', '') for h in have]:
                have.append(spec)
        # 值导入排前面，类型导入排后面，读起来清楚
        values = sorted(h for h in have if not h.startswith('type '))
        types = sorted(h for h in have if h.startswith('type '))
        merged = ', '.join(values + types)
        return text[:m.start()] + f"import {{ {merged} }} from '{rel}'" + text[m.end():]

    anchor = re.search(r"(<script setup[^>]*>\s*\n)", text)
    if not anchor:
        return text
    line = f"import {{ {', '.join(type_specs)} }} from '{rel}'\n"
    return text[:anchor.end()] + line + text[anchor.end():]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()

    total = 0
    for path in sorted(SRC.rglob('*.vue')):
        if 'ui' in path.relative_to(SRC).parts[:1]:
            continue
        text = original = path.read_text(encoding='utf-8')
        hits = 0

        text, n = unwrap_h_icon(text)
        hits += n

        for old, new in COMPONENTS.items():
            c = len(re.findall(rf'\b{old}\b', text))
            if c:
                text = re.sub(rf'\b{old}\b', new, text)
                hits += c

        needed_types: set[str] = set()
        for old, new in TYPES.items():
            c = len(re.findall(rf'\b{old}\b', text))
            if c:
                text = re.sub(rf'\b{old}\b', new, text)
                needed_types.add(new)
                hits += c

        text = ensure_type_import(text, path, needed_types)

        if text != original:
            total += hits
            print(f'{path}  {hits} 处')
            if args.write:
                path.write_text(text, encoding='utf-8')

    print(f'\n合计 {total} 处')
    return 0


if __name__ == '__main__':
    sys.exit(main())
