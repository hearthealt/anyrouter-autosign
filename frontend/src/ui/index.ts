/**
 * UI 原语库统一出口。
 *
 * 自建组件替代 Naive UI。API 刻意贴合原有调用方式，
 * 让 25 个视图文件的迁移以换标签名为主，尽量不动逻辑。
 *
 * 不包含 Tabs：项目里两处 tabs 都是 `type="segment"`，
 * 用 UiSegment 配 v-show 更直接，不值得再造一层。
 */

// 基础
export { default as UiButton } from './UiButton.vue'
export { default as UiInput } from './UiInput.vue'
export { default as UiNumberInput } from './UiNumberInput.vue'
export { default as UiSelect } from './UiSelect.vue'
export { default as UiCheckbox } from './UiCheckbox.vue'
export { default as UiSwitch } from './UiSwitch.vue'
export { default as UiSegment } from './UiSegment.vue'
export { default as UiTag } from './UiTag.vue'
export { default as UiBadge } from './UiBadge.vue'
export { default as UiDivider } from './UiDivider.vue'
export { default as UiSkeleton } from './UiSkeleton.vue'
export { default as UiSpinner } from './UiSpinner.vue'
export { default as UiLoading } from './UiLoading.vue'

// 浮层
export { default as UiModal } from './UiModal.vue'
export { default as UiDrawer } from './UiDrawer.vue'
export { default as UiPopover } from './UiPopover.vue'
export { default as UiTooltip } from './UiTooltip.vue'
export { default as UiDropdown } from './UiDropdown.vue'
export { default as UiConfirm } from './UiConfirm.vue'

// 数据
export { default as DataGrid } from './DataGrid.vue'
export { default as UiPagination } from './UiPagination.vue'

// 重输入
export { default as UiDateRange } from './UiDateRange.vue'
export { default as UiTimeField } from './UiTimeField.vue'
export { default as UiFileDrop } from './UiFileDrop.vue'

// 类型
export type { GridColumn, GridColumns, GridSortState, SortOrder } from './DataGrid.vue'
export type { SelectOptionItem } from './UiSelect.vue'
export type { SegmentOption } from './UiSegment.vue'
export type { DropdownOption } from './UiDropdown.vue'
export type { Placement } from './useAnchoredLayer'
