/**
 * 把列定义里的 `render()` 返回值渲染出来的函数式组件。
 *
 * 现有 5 处表格的列都用 `render: (row) => h(...)` 返回 VNode，
 * 模板里没法直接渲染一个 VNode 变量，所以需要这么一层。
 * 单独成文件是为了让它有稳定的组件标识，避免每次渲染都重建组件对象。
 */
import type { VNodeChild } from 'vue'

const RenderCell = (props: { node: VNodeChild }) => props.node

RenderCell.props = { node: { type: null, required: false } }

export default RenderCell
