<template>
    <div class="chat-page">
        <div class="luxury-overlay"></div>
        <div class="glow-point p1"></div>
        <div class="glow-point p2"></div>

        <main class="chat-main">
            <div class="chat-container luxury-login-card">
                <div class="logo-aura">
                    <div class="logo-inner">
                        <span class="logo-icon">⚖️</span>
                    </div>
                </div>

                <h1 class="login-title">法影智芒</h1>
                <div class="brand-divider">
                    <span class="divider-line"></span>
                    <span class="divider-text">LEGAL AI PLATFORM</span>
                    <span class="divider-line"></span>
                </div>
                <p class="login-subtitle">尊享智能法律协作</p>

                <el-form class="login-form" @submit.prevent>
                    <div class="input-group">
                        <label class="input-label">IDENTITY</label>
                        <el-input v-model="username" placeholder="请输入用户名" auto-complete="username"
                            class="luxury-input" />
                    </div>

                    <div class="input-group">
                        <label class="input-label">SECRET KEY</label>
                        <el-input v-model="password" type="password" show-password placeholder="请输入密码"
                            auto-complete="current-password" class="luxury-input" />
                    </div>

                    <transition name="el-fade-in">
                        <div v-if="errorMsg" class="error-badge">
                            <span class="error-dot"></span> {{ errorMsg }}
                        </div>
                    </transition>

                    <button class="luxury-login-btn" :disabled="loading" @click="handleLogin">
                        <span class="btn-text" v-if="!loading">立 即 登 录</span>
                        <span class="btn-loading" v-else>鉴权中...</span>
                        <div class="btn-shimmer"></div>
                    </button>

                    <div class="login-footer">
                        <span>登录即代表同意安全合规协议</span>
                    </div>
                </el-form>
            </div>
        </main>
    </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

// 登录逻辑：调用后端 Spring Boot 接口 /api/auth/login（通过 nginx 代理为 /java-api/auth/login）
const handleLogin = async () => {
    errorMsg.value = ''
    if (!username.value || !password.value) {
        errorMsg.value = '请输入用户名和密码'
        return
    }
    loading.value = true
    try {
        const resp = await fetch('/java-api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username.value,
                password: password.value,
            }),
        })

        if (!resp.ok) {
            // 尝试解析后端返回的错误信息，若为 JSON 则取 message 字段，避免直接展示完整 JSON
            let msg = '登录失败：服务器错误'
            try {
                const text = await resp.text()
                if (text) {
                    try {
                        const parsed = JSON.parse(text)
                        if (parsed && parsed.message) msg = parsed.message
                        else msg = text
                    } catch {
                        msg = text
                    }
                }
            } catch { /* ignore */ }
            errorMsg.value = msg
            return
        }

        const data = await resp.json()

        if (!data || !data.token) {
            errorMsg.value = data?.message || '登录失败：用户名或密码错误'
            return
        }

        // 存储 token 和用户名，供后续接口使用
        localStorage.setItem('authToken', data.token)
        if (data.username) {
            localStorage.setItem('username', data.username)
        }

        // 登录成功后跳转到登录前的目标（若有），否则跳转到聊天页
        const redirectPath = route.query.redirect ? String(route.query.redirect) : null
        if (redirectPath) {
            router.push(redirectPath).catch(() => { window.location.href = redirectPath })
        } else {
            router.push({ name: 'chat' }).catch(() => { window.location.href = '/chat' })
        }
    } catch (e) {
        errorMsg.value = '登录失败：' + (e?.message || '网络异常')
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
/* --- 奢华背景基座 --- */
.chat-page {
    min-height: 100vh;
    width: 100vw;
    background: #020b14;
    /* 极夜黑 */
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Inter", "PingFang SC", sans-serif;
    position: relative;
    overflow: hidden;
}

/* 背景流动光效 */
.luxury-overlay {
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 50% 50%, #04213a 0%, #020b14 100%);
    z-index: 1;
}

.glow-point {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    z-index: 2;
    opacity: 0.15;
}

.p1 {
    width: 400px;
    height: 400px;
    background: #409eff;
    top: -100px;
    left: -100px;
}

.p2 {
    width: 300px;
    height: 300px;
    background: #d4af37;
    bottom: -50px;
    right: -50px;
}

/* --- 登录卡片 (玻璃拟态 + 金属边框) --- */
.luxury-login-card {
    position: relative;
    z-index: 10;
    width: 100%;
    max-width: 400px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 32px;
    padding: 50px 40px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Logo 动效 */
.logo-aura {
    width: 84px;
    height: 84px;
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(255, 255, 255, 0.05) 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    border: 1px solid rgba(212, 175, 55, 0.3);
    position: relative;
}

.logo-aura::after {
    content: '';
    position: absolute;
    inset: -4px;
    border: 1px solid rgba(212, 175, 55, 0.1);
    border-radius: 50%;
    animation: pulse 3s infinite;
}

@keyframes pulse {
    0% {
        transform: scale(1);
        opacity: 1;
    }

    100% {
        transform: scale(1.3);
        opacity: 0;
    }
}

.logo-icon {
    font-size: 36px;
    filter: drop-shadow(0 0 10px rgba(64, 158, 255, 0.5));
}

/* 标题排版 */
.login-title {
    font-size: 28px;
    font-weight: 800;
    color: #fff;
    letter-spacing: 4px;
    margin-bottom: 12px;
}

.brand-divider {
    display: flex;
    align-items: center;
    gap: 15px;
    width: 100%;
    margin-bottom: 8px;
}

.divider-line {
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
}

.divider-text {
    font-size: 9px;
    color: #d4af37;
    font-weight: 700;
    letter-spacing: 2px;
}

.login-subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.4);
    margin-bottom: 40px;
}

/* --- 输入项奢华重塑 --- */
.input-group {
    width: 100%;
    margin-bottom: 24px;
}

.input-label {
    display: block;
    font-size: 10px;
    color: #d4af37;
    font-weight: 700;
    margin-bottom: 8px;
    margin-left: 4px;
    letter-spacing: 1px;
}

/* 深度定制 Element Input */
:deep(.luxury-input .el-input__wrapper) {
    background-color: rgba(255, 255, 255, 0.05) !important;
    box-shadow: none !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 8px 16px !important;
    transition: all 0.3s;
}

:deep(.luxury-input .el-input__wrapper.is-focus) {
    border-color: #d4af37 !important;
    background-color: rgba(255, 255, 255, 0.08) !important;
}

:deep(.luxury-input .el-input__inner) {
    color: #fff !important;
    font-size: 15px !important;
}

/* --- 错误提示 --- */
.error-badge {
    background: rgba(245, 108, 108, 0.1);
    border: 1px solid rgba(245, 108, 108, 0.2);
    color: #f56c6c;
    padding: 10px 16px;
    border-radius: 10px;
    font-size: 13px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.error-dot {
    width: 6px;
    height: 6px;
    background: #f56c6c;
    border-radius: 50%;
}

/* --- 按钮：黄金流体感 --- */
.luxury-login-btn {
    width: 100%;
    height: 52px;
    background: #fff;
    color: #020b14;
    border: none;
    border-radius: 14px;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 2px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
    margin-top: 10px;
}

.luxury-login-btn:hover:enabled {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(255, 255, 255, 0.2);
    background: #f0f0f0;
}

.luxury-login-btn:active:enabled {
    transform: translateY(0);
}

.btn-shimmer {
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.05), transparent);
    transform: skewX(-30deg);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% {
        left: -100%;
    }

    100% {
        left: 150%;
    }
}

.login-footer {
    margin-top: 24px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.2);
    text-align: center;
}
</style>