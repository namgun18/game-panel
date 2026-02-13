<template>
  <v-container>
    <h1 class="text-h4 mb-4 font-weight-bold" style="color:#E6EDF3;">게임 신청 관리</h1>

    <v-chip-group v-model="statusFilter" mandatory class="mb-4">
      <v-chip value="" variant="tonal">전체</v-chip>
      <v-chip value="pending" color="warning" variant="tonal">대기</v-chip>
      <v-chip value="approved" color="success" variant="tonal">승인</v-chip>
      <v-chip value="rejected" color="error" variant="tonal">거절</v-chip>
    </v-chip-group>

    <v-card style="border:1px solid rgba(88,166,255,0.15);">
      <v-table class="bg-transparent">
        <thead>
          <tr>
            <th style="color:#8B949E;">신청일</th>
            <th style="color:#8B949E;">신청자</th>
            <th style="color:#8B949E;">게임</th>
            <th style="color:#8B949E;">인원</th>
            <th style="color:#8B949E;">희망 시간대</th>
            <th style="color:#8B949E;">상태</th>
            <th style="color:#8B949E;">액션</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in requests" :key="r.id">
            <td>{{ formatDate(r.created_at) }}</td>
            <td class="font-weight-medium">{{ r.requester_name }}</td>
            <td>{{ r.game_name }}</td>
            <td>{{ r.player_count }}명</td>
            <td>{{ r.preferred_time || '-' }}</td>
            <td>
              <v-chip :color="statusColor(r.status)" size="small" variant="tonal">{{ statusLabel(r.status) }}</v-chip>
            </td>
            <td>
              <template v-if="r.status === 'pending'">
                <v-btn size="small" color="success" variant="tonal" class="mr-1" @click="review(r.id, 'approved')">
                  승인
                </v-btn>
                <v-btn size="small" color="error" variant="tonal" @click="review(r.id, 'rejected')">
                  거절
                </v-btn>
              </template>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '../api'

const requests = ref([])
const statusFilter = ref('')

async function fetchRequests() {
  const params = statusFilter.value ? { status_filter: statusFilter.value } : {}
  const res = await api.get('/api/game-requests/', { params })
  requests.value = res.data
}

async function review(id, status) {
  const notes = status === 'rejected' ? prompt('거절 사유 (선택):') : null
  try {
    await api.patch(`/api/game-requests/${id}`, {
      status,
      admin_notes: notes,
    })
    await fetchRequests()
  } catch (e) {
    alert(e.response?.data?.detail || '처리 실패')
  }
}

function statusColor(s) {
  return { pending: 'warning', approved: 'success', rejected: 'error' }[s] || 'grey'
}

function statusLabel(s) {
  return { pending: '대기', approved: '승인', rejected: '거절' }[s] || s
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ko-KR')
}

watch(statusFilter, fetchRequests)
onMounted(fetchRequests)
</script>
