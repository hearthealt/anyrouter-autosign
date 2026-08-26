<template>
  <UiModal v-model:show="visible" :width="860" :mask-closable="false">
    <div class="batch-import-modal">
      <div class="modal-head">
        <div>
          <h3>批量导入账号</h3>
          <p>支持粘贴 JSON 或上传 CSV，逐条校验并返回每条结果</p>
        </div>
        <UiButton text @click="close">
          <X :size="16" />
        </UiButton>
      </div>

      <div class="modal-body">
        <div class="hint">
          <Info :size="14" />
          <span>
            字段支持 <code>platform_id</code> / <code>platform</code>、
            <code>group_id</code> / <code>group</code>，账号凭证字段与单个添加账号保持一致。
            访问出口字段支持 <code>proxy_mode</code>、<code>proxy_url</code>。
          </span>
        </div>

        <div class="field-grid">
          <div class="field">
            <label>默认平台（可选）</label>
            <UiSelect
              v-model:value="fallbackPlatformId"
              :options="platformOptions"
              size="small"
              clearable
              placeholder="当数据里未写 platform 时使用"
            />
          </div>
          <div class="field">
            <label>默认分组（可选）</label>
            <UiSelect
              v-model:value="fallbackGroupId"
              :options="groupOptions"
              size="small"
              clearable
              placeholder="当数据里未写 group 时使用"
            />
          </div>
        </div>

        <UiSegment v-model:value="mode" :options="[{ label: '粘贴 JSON', value: 'json' }, { label: '上传 CSV', value: 'csv' }]" />
        <div v-show="mode === 'json'" class="tab-panel">
            <div class="import-panel">
              <div class="panel-headline">
                <span>JSON 数组或 <code>{\"items\": [...]}</code> 都支持</span>
                <UiButton text size="small" @click="fillExample">
                  填充示例
                </UiButton>
              </div>
              <UiInput
                v-model:value="jsonText"
                type="textarea"
                :rows="14"
                placeholder="[{ &quot;platform&quot;: &quot;AnyRouter&quot;, &quot;login_username&quot;: &quot;demo@example.com&quot;, &quot;login_password&quot;: &quot;secret&quot; }, { &quot;platform&quot;: &quot;某 HTTP 平台&quot;, &quot;external_user_id&quot;: &quot;user-001&quot;, &quot;auth_type&quot;: &quot;bearer&quot;, &quot;auth_data&quot;: { &quot;token&quot;: &quot;...&quot; } }]"
              />
            </div>
                  </div>
        <div v-show="mode === 'csv'" class="tab-panel">
            <div class="import-panel">
              <div class="upload-card">
                <div class="upload-copy">
                  <div class="upload-title">CSV 表头</div>
                  <div class="upload-desc">
                    <code>platform_id</code>, <code>platform</code>, <code>group_id</code>, <code>group</code>,
                    <code>user_id</code>, <code>session_cookie</code>, <code>external_user_id</code>, <code>username</code>,
                    <code>display_name</code>, <code>auth_type</code>, <code>auth_data</code>, <code>login_username</code>, <code>login_password</code>,
                    <code>proxy_mode</code>, <code>proxy_url</code>
                  </div>
                </div>
                <UiFileDrop accept=".csv,text/csv" @select="handleCsvFileChange">
                  <UiButton size="small" type="primary">
                    <template #icon><CloudUpload :size="14" /></template>
                    选择 CSV
                  </UiButton>
                </UiFileDrop>
              </div>

              <div v-if="csvFileName" class="file-meta">
                <span>{{ csvFileName }}</span>
                <span>{{ csvRowCount }} 条记录</span>
              </div>

              <UiInput
                :value="csvPreview"
                type="textarea"
                :rows="12"
                readonly
                placeholder="选择 CSV 后会在这里显示内容预览"
              />
            </div>
                  </div>

        <div v-if="summary" class="summary-row">
          <div class="summary-card">
            <span class="summary-label">总条数</span>
            <strong>{{ summary.total }}</strong>
          </div>
          <div class="summary-card success">
            <span class="summary-label">成功</span>
            <strong>{{ summary.success_count }}</strong>
          </div>
          <div class="summary-card error">
            <span class="summary-label">失败</span>
            <strong>{{ summary.fail_count }}</strong>
          </div>
        </div>

        <div v-if="results.length > 0" class="result-list">
          <div
            v-for="result in results"
            :key="`${result.index}-${result.username || result.message}`"
            class="result-item"
            :class="{ success: result.success, error: !result.success }"
          >
            <div class="result-main">
              <div class="result-head">
                <span class="result-index">#{{ result.index + 1 }}</span>
                <UiTag size="small" :type="result.success ? 'success' : 'error'" :bordered="false">
                  {{ result.success ? '成功' : '失败' }}
                </UiTag>
                <span v-if="result.username" class="result-username">{{ result.username }}</span>
              </div>
              <div class="result-message">{{ result.message }}</div>
            </div>
            <div v-if="result.account_id" class="result-side">ID {{ result.account_id }}</div>
          </div>
        </div>
      </div>

      <div class="modal-foot">
        <UiButton @click="close">关闭</UiButton>
        <UiButton type="primary" :loading="importing" @click="handleSubmit">
          开始导入
        </UiButton>
      </div>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { UiFileDrop, UiButton, UiInput, UiModal, UiSegment, UiSelect, UiTag } from '../../ui'
import { computed, ref } from 'vue'
import { CloudUpload, Info, X } from 'lucide-vue-next'
import { accountApi } from '../../api'
import type {
  AccountGroup,
  BatchImportItem,
  BatchImportResponse,
  BatchImportResultItem,
  AccountProxyMode,
  Platform,
  SelectOption,
} from '../../types'

const props = defineProps<{
  show: boolean
  platforms: Platform[]
  groups: AccountGroup[]
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  imported: [successCount: number]
}>()

const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const mode = ref<'json' | 'csv'>('json')
const jsonText = ref('')
const csvText = ref('')
const csvFileName = ref('')
const csvRowCount = ref(0)
const fallbackPlatformId = ref<number | null>(null)
const fallbackGroupId = ref<number | null>(null)
const importing = ref(false)
const summary = ref<BatchImportResponse | null>(null)
const results = ref<BatchImportResultItem[]>([])

const platformOptions = computed<SelectOption<number>[]>(() =>
  props.platforms.map(platform => ({
    label: platform.is_default ? `${platform.name} (默认)` : platform.name,
    value: platform.id
  }))
)

const groupOptions = computed<SelectOption<number>[]>(() =>
  props.groups.map(group => ({
    label: group.name,
    value: group.id
  }))
)

const csvPreview = computed(() => {
  if (!csvText.value) return ''
  const lines = csvText.value.split(/\r?\n/).slice(0, 12)
  return lines.join('\n')
})

const normalizeOptionalString = (value: unknown): string | undefined => {
  if (value == null) return undefined
  const normalized = String(value).trim()
  return normalized || undefined
}

const normalizeProxyMode = (value: unknown, index: number): AccountProxyMode => {
  const normalized = normalizeOptionalString(value)?.toLowerCase()
  if (!normalized) return 'direct'
  if (normalized === 'global') return 'direct'
  if (normalized === 'direct' || normalized === 'custom') {
    return normalized
  }
  throw new Error(`第 ${index + 1} 条的 proxy_mode 无效`)
}

const resolveNamedPlatform = (name: string) =>
  props.platforms.find(platform =>
    platform.name.trim().toLowerCase() === name.trim().toLowerCase()
    || platform.base_url.trim().toLowerCase() === name.trim().toLowerCase()
  )

const resolveNamedGroup = (name: string) =>
  props.groups.find(group => group.name.trim().toLowerCase() === name.trim().toLowerCase())

const resolvePlatformId = (row: Record<string, unknown>, index: number): number => {
  const platformId = normalizeOptionalString(row.platform_id ?? row.platformId)
  if (platformId) {
    const parsed = Number(platformId)
    if (!Number.isInteger(parsed) || parsed <= 0) {
      throw new Error(`第 ${index + 1} 条的 platform_id 无效`)
    }
    return parsed
  }

  const platformName = normalizeOptionalString(row.platform ?? row.platform_name ?? row.platformName)
  if (platformName) {
    const matched = resolveNamedPlatform(platformName)
    if (!matched) {
      throw new Error(`第 ${index + 1} 条的平台 "${platformName}" 不存在`)
    }
    return matched.id
  }

  if (fallbackPlatformId.value) {
    return fallbackPlatformId.value
  }

  throw new Error(`第 ${index + 1} 条缺少 platform_id 或 platform`)
}

const resolveGroupId = (row: Record<string, unknown>, index: number): number | undefined => {
  const groupId = normalizeOptionalString(row.group_id ?? row.groupId)
  if (groupId) {
    const parsed = Number(groupId)
    if (!Number.isInteger(parsed) || parsed <= 0) {
      throw new Error(`第 ${index + 1} 条的 group_id 无效`)
    }
    return parsed
  }

  const groupName = normalizeOptionalString(row.group ?? row.group_name ?? row.groupName)
  if (groupName) {
    const matched = resolveNamedGroup(groupName)
    if (!matched) {
      throw new Error(`第 ${index + 1} 条的分组 "${groupName}" 不存在`)
    }
    return matched.id
  }

  return fallbackGroupId.value || undefined
}

const buildImportItems = (rows: Array<Record<string, unknown>>): BatchImportItem[] => {
  return rows.map((raw, index) => {
    const proxyMode = normalizeProxyMode(raw.proxy_mode ?? raw.proxyMode, index)
    const proxyUrl = normalizeOptionalString(raw.proxy_url ?? raw.proxyUrl)
    if (proxyMode === 'custom' && !proxyUrl) {
      throw new Error(`第 ${index + 1} 条使用 custom 代理时必须填写 proxy_url`)
    }

    const authType = normalizeOptionalString(raw.auth_type ?? raw.authType)?.toLowerCase() as BatchImportItem['auth_type'] | undefined
    const rawAuthData = raw.auth_data ?? raw.authData
    let authData: Record<string, unknown> | undefined
    if (rawAuthData != null && rawAuthData !== '') {
      if (typeof rawAuthData === 'string') {
        try {
          authData = JSON.parse(rawAuthData) as Record<string, unknown>
        } catch (error: any) {
          throw new Error(`第 ${index + 1} 条的 auth_data 不是有效 JSON：${error.message}`)
        }
      } else if (typeof rawAuthData === 'object' && !Array.isArray(rawAuthData)) {
        authData = rawAuthData as Record<string, unknown>
      } else {
        throw new Error(`第 ${index + 1} 条的 auth_data 必须是 JSON 对象`)
      }
    }

    return {
      platform_id: resolvePlatformId(raw, index),
      group_id: resolveGroupId(raw, index),
      user_id: normalizeOptionalString(raw.user_id ?? raw.userId),
      session_cookie: normalizeOptionalString(raw.session_cookie ?? raw.sessionCookie),
      external_user_id: normalizeOptionalString(raw.external_user_id ?? raw.externalUserId),
      username: normalizeOptionalString(raw.username),
      display_name: normalizeOptionalString(raw.display_name ?? raw.displayName),
      login_username: normalizeOptionalString(raw.login_username ?? raw.loginUsername),
      login_password: normalizeOptionalString(raw.login_password ?? raw.loginPassword),
      auth_type: authType,
      auth_data: authData,
      note: normalizeOptionalString(raw.note),
      proxy_mode: proxyMode,
      proxy_url: proxyMode === 'custom' ? proxyUrl : undefined,
    }
  })
}

const parseJsonRows = (): Array<Record<string, unknown>> => {
  if (!jsonText.value.trim()) {
    throw new Error('请先粘贴 JSON 数据')
  }

  const parsed = JSON.parse(jsonText.value)
  const rows = Array.isArray(parsed) ? parsed : parsed?.items
  if (!Array.isArray(rows)) {
    throw new Error('JSON 必须是数组，或包含 items 数组')
  }

  return rows.map((item, index) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      throw new Error(`第 ${index + 1} 条不是对象`)
    }
    return item as Record<string, unknown>
  })
}

