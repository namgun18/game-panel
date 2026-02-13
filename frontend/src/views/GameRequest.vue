<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="6">
        <v-card style="border:1px solid rgba(88,166,255,0.15);">
          <v-card-title class="text-h5 font-weight-bold" style="color:#E6EDF3;">🎮 게임 서버 신청</v-card-title>
          <v-card-subtitle style="color:#8B949E;">원하는 게임 서버를 신청하세요</v-card-subtitle>

          <v-card-text>
            <v-text-field v-model="form.requester_name" label="이름 / 닉네임" required />
            <v-text-field v-model="form.requester_email" label="이메일 (선택)" type="email" />
            <v-text-field v-model="form.game_name" label="게임 이름" required
              placeholder="예: Minecraft, Valheim, Palworld" />
            <v-text-field v-model.number="form.player_count" label="예상 인원" type="number" min="1" />
            <v-text-field v-model="form.preferred_time" label="희망 운영 시간대"
              placeholder="예: 평일 저녁 8시~12시" />
            <v-textarea v-model="form.notes" label="비고" rows="3"
              placeholder="추가 요청사항이 있으면 적어주세요" />
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" size="large" :loading="loading" @click="submit">
              신청하기
            </v-btn>
          </v-card-actions>

          <v-alert v-if="success" type="success" variant="tonal" class="ma-4">
            신청이 접수되었습니다! 관리자 검토 후 안내드리겠습니다.
          </v-alert>
          <v-alert v-if="error" type="error" variant="tonal" class="ma-4">
            {{ error }}
          </v-alert>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '../api'

const form = reactive({
  requester_name: '',
  requester_email: '',
  game_name: '',
  player_count: 1,
  preferred_time: '',
  notes: '',
})

const loading = ref(false)
const success = ref(false)
const error = ref('')

async function submit() {
  if (!form.requester_name || !form.game_name) {
    error.value = '이름과 게임 이름은 필수입니다'
    return
  }

  loading.value = true
  error.value = ''
  success.value = false

  try {
    await api.post('/api/game-requests/', form)
    success.value = true
    Object.assign(form, {
      requester_name: '', requester_email: '', game_name: '',
      player_count: 1, preferred_time: '', notes: '',
    })
  } catch (e) {
    error.value = e.response?.data?.detail || '신청 실패'
  } finally {
    loading.value = false
  }
}
</script>
