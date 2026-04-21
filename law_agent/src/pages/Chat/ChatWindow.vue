<template>
    <div class="chat-page">
        <div class="luxury-bg-glow"></div>

        <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, mobile: isMobile }">
            <div class="sidebar-toggle" @click="toggleSidebar">
                <span v-if="sidebarCollapsed">展开面板</span>
                <span v-else>收起控制台</span>
            </div>

            <div class="sidebar-box" v-show="!sidebarCollapsed">
                <div class="panel-header">
                    <span class="gold-text">CONTROL PANEL</span>
                    <h3>智能体配置</h3>
                </div>

                <div class="select-wrapper">
                    <select v-model="selectedAgentName" class="luxury-select">
                        <option disabled value="">— 请选择法律专家 —</option>
                        <option v-for="item in agentList" :key="item.name" :value="item.name">
                            {{ item.name }}
                        </option>
                    </select>
                </div>

                <transition name="fade">
                    <div v-if="selectedAgentName === '合同解释专家'" class="luxury-note">
                        <strong>专家提示：</strong> 提供合同类型、当事人全称及重点条款，将获得更精准的法律推演。
                    </div>
                </transition>

                <!-- <div class="new-session-wrapper">
                    <button class="new-session-btn" @click="clearChat">
                        <span class="icon-plus">＋</span>
                        <span>开启新会话</span>
                    </button>
                </div> -->
            </div>
        </aside>

        <main class="chat-main" :class="{ expanded: sidebarCollapsed }">
            <div class="chat-container">
                <header class="chat-header">
                    <div class="status-indicator" :class="{ active: !loading }"></div>
                    <h1 class="chat-title">法影智芒 <span>| 法律 AI 协作平台</span></h1>
                </header>

                <div class="message-box" ref="messageBox">
                    <div v-for="(msg, idx) in messages" :key="idx" class="message-item" :class="msg.role">
                        <div class="avatar-container">
                            <div class="avatar-glow"></div>
                            <div class="avatar-circle">{{ msg.role === 'user' ? 'ME' : 'AI' }}</div>
                        </div>
                        <div class="bubble-wrapper">
                            <div class="bubble-info">{{ msg.role === 'user' ? '您的咨询' : selectedAgentName || 'AI 助手' }}
                            </div>
                            <div class="bubble" v-html="msg.content"></div>
                        </div>
                    </div>

                    <div v-if="streaming" class="message-item ai">
                        <div class="avatar-container">
                            <div class="avatar-glow"></div>
                            <div class="avatar-circle">AI</div>
                        </div>
                        <div class="bubble-wrapper">
                            <div class="bubble-info">实时分析中...</div>
                            <div class="bubble">
                                <span v-html="fullResponse"></span>
                                <span class="cursor"></span>
                            </div>
                        </div>
                    </div>
                </div>

                <footer class="input-area">
                    <div class="input-container">
                        <textarea v-model="inputText" placeholder="请描述您的法律问题或粘贴条款..."
                            @keyup.enter.exact.prevent="sendMessage" rows="3"></textarea>
                        <div class="input-actions">
                            <div v-if="errorMsg" class="error-text">{{ errorMsg }}</div>
                            <button class="send-btn" :disabled="loading" @click="sendMessage">
                                <span v-if="!loading">发送指令</span>
                                <span v-else class="loading-spin"></span>
                            </button>
                        </div>
                    </div>
                </footer>
            </div>
        </main>
    </div>
</template>
<script setup>
import { onMounted, onUnmounted } from 'vue'
// 响应式判断是否为移动端
const isMobile = ref(false)
const checkMobile = () => {
    isMobile.value = window.innerWidth <= 600
}
onMounted(() => {
    checkMobile()
    window.addEventListener('resize', checkMobile)
})
onUnmounted(() => {
    window.removeEventListener('resize', checkMobile)
})
// 侧边栏收起状态
const sidebarCollapsed = ref(false)
const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
}
import { ref, nextTick, watch } from 'vue'

// 智能体配置（和你 Python 代码完全一致）
const agentList = ref([
    // 使用 nginx 代理路径，前端向同源发送请求，nginx 会转发到 Spring 后端（java_backend）
    { name: '合同解释专家', url: '/java-api/contract_analysis_stream' },
    { name: '法律检索助手', url: '/java-api/exchange_analysis_stream' },
])
// 默认不选中任何智能体
const selectedAgent = ref(null)
const selectedAgentName = ref('')

// 聊天状态
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const streaming = ref(false)
const fullResponse = ref('')
const errorMsg = ref('')
const messageBox = ref(null)
// 当前请求的 AbortController，用于取消 SSE
const currentController = ref(null)