const parseCsv = (text: string): string[][] => {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let inQuotes = false

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]

    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i += 1
        } else {
          inQuotes = false
        }
      } else {
        field += char
      }
      continue
    }

    if (char === '"') {
      inQuotes = true
    } else if (char === ',') {
      row.push(field)
      field = ''
    } else if (char === '\n') {
      row.push(field)
      rows.push(row)
      row = []
      field = ''
    } else if (char !== '\r') {
      field += char
    }
  }

  row.push(field)
  if (row.some(cell => cell.trim() !== '')) {
    rows.push(row)
  }

  return rows
}

const parseCsvRows = (): Array<Record<string, unknown>> => {
  if (!csvText.value.trim()) {
    throw new Error('请先上传 CSV 文件')
  }

  const table = parseCsv(csvText.value.replace(/^\uFEFF/, ''))
  if (table.length < 2) {
    throw new Error('CSV 至少需要表头和一条数据')
  }

  const headers = table[0].map((header, index) =>
    (index === 0 ? header.replace(/^\uFEFF/, '') : header).trim()
  )

  if (headers.some(header => !header)) {
    throw new Error('CSV 表头存在空列名')
  }

  return table
    .slice(1)
    .filter(row => row.some(cell => cell.trim() !== ''))
    .map((row, rowIndex) => {
      const record: Record<string, unknown> = {}
      headers.forEach((header, index) => {
        record[header] = row[index] ?? ''
      })
      if (Object.keys(record).length === 0) {
        throw new Error(`第 ${rowIndex + 1} 行为空`)
      }
      return record
    })
}

