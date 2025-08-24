<template>
  <div class="rom-verification">
    <div class="verification-header">
      <h2>ROM Ownership Verification</h2>
      <p>Upload your ROM files to verify ownership and unlock access to games</p>
    </div>

    <!-- Upload Section -->
    <div class="upload-section" v-if="!currentVerification">
      <h3>Verify ROM Ownership</h3>
      <div class="rom-selector">
        <label for="rom-select">Select ROM to verify:</label>
        <select id="rom-select" v-model="selectedRomId" @change="onRomSelect">
          <option value="">Choose a ROM...</option>
          <option 
            v-for="rom in availableRoms" 
            :key="rom.id" 
            :value="rom.id"
          >
            {{ rom.name }} ({{ rom.platform }})
          </option>
        </select>
      </div>

      <div v-if="selectedRomId" class="upload-form">
        <div class="file-upload">
          <label for="rom-file">Upload ROM file:</label>
          <input 
            type="file" 
            id="rom-file" 
            @change="onFileSelect" 
            accept=".zip,.7z,.iso,.bin,.cue,.gba,.nds,.3ds,.cia"
            ref="fileInput"
          />
          <small>Supported formats: ZIP, 7Z, ISO, BIN, CUE, GBA, NDS, 3DS, CIA</small>
        </div>

        <div class="upload-actions">
          <button 
            @click="uploadROM" 
            :disabled="!selectedFile || uploading"
            class="btn btn-primary"
          >
            <span v-if="uploading">Uploading...</span>
            <span v-else>Upload for Verification</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Current Verification Status -->
    <div v-if="currentVerification" class="verification-status">
      <h3>Verification Status</h3>
      <div class="status-card" :class="currentVerification.status">
        <div class="status-header">
          <span class="status-badge">{{ currentVerification.status.toUpperCase() }}</span>
          <span class="rom-name">{{ currentVerification.rom_name }}</span>
        </div>
        
        <div class="status-details">
          <p><strong>Uploaded:</strong> {{ formatDate(currentVerification.uploaded_at) }}</p>
          <p><strong>Expires:</strong> {{ formatDate(currentVerification.expires_at) }}</p>
          
          <div v-if="currentVerification.verified_at">
            <p><strong>Verified:</strong> {{ formatDate(currentVerification.verified_at) }}</p>
            <p v-if="currentVerification.notes"><strong>Notes:</strong> {{ currentVerification.notes }}</p>
          </div>
          
          <div v-if="currentVerification.status === 'pending' && currentVerification.is_expired">
            <p class="expired-warning">⚠️ Verification expired. Please upload again.</p>
          </div>
        </div>

        <div class="status-actions">
          <button 
            v-if="currentVerification.status === 'pending' && !currentVerification.is_expired"
            @click="resetVerification"
            class="btn btn-secondary"
          >
            Upload New File
          </button>
          <button 
            v-if="currentVerification.status === 'rejected'"
            @click="resetVerification"
            class="btn btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>

    <!-- My Verified ROMs -->
    <div class="verified-roms">
      <h3>My Verified ROMs</h3>
      <div v-if="verifiedRoms.length === 0" class="no-verified">
        <p>No ROMs verified yet. Upload ROM files to get started!</p>
      </div>
      <div v-else class="verified-list">
        <div 
          v-for="rom in verifiedRoms" 
          :key="rom.rom_id"
          class="verified-rom-card"
        >
          <div class="rom-info">
            <h4>{{ rom.rom_name }}</h4>
            <p class="platform">{{ rom.platform }}</p>
            <p class="verified-date">Verified: {{ formatDate(rom.verified_at) }}</p>
            <p v-if="rom.verifier" class="verifier">By: {{ rom.verifier }}</p>
          </div>
          <div class="rom-actions">
            <button class="btn btn-success">Play Game</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Admin Section -->
    <div v-if="isAdmin" class="admin-section">
      <h3>Admin Panel</h3>
      <div class="admin-stats">
        <div class="stat-card">
          <h4>Pending Verifications</h4>
          <p class="stat-number">{{ stats.pending }}</p>
        </div>
        <div class="stat-card">
          <h4>Total Verified</h4>
          <p class="stat-number">{{ stats.verified }}</p>
        </div>
        <div class="stat-card">
          <h4>Rejected</h4>
          <p class="stat-number">{{ stats.rejected }}</p>
        </div>
      </div>

      <div class="pending-verifications">
        <h4>Pending Verifications</h4>
        <div v-if="pendingVerifications.length === 0" class="no-pending">
          <p>No pending verifications</p>
        </div>
        <div v-else class="pending-list">
          <div 
            v-for="verification in pendingVerifications" 
            :key="verification.id"
            class="pending-verification-card"
          >
            <div class="verification-info">
              <h5>{{ verification.rom_name }}</h5>
              <p><strong>User:</strong> {{ verification.username }}</p>
              <p><strong>Platform:</strong> {{ verification.platform }}</p>
              <p><strong>File:</strong> {{ verification.uploaded_file_name }}</p>
              <p><strong>Size:</strong> {{ formatFileSize(verification.uploaded_file_size) }}</p>
              <p><strong>MD5:</strong> <code>{{ verification.uploaded_md5_hash }}</code></p>
              <p><strong>SHA1:</strong> <code>{{ verification.uploaded_sha1_hash }}</code></p>
              <p><strong>Uploaded:</strong> {{ formatDate(verification.uploaded_at) }}</p>
              <p><strong>Expires:</strong> {{ formatDate(verification.expires_at) }}</p>
            </div>
            
            <div class="verification-actions">
              <div class="action-buttons">
                <button 
                  @click="approveVerification(verification.id)"
                  class="btn btn-success"
                  :disabled="!verification.can_verify"
                >
                  Approve
                </button>
                <button 
                  @click="rejectVerification(verification.id)"
                  class="btn btn-danger"
                  :disabled="!verification.can_verify"
                >
                  Reject
                </button>
              </div>
              <div class="notes-input">
                <label for="notes">Notes:</label>
                <textarea 
                  id="notes" 
                  v-model="verificationNotes[verification.id]"
                  placeholder="Optional notes..."
                  rows="3"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCollectionsStore } from '@/stores/collections'

