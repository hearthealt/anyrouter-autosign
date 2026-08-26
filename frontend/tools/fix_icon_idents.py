"""
修正 migrate_naive.py 的遗漏：图标 import 已改名，但模板与 render 函数里的
组件标识符还是旧的 ionicons 名字。这里把整个文件里的标识符统一替换掉。

按标识符边界替换（\b...\b），不碰字符串字面量以外的东西 ——
这些名字只可能作为组件标识符出现，不会撞到业务词汇。

用法：
    python tools/fix_icon_idents.py            # 预演
    python tools/fix_icon_idents.py --write
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from migrate_naive import ICONS  # noqa: E402  复用同一张映射表

SRC = pathlib.Path('src')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()

    # 长名优先替换，避免 Foo 是 FooBar 前缀时误伤（这里其实无重叠，保险起见）
    ordered = sorted(ICONS.items(), key=lambda kv: -len(kv[0]))

    total = 0
    for path in sorted(SRC.rglob('*.vue')):
        if 'ui' in path.relative_to(SRC).parts[:1]:
            continue
        text = original = path.read_text(encoding='utf-8')
        hits = 0
        for old, new in ordered:
            n = len(re.findall(rf'\b{old}\b', text))
            if n:
                text = re.sub(rf'\b{old}\b', new, text)
                hits += n
        if hits:
            total += hits
            print(f'{path}  {hits} 处')
            if args.write:
                path.write_text(text, encoding='utf-8')

    # 同名图标合并后可能出现重复导入（PaperPlaneOutline 和 SendOutline 都映射成 Send）
    if args.write:
        for path in sorted(SRC.rglob('*.vue')):
            if 'ui' in path.relative_to(SRC).parts[:1]:
                continue
            text = path.read_text(encoding='utf-8')

            def dedup(m: re.Match[str]) -> str:
                names = sorted({n.strip() for n in m.group(1).split(',') if n.strip()})
                return 'import { ' + ', '.join(names) + " } from 'lucide-vue-next'"

            fixed = re.sub(r"import\s*\{([^}]+)\}\s*from\s*'lucide-vue-next'", dedup, text)
            if fixed != text:
                path.write_text(fixed, encoding='utf-8')
                print(f'{path}  去重 lucide 导入')

    print(f'\n合计替换 {total} 处标识符')
    return 0


if __name__ == '__main__':
    sys.exit(main())