const fillExample = () => {
  const defaultPlatform = props.platforms.find(platform => platform.is_default) ?? props.platforms[0]
  const firstGroup = props.groups[0]

  jsonText.value = JSON.stringify(
    [
      {
        platform: defaultPlatform?.name || 'AnyRouter',
        group: firstGroup?.name,
        login_username: 'demo@example.com',
        login_password: 'secret-password',
        proxy_mode: 'direct'
      },
      {
        platform_id: defaultPlatform?.id || 1,
        user_id: '123456',
        session_cookie: 'your-session-cookie',
        proxy_mode: 'custom',
        proxy_url: 'http://user:pass@cn-proxy.example.com:8080'
      },
      {
        platform: defaultPlatform?.name || '某 HTTP 平台',
        external_user_id: 'user-001',
        username: 'demo',
        auth_type: 'bearer',
        auth_data: { token: 'your-token' },
        proxy_mode: 'direct'
      }
    ],
    null,
    2
  )
}

const resetState = () => {
  mode.value = 'json'
  jsonText.value = ''
  csvText.value = ''
  csvFileName.value = ''
  csvRowCount.value = 0
  fallbackPlatformId.value = null
  fallbackGroupId.value = null
  summary.value = null
  results.value = []
  importing.value = false
}

const close = () => {
  visible.value = false
  resetState()
}