// Store
const authStore = useAuthStore()
const collectionsStore = useCollectionsStore()

// Reactive data
const selectedRomId = ref('')
const selectedFile = ref(null)
const uploading = ref(false)
const currentVerification = ref(null)
const verifiedRoms = ref([])
const pendingVerifications = ref([])
const stats = ref({ pending: 0, verified: 0, rejected: 0, expired: 0 })
const verificationNotes = ref({})

// Computed properties
const isAdmin = computed(() => authStore.user?.role === 'admin')
const availableRoms = computed(() => collectionsStore.roms || [])

// Methods
const onRomSelect = () => {
  selectedFile.value = null
  if (selectedRomId.value) {
    checkVerificationStatus(selectedRomId.value)
  }
}

const onFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

const uploadROM = async () => {
  if (!selectedFile.value || !selectedRomId.value) return

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('rom_file', selectedFile.value)

    const response = await fetch(`/api/rom-verification/upload/${selectedRomId.value}`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      const result = await response.json()
      await checkVerificationStatus(selectedRomId.value)
      alert('ROM uploaded successfully for verification!')
    } else {
      const error = await response.json()
      alert(`Upload failed: ${error.detail}`)
    }
  } catch (error) {
    console.error('Upload error:', error)
    alert('Upload failed. Please try again.')
  } finally {
    uploading.value = false
  }
}

