<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8">

        <!-- 신청 폼 -->
        <v-card class="mb-6" style="border:1px solid rgba(88,166,255,0.15);">
          <v-card-title class="text-h5 font-weight-bold" style="color:#E6EDF3;">🎮 게임 서버 신청</v-card-title>
          <v-card-subtitle style="color:#8B949E;">원하는 게임 서버를 신청하세요</v-card-subtitle>

          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field v-model="form.requester_name" label="이름 / 닉네임" required />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field v-model="form.game_name" label="게임 이름" required
                  placeholder="예: Minecraft, Valheim, Palworld" />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field v-model.number="form.player_count" label="예상 인원" type="number" min="1" />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field v-model="form.preferred_time" label="희망 운영 시간대"
                  placeholder="예: 평일 저녁 8시~12시" />
              </v-col>
              <v-col cols="12">
                <v-textarea v-model="form.notes" label="비고" rows="2"
                  placeholder="추가 요청사항이 있으면 적어주세요" />
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions class="px-4 pb-4">
            <v-spacer />
            <v-btn color="primary" size="large" :loading="submitLoading" @click="submit">
              <v-icon start>mdi-send</v-icon> 신청하기
            </v-btn>
          </v-card-actions>

          <v-alert v-if="success" type="success" variant="tonal" class="ma-4">
            신청이 접수되었습니다! 관리자 검토 후 안내드리겠습니다.
          </v-alert>
          <v-alert v-if="error" type="error" variant="tonal" class="ma-4">{{ error }}</v-alert>
        </v-card>

        <!-- 내 신청 내역 -->
        <v-card style="border:1px solid rgba(88,166,255,0.15);">
          <v-card-title class="d-flex align-center" style="color:#E6EDF3;">
            📋 내 신청 내역
            <v-spacer />
            <v-btn icon="mdi-refresh" variant="text" color="primary" size="small"
              @click="fetchMyRequests" :loading="listLoading" />
          </v-card-title>
          <v-card-text>
            <v-table v-if="myRequests.length" class="bg-transparent">
              <thead>
                <tr>
                  <th style="color:#8B949E;">게임</th>
                  <th style="color:#8B949E;">인원</th>
                  <th style="color:#8B949E;">상태</th>
                  <th style="color:#8B949E;">관리자 메모</th>
                  <th style="color:#8B949E;">신청일</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in myRequests" :key="r.id">
                  <td class="font-weight-medium">{{ r.game_name }}</td>
                  <td>{{ r.player_count }}명</td>
                  <td>
                    <v-chip :color="statusColor(r.status)" size="small" variant="tonal">
                      {{ statusLabel(r.status) }}
                    </v-chip>
                  </td>
                  <td style="color:#8B949E;">{{ r.admin_notes || '-' }}</td>
                  <td style="color:#8B949E;">{{ formatDate(r.created_at) }}</td>
                </tr>
              </tbody>
            </v-table>
            <v-alert v-else type="info" variant="tonal">
              아직 신청 내역이 없습니다.
            </v-alert>
          </v-card-text>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'

const form = reactive({
  requester_name: '',
  requester_email: '',
  game_name: '',
  player_count: 1,
  preferred_time: '',
  notes: '',
})

const submitLoading = ref(false)
const listLoading = ref(false)
const success = ref(false)
const error = ref('')
const myRequests = ref([])

async function submit() {
  if (!form.requester_name || !form.game_name) {
    error.value = '이름과 게임 이름은 필수입니다'
    return
  }

  submitLoading.value = true
  error.value = ''
  success.value = false

  try {
    await api.post('/api/game-requests/', form)
    success.value = true
    Object.assign(form, {
      requester_name: '', requester_email: '', game_name: '',
      player_count: 1, preferred_time: '', notes: '',
    })
    await fetchMyRequests()
  } catch (e) {
    error.value = e.response?.data?.detail || '신청 실패'
  } finally {
    submitLoading.value = false
  }
}

async function fetchMyRequests() {
  listLoading.value = true
  try {
    const res = await api.get('/api/game-requests/my')
    myRequests.value = res.data
  } catch (e) {
    console.error('신청 내역 조회 실패:', e)
  } finally {
    listLoading.value = false
  }
}

function statusColor(s) {
  return s === 'approved' ? 'success' : s === 'rejected' ? 'error' : 'warning'
}

function statusLabel(s) {
  return s === 'approved' ? '승인' : s === 'rejected' ? '거절' : '대기중'
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

onMounted(fetchMyRequests)
</script>
