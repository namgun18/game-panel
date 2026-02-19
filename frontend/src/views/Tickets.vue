<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8">

        <!-- 문의 폼 -->
        <v-card class="mb-6" style="border:1px solid rgba(88,166,255,0.15);">
          <v-card-title class="text-h5 font-weight-bold" style="color:#E6EDF3;">🎫 문의하기</v-card-title>
          <v-card-subtitle style="color:#8B949E;">게임 서버 관련 문의를 접수하세요</v-card-subtitle>

          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field :model-value="auth.user?.display_name || auth.user?.username"
                  label="닉네임" readonly disabled prepend-inner-icon="mdi-account" />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select v-model="form.container_name" :items="containerOptions"
                  label="관련 서버 (선택사항)" prepend-inner-icon="mdi-server"
                  clearable :loading="containersLoading"
                  hint="문제가 발생한 서버를 선택하세요" persistent-hint />
              </v-col>
              <v-col cols="12">
                <v-text-field v-model="form.title" label="제목" counter="200" maxlength="200"
                  prepend-inner-icon="mdi-format-title" placeholder="문의 제목을 입력하세요" />
              </v-col>
              <v-col cols="12">
                <v-textarea v-model="form.description" label="내용" rows="4"
                  placeholder="문의 내용을 자세히 적어주세요" />
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions class="px-4 pb-4">
            <v-spacer />
            <v-btn color="primary" size="large" :loading="submitLoading" @click="submit">
              <v-icon start>mdi-send</v-icon> 접수하기
            </v-btn>
          </v-card-actions>

          <v-alert v-if="success" type="success" variant="tonal" class="ma-4">
            문의가 접수되었습니다! 관리자 확인 후 답변드리겠습니다.
          </v-alert>
          <v-alert v-if="error" type="error" variant="tonal" class="ma-4">{{ error }}</v-alert>
        </v-card>

        <!-- 내 문의 내역 -->
        <v-card style="border:1px solid rgba(88,166,255,0.15);">
          <v-card-title class="d-flex align-center" style="color:#E6EDF3;">
            📋 내 문의 내역
            <v-spacer />
            <v-btn icon="mdi-refresh" variant="text" color="primary" size="small"
              @click="fetchMyTickets" :loading="listLoading" />
          </v-card-title>
          <v-card-text>
            <div v-if="myTickets.length">
              <v-card v-for="t in myTickets" :key="t.id" class="mb-3 pa-3"
                variant="outlined" style="border-color:rgba(88,166,255,0.1);">
                <div class="d-flex align-center mb-2">
                  <strong class="text-h6" style="color:#E6EDF3;">{{ t.title }}</strong>
                  <v-spacer />
                  <v-chip :color="statusColor(t.status)" size="small" variant="tonal">
                    {{ t.status_label }}
                  </v-chip>
                </div>
                <div class="text-caption mb-2" style="color:#8B949E;">
                  {{ t.container_name ? t.container_name + ' · ' : '' }}{{ formatDate(t.created_at) }}
                </div>
                <div class="text-body-2 mb-2" style="color:#C9D1D9; white-space: pre-wrap;">{{ t.description }}</div>

                <!-- 관리자 답변 -->
                <v-sheet v-if="t.admin_reply"
                  style="background:#0d2b1a;border:1px solid rgba(102,187,106,0.2);" class="pa-3 rounded-lg mt-2">
                  <div class="text-caption mb-1" style="color:#66BB6A;">
                    💬 관리자 답변
                    <span v-if="t.replied_by_name" style="color:#8B949E;"> — {{ t.replied_by_name }}</span>
                    <span v-if="t.replied_at" style="color:#8B949E;"> · {{ formatDate(t.replied_at) }}</span>
                  </div>
                  <div style="color:#C9D1D9; white-space: pre-wrap;">{{ t.admin_reply }}</div>
                </v-sheet>
              </v-card>
            </div>
            <v-alert v-else type="info" variant="tonal">
              아직 문의 내역이 없습니다.
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
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()

const form = reactive({
  container_name: null,
  title: '',
  description: '',
})

const submitLoading = ref(false)
const listLoading = ref(false)
const containersLoading = ref(false)
const success = ref(false)
const error = ref('')
const myTickets = ref([])
const containerOptions = ref([])

async function fetchContainers() {
  containersLoading.value = true
  try {
    const res = await api.get('/api/tickets/containers')
    containerOptions.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    containersLoading.value = false
  }
}

async function submit() {
  if (!form.title.trim()) {
    error.value = '제목은 필수입니다'
    return
  }
  if (!form.description.trim()) {
    error.value = '내용은 필수입니다'
    return
  }

  submitLoading.value = true
  error.value = ''
  success.value = false

  try {
    await api.post('/api/tickets/', {
      container_name: form.container_name || null,
      title: form.title,
      description: form.description,
    })
    success.value = true
    Object.assign(form, { container_name: null, title: '', description: '' })
    await fetchMyTickets()
  } catch (e) {
    error.value = e.response?.data?.detail || '접수 실패'
  } finally {
    submitLoading.value = false
  }
}

async function fetchMyTickets() {
  listLoading.value = true
  try {
    const res = await api.get('/api/tickets/my')
    myTickets.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    listLoading.value = false
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
  return new Date(iso).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

onMounted(() => {
  fetchContainers()
  fetchMyTickets()
})
</script>
