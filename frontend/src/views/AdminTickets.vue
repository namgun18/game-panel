<template>
  <v-container>
    <h1 class="text-h4 mb-4 font-weight-bold" style="color:#E6EDF3;">문의 관리</h1>

    <v-chip-group v-model="statusFilter" mandatory class="mb-4">
      <v-chip value="" variant="tonal">전체</v-chip>
      <v-chip v-for="(label, key) in statusLabels" :key="key" :value="key"
        :color="statusColor(key)" variant="tonal">{{ label }}</v-chip>
    </v-chip-group>

    <v-card style="border:1px solid rgba(88,166,255,0.15);">
      <v-table class="bg-transparent">
        <thead>
          <tr>
            <th style="color:#8B949E;">접수일</th>
            <th style="color:#8B949E;">문의자</th>
            <th style="color:#8B949E;">서버</th>
            <th style="color:#8B949E;">제목</th>
            <th style="color:#8B949E;">상태</th>
            <th style="color:#8B949E;">액션</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in filteredTickets" :key="t.id">
            <td>{{ formatDate(t.created_at) }}</td>
            <td class="font-weight-medium">{{ t.requester_name }}</td>
            <td>{{ t.container_name || '-' }}</td>
            <td>{{ t.title }}</td>
            <td>
              <v-chip :color="statusColor(t.status)" size="small" variant="tonal">
                {{ t.status_label }}
              </v-chip>
            </td>
            <td>
              <v-btn size="small" color="primary" variant="tonal" @click="openDetailDialog(t)">
                상세/답변
              </v-btn>
            </td>
          </tr>
          <tr v-if="!filteredTickets.length">
            <td colspan="6" class="text-center pa-4" style="color:#8B949E;">문의가 없습니다</td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <!-- ═══ 상세/답변 다이얼로그 ═══ -->
    <v-dialog v-model="detailDialog" max-width="700" persistent>
      <v-card class="pa-4" style="border:1px solid rgba(88,166,255,0.15);">
        <v-card-title class="text-h6" style="color:#58A6FF;">
          🎫 {{ sel?.title }}
        </v-card-title>
        <v-card-subtitle>
          {{ sel?.requester_name }}
          <span v-if="sel?.container_name"> · {{ sel.container_name }}</span>
          · {{ formatDate(sel?.created_at) }}
          · <v-chip :color="statusColor(sel?.status)" size="x-small" variant="tonal">{{ sel?.status_label }}</v-chip>
        </v-card-subtitle>

        <v-card-text>
          <!-- 문의 내용 -->
          <v-sheet style="background:#161B22;border:1px solid rgba(88,166,255,0.1);"
            class="pa-4 rounded-lg mb-4">
            <div class="text-caption mb-1" style="color:#8B949E;">문의 내용</div>
            <div style="color:#C9D1D9; white-space: pre-wrap;">{{ sel?.description }}</div>
          </v-sheet>

          <!-- 상태 변경 -->
          <v-select v-model="replyForm.status" :items="statusOptions" item-title="label" item-value="key"
            label="상태 변경" prepend-inner-icon="mdi-swap-horizontal" class="mb-2" />

          <!-- 답변 -->
          <v-textarea v-model="replyForm.admin_reply" label="관리자 답변" rows="3"
            :placeholder="sel?.admin_reply ? '기존 답변을 수정하려면 입력' : '답변 내용을 입력하세요'" />

          <!-- 기존 답변 표시 -->
          <v-sheet v-if="sel?.admin_reply && !replyForm.admin_reply"
            style="background:#0d2b1a;border:1px solid rgba(102,187,106,0.2);" class="pa-3 rounded-lg mt-2">
            <div class="text-caption mb-1" style="color:#66BB6A;">
              기존 답변
              <span v-if="sel.replied_by_name" style="color:#8B949E;"> — {{ sel.replied_by_name }}</span>
            </div>
            <div style="color:#C9D1D9; white-space: pre-wrap;">{{ sel.admin_reply }}</div>
          </v-sheet>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="detailDialog = false">닫기</v-btn>
          <v-btn color="primary" variant="elevated" :loading="updateLoading" @click="submitUpdate">
            <v-icon start>mdi-check</v-icon> 저장 및 알림 발송
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'

const tickets = ref([])
const statusFilter = ref('')
const sel = ref(null)
const updateLoading = ref(false)
const detailDialog = ref(false)

const replyForm = reactive({
  status: '',
  admin_reply: '',
})

const statusLabels = {
  submitted: '접수', acknowledged: '확인',
  replied: '답변완료', resolved: '완료',
}

const statusOptions = [
  { key: 'submitted', label: '접수' },
  { key: 'acknowledged', label: '확인' },
  { key: 'replied', label: '답변완료' },
  { key: 'resolved', label: '완료' },
]

const filteredTickets = computed(() => {
  if (!statusFilter.value) return tickets.value
  return tickets.value.filter(t => t.status === statusFilter.value)
})

async function fetchTickets() {
  try {
    const res = await api.get('/api/tickets/')
    tickets.value = res.data
  } catch (e) {
    console.error(e)
  }
}

function openDetailDialog(t) {
  sel.value = t
  replyForm.status = t.status
  replyForm.admin_reply = ''
  detailDialog.value = true
}

async function submitUpdate() {
  if (!sel.value) return
  updateLoading.value = true

  try {
    const payload = {}
    if (replyForm.status !== sel.value.status) {
      payload.status = replyForm.status
    }
    if (replyForm.admin_reply.trim()) {
      payload.admin_reply = replyForm.admin_reply
      // 답변 입력 시 자동으로 replied 상태로 변경
      if (!payload.status && sel.value.status === 'submitted') {
        payload.status = 'replied'
      } else if (!payload.status && sel.value.status === 'acknowledged') {
        payload.status = 'replied'
      }
    }

    if (Object.keys(payload).length === 0) {
      detailDialog.value = false
      return
    }

    await api.patch(`/api/tickets/${sel.value.id}`, payload)
    detailDialog.value = false
    await fetchTickets()
  } catch (e) {
    alert(e.response?.data?.detail || '처리 실패')
  } finally {
    updateLoading.value = false
  }
}

function statusColor(s) {
  const map = {
    submitted: 'info', acknowledged: 'warning', replied: 'success', resolved: 'grey',
  }
  return map[s] || 'grey'
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ko-KR')
}

onMounted(fetchTickets)
</script>