// 监听下拉的 name，计算出当前选中的智能体对象
watch(selectedAgentName, (name) => {
    selectedAgent.value = agentList.value.find((item) => item.name === name) || null
})

// 管理员登录状态
const adminLoginVisible = ref(false)
const adminPassword = ref('')
const adminLoginError = ref('')




// 发送消息
const sendMessage = async () => {
    if (!selectedAgent.value) {
        errorMsg.value = '请先在侧边栏选择一个智能体。'
        return
    }
    if (!inputText.value.trim()) return
    const userMsg = inputText.value.trim()
    inputText.value = ''

    // 加入用户消息
    messages.value.push({ role: 'user', content: userMsg })
    await nextTick()
    scrollToBottom()

    // 如果有尚未结束的请求，先取消
    if (currentController.value) {
        currentController.value.abort()
        currentController.value = null
    }

    // 开始请求
    loading.value = true
    streaming.value = true
    fullResponse.value = ''
    errorMsg.value = ''

    // 为本次请求创建 AbortController，用于前端超时/手动中断
    const controller = new AbortController()
    currentController.value = controller

    // 简单前端超时控制（例如 120 秒）
    const TIMEOUT_MS = 480000
    const timeoutId = setTimeout(() => {
        // 还在当前这次请求，才触发 abort
        if (currentController.value === controller) {
            controller.abort()
        }
    }, TIMEOUT_MS)

    try {
        console.debug('发送请求到后端 URL:', selectedAgent.value.url)
        // 构造 headers，若已登录则携带 Bearer Token
        const headers = { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' }
        const token = localStorage.getItem('authToken')
        if (token) headers['Authorization'] = `Bearer ${token}`

        const response = await fetch(selectedAgent.value.url, {
            method: 'POST',
            mode: 'cors',
            credentials: 'same-origin',
            headers,
            body: JSON.stringify({ input: userMsg }),
            signal: controller.signal,
        })

        if (!response.ok) {
            errorMsg.value = '服务器错误：' + response.status
            streaming.value = false
            loading.value = false
            return
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        let aiMessageBuffer = ''
        while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const text = decoder.decode(value, { stream: true })
            const lines = text.split('\n')

            for (const line of lines) {
                if (!line.trim()) continue
                if (line.startsWith('data:')) {
                    const jsonStr = line.slice(5).trim()
                    if (!jsonStr) continue
                    try {
                        const data = JSON.parse(jsonStr)
                        if (data.type === 'data') {
                            const token = data.content || ''
                            aiMessageBuffer += token
                            fullResponse.value = aiMessageBuffer
                            streaming.value = true
                            await nextTick()
                            scrollToBottom()
                        } else if (data.type === 'done') {
                            streaming.value = false
                            // 不追加消息，done 只关闭流式区
                        } else if (data.type === 'error') {
                            errorMsg.value = data.content || '服务异常'
                            streaming.value = false
                        } else if (data.type === 'thread_id') {
                            // 可选：如需保存 thread_id，可在此处处理
                        }
                    } catch { continue }
                }
            }
        }

        // 结束后保留最后一条 AI 回复（如果有流式内容）
        if (aiMessageBuffer) {
            messages.value.push({ role: 'ai', content: aiMessageBuffer })
        }
        fullResponse.value = ''
        streaming.value = false
    } catch (err) {
        console.error('请求异常：', err)
        if (err && err.name === 'AbortError') {
            errorMsg.value = '连接已中断：可能是请求超时或手动开始了新的对话。'
        } else if (err && err.message) {
            errorMsg.value = '连接失败：' + err.name + ' - ' + err.message
        } else {
            errorMsg.value = '连接失败：未知错误'
        }
    } finally {
        clearTimeout(timeoutId)
        loading.value = false
        streaming.value = false
        if (currentController.value === controller) {
            currentController.value = null
        }
    }
}

// 清空对话
const clearChat = () => {
    // 清空时同时中断当前请求
    if (currentController.value) {
        currentController.value.abort()
        currentController.value = null
    }
    messages.value = []
    fullResponse.value = ''
    errorMsg.value = ''
}

// 切换智能体时，清空当前对话，实现真正“切换会话”
watch(selectedAgent, () => {
    clearChat()
})

// 滚动到底部
const scrollToBottom = () => {
    nextTick(() => {
        if (messageBox.value) {
            messageBox.value.scrollTop = messageBox.value.scrollHeight
        }
    })
}
</script>

<style scoped>
/* --- 全局基础 --- */
.chat-page {
    display: flex;
    height: 100vh;
    background: #020b14;
    /* 极夜黑 */
    color: #fff;
    font-family: 'PingFang SC', 'Inter', sans-serif;
    position: relative;
    overflow: hidden;
}

.luxury-bg-glow {
    position: absolute;
    top: -10%;
    right: -10%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(64, 158, 255, 0.08) 0%, transparent 70%);
    pointer-events: none;
}