// UiFileDrop 直接给原生 File
const handleCsvFileChange = async (rawFile: File) => {
  if (!rawFile) return

  try {
    const text = await rawFile.text()
    const rows = parseCsv(text.replace(/^\uFEFF/, ''))
    if (rows.length < 2) {
      throw new Error('CSV 至少需要表头和一条数据')
    }

    csvText.value = text.replace(/^\uFEFF/, '')
    csvFileName.value = rawFile.name
    csvRowCount.value = rows.slice(1).filter(row => row.some(cell => cell.trim() !== '')).length
    mode.value = 'csv'
  } catch (e: any) {
    csvText.value = ''
    csvFileName.value = ''
    csvRowCount.value = 0
    window.$notify(e.message || '读取 CSV 失败', 'error')
  }
}

const handleSubmit = async () => {
  if (props.platforms.length === 0) {
    window.$notify('请先创建平台，再执行批量导入', 'warning')
    return
  }

  importing.value = true
  try {
    const rows = mode.value === 'json' ? parseJsonRows() : parseCsvRows()
    if (rows.length === 0) {
      throw new Error('没有可导入的数据')
    }

    const items = buildImportItems(rows)
    const res: any = await accountApi.batchImport({ items })
    const data = (res.data || {}) as BatchImportResponse

    summary.value = {
      total: data.total || items.length,
      success_count: data.success_count || 0,
      fail_count: data.fail_count || 0,
      results: data.results || []
    }
    results.value = summary.value.results

    if (summary.value.success_count > 0) {
      emit('imported', summary.value.success_count)
    }

    window.$notify(
      res.message || '批量导入完成',
      summary.value.fail_count > 0 ? 'warning' : 'success'
    )
  } catch (e: any) {
    window.$notify(e.message || '批量导入失败', 'error')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.batch-import-modal { display: flex; flex-direction: column; min-width: 0; }

.modal-head,
.modal-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
}

.modal-head {
  border-bottom: 1px solid var(--border-color-light);
}

.modal-head h3 {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
}

.modal-head p {
  margin: 2px 0 0;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  max-height: 78vh;
  overflow-y: auto;
}

.modal-foot {
  justify-content: flex-end;
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.hint {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  line-height: 1.5;
}

.hint code,
.panel-headline code,
.upload-desc code {
  font-family: var(--font-mono);
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.import-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.panel-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.upload-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  background: var(--bg-card);
}

.upload-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.upload-title {
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.upload-desc {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  line-height: 1.5;
}

.file-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-2);
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--spacing-3);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  background: var(--bg-card);
}

.summary-card strong {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  line-height: 1;
}

.summary-card.success strong {
  color: var(--success-color);
}

.summary-card.error strong {
  color: var(--error-color);
}

.summary-label {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.result-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-3);
  align-items: center;
  padding: var(--spacing-3);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  background: var(--bg-card);
}

.result-item.success {
  border-color: rgba(22, 163, 74, 0.22);
}

.result-item.error {
  border-color: rgba(220, 38, 38, 0.22);
}

.result-main {
  min-width: 0;
}

.result-head {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.result-index {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.result-username {
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.result-message {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  word-break: break-word;
}

.result-side {
  font-family: var(--font-mono);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

@media (max-width: 720px) {
  .field-grid,
  .summary-row {
    grid-template-columns: 1fr;
  }

  .upload-card,
  .result-item {
    grid-template-columns: 1fr;
  }

  .upload-card {
    align-items: flex-start;
  }
}
</style>