const checkVerificationStatus = async (romId) => {
  try {
    const response = await fetch(`/api/rom-verification/status/${romId}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      const result = await response.json()
      if (result.status !== 'none') {
        currentVerification.value = {
          ...result,
          rom_name: availableRoms.value.find(r => r.id === parseInt(romId))?.name || 'Unknown ROM'
        }
      } else {
        currentVerification.value = null
      }
    }
  } catch (error) {
    console.error('Error checking verification status:', error)
  }
}

const resetVerification = () => {
  currentVerification.value = null
  selectedRomId.value = ''
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const loadVerifiedRoms = async () => {
  try {
    const response = await fetch('/api/rom-verification/my-verified', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      verifiedRoms.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading verified ROMs:', error)
  }
}

const loadPendingVerifications = async () => {
  if (!isAdmin.value) return

  try {
    const response = await fetch('/api/rom-verification/pending', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      pendingVerifications.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading pending verifications:', error)
  }
}

const loadStats = async () => {
  if (!isAdmin.value) return

  try {
    const response = await fetch('/api/rom-verification/stats', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      stats.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

const approveVerification = async (verificationId) => {
  const notes = verificationNotes.value[verificationId] || ''
  
  try {
    const formData = new FormData()
    formData.append('approved', 'true')
    formData.append('notes', notes)

    const response = await fetch(`/api/rom-verification/verify/${verificationId}`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      await loadPendingVerifications()
      await loadStats()
      await loadVerifiedRoms()
      alert('Verification approved!')
    } else {
      const error = await response.json()
      alert(`Approval failed: ${error.detail}`)
    }
  } catch (error) {
    console.error('Error approving verification:', error)
    alert('Approval failed. Please try again.')
  }
}

const rejectVerification = async (verificationId) => {
  const notes = verificationNotes.value[verificationId] || ''
  
  try {
    const formData = new FormData()
    formData.append('approved', 'false')
    formData.append('notes', notes)

    const response = await fetch(`/api/rom-verification/verify/${verificationId}`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      await loadPendingVerifications()
      await loadStats()
      alert('Verification rejected!')
    } else {
      const error = await response.json()
      alert(`Rejection failed: ${error.detail}`)
    }
  } catch (error) {
    console.error('Error rejecting verification:', error)
    alert('Rejection failed. Please try again.')
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Template refs
const fileInput = ref(null)

// Lifecycle
onMounted(async () => {
  await loadVerifiedRoms()
  if (isAdmin.value) {
    await loadPendingVerifications()
    await loadStats()
  }
})
</script>

<style scoped>
.rom-verification {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.verification-header {
  text-align: center;
  margin-bottom: 30px;
}

.verification-header h2 {
  color: #333;
  margin-bottom: 10px;
}

.verification-header p {
  color: #666;
  font-size: 16px;
}

.upload-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.rom-selector {
  margin-bottom: 20px;
}

.rom-selector label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.rom-selector select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.upload-form {
  border-top: 1px solid #ddd;
  padding-top: 20px;
}

.file-upload {
  margin-bottom: 20px;
}

.file-upload label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.file-upload input[type="file"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.file-upload small {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 12px;
}

.upload-actions {
  text-align: center;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #1e7e34;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.verification-status {
  margin-bottom: 30px;
}

.status-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-card.pending {
  border-left: 4px solid #ffc107;
}

.status-card.verified {
  border-left: 4px solid #28a745;
}

.status-card.rejected {
  border-left: 4px solid #dc3545;
}

.status-card.expired {
  border-left: 4px solid #6c757d;
}

.status-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.status-badge {
  background: #333;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  margin-right: 15px;
}

.rom-name {
  font-size: 18px;
  font-weight: 600;
}

.status-details p {
  margin: 8px 0;
  color: #555;
}

.expired-warning {
  color: #dc3545;
  font-weight: 600;
}

.status-actions {
  margin-top: 20px;
  text-align: center;
}

.verified-roms {
  margin-bottom: 30px;
}

.verified-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.verified-rom-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.rom-info h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.platform {
  color: #666;
  font-size: 14px;
  margin: 5px 0;
}

.verified-date, .verifier {
  color: #888;
  font-size: 12px;
  margin: 5px 0;
}

.rom-actions {
  margin-top: 15px;
  text-align: center;
}

.admin-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.admin-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #007bff;
  margin: 10px 0;
}

.pending-verifications {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.pending-verification-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.verification-info h5 {
  margin: 0 0 15px 0;
  color: #333;
}

.verification-info p {
  margin: 5px 0;
  color: #555;
}

.verification-info code {
  background: #f8f9fa;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

.verification-actions {
  margin-top: 20px;
  border-top: 1px solid #ddd;
  padding-top: 20px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.notes-input label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
}

.notes-input textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
}

.no-verified, .no-pending {
  text-align: center;
  color: #666;
  padding: 40px;
}
</style>