/* --- 侧边栏：磨砂玻璃 --- */
.sidebar {
    width: 260px;
    background: rgba(10, 25, 41, 0.7);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 100;
}

.sidebar.collapsed {
    width: 60px;
}

.sidebar-toggle {
    padding: 20px;
    font-size: 12px;
    letter-spacing: 2px;
    color: rgba(255, 255, 255, 0.4);
    cursor: pointer;
    text-transform: uppercase;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.panel-header {
    margin-bottom: 24px;
    padding: 0 20px;
}

.gold-text {
    color: #d4af37;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
}


.luxury-select {
    width: 100%;
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #222;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.2s;
}

/* 选项颜色适配 */
.luxury-select option {
    color: #222;
    background: #fff;
}

.luxury-note {
    background: rgba(212, 175, 55, 0.05);
    border-left: 2px solid #d4af37;
    padding: 12px;
    font-size: 13px;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.7);
}

/* --- 主区域：悬浮卡片感 --- */
.chat-main {
    flex: 1;
    padding: 30px;
    display: flex;
    justify-content: center;
    background: radial-gradient(at bottom right, #041628, #020b14);
}

.chat-container {
    width: 100%;
    max-width: 1000px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 40px 100px rgba(0, 0, 0, 0.5);
}

.chat-header {
    padding: 20px 30px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    align-items: center;
    gap: 15px;
}

.chat-title {
    font-size: 18px;
    font-weight: 600;
}

.chat-title span {
    font-weight: 300;
    opacity: 0.5;
    font-size: 14px;
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #555;
}

.status-indicator.active {
    background: #67c23a;
    box-shadow: 0 0 10px #67c23a;
}

/* --- 消息气泡：科技奢华感 --- */
.message-box {
    flex: 1;
    padding: 30px;
    overflow-y: auto;
}

.message-item {
    margin-bottom: 32px;
    display: flex;
    gap: 20px;
}

.message-item.user {
    flex-direction: row-reverse;
}

.avatar-circle {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.message-item.user .avatar-circle {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
}

.bubble-wrapper {
    max-width: 70%;
}

.bubble-info {
    font-size: 11px;
    margin-bottom: 6px;
    opacity: 0.4;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.message-item.user .bubble-info {
    text-align: right;
}

.bubble {
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 0 16px 16px 16px;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.03);
}

.message-item.user .bubble {
    background: #fff;
    color: #020b14;
    border-radius: 16px 0 16px 16px;
}

/* --- 输入区 --- */
.input-area {
    padding: 0 30px 30px;
}

.input-container {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 15px;
    transition: all 0.3s;
}

.input-container:focus-within {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
}

textarea {
    width: 100%;
    background: transparent;
    border: none;
    color: #fff;
    outline: none;
    resize: none;
    font-size: 15px;
}

.input-actions {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.send-btn {
    background: #fff;
    color: #020b14;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.send-btn:hover {
    background: #d4af37;
    color: #fff;
}

/* --- 移动端适配适配微调 --- */
@media (max-width: 600px) {
    .chat-main {
        padding: 10px;
    }

    .chat-container {
        border-radius: 0;
        border: none;
    }

    .bubble-wrapper {
        max-width: 85%;
    }
}

/* 光标动画 */
.cursor {
    display: inline-block;
    width: 8px;
    height: 18px;
    background: #d4af37;
    margin-left: 4px;
    animation: blink 1s infinite;
    vertical-align: middle;
}

@keyframes blink {
    50% {
        opacity: 0;
    }
}

/* 新潮“开启新会话”按钮样式 */
.new-session-wrapper {
    display: flex;
    justify-content: center;
    margin: 32px 0 0 0;
}

.new-session-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(90deg, #d4af37 0%, #67c23a 100%);
    color: #fff;
    border: none;
    border-radius: 999px;
    padding: 12px 32px;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 1px;
    box-shadow: 0 4px 24px rgba(212, 175, 55, 0.12), 0 1.5px 6px rgba(103, 194, 58, 0.10);
    cursor: pointer;
    transition: background 0.2s, transform 0.15s;
    outline: none;
    position: relative;
    overflow: hidden;
}

.new-session-btn:hover {
    background: linear-gradient(90deg, #67c23a 0%, #d4af37 100%);
    transform: translateY(-2px) scale(1.04);
    box-shadow: 0 8px 32px rgba(212, 175, 55, 0.18), 0 3px 12px rgba(103, 194, 58, 0.16);
}

.icon-plus {
    font-size: 20px;
    font-weight: 900;
    line-height: 1;
    margin-right: 2px;
    color: #fff;
    text-shadow: 0 1px 4px rgba(212, 175, 55, 0.3);
}
</style>