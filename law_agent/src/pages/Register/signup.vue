<template>
    <div class="chat-page">
        <div class="luxury-overlay"></div>
        <div class="glow-point p3"></div>

        <main class="chat-main">
            <div class="chat-container luxury-register-card">
                <div class="logo-aura">
                    <div class="logo-inner">
                        <span class="logo-icon">⚖️</span>
                    </div>
                </div>

                <h1 class="login-title">法影智芒</h1>
                <div class="brand-divider">
                    <span class="divider-line"></span>
                    <span class="divider-text">MEMBERSHIP</span>
                    <span class="divider-line"></span>
                </div>
                <p class="login-subtitle">开启您的 AI 法律智库</p>

                <el-form class="login-form" @submit.prevent>
                    <div class="input-group">
                        <label class="input-label">USERNAME</label>
                        <el-input v-model="username" placeholder="设定您的登录账号" auto-complete="username"
                            class="luxury-input" />
                    </div>

                    <div class="input-group">
                        <label class="input-label">PASSWORD</label>
                        <el-input v-model="password" type="password" show-password placeholder="设定高强度密码"
                            auto-complete="new-password" class="luxury-input" />
                    </div>

                    <div class="input-group">
                        <label class="input-label">CONFIRM PASSWORD</label>
                        <el-input v-model="confirmPassword" type="password" show-password placeholder="请再次输入以确认"
                            auto-complete="new-password" class="luxury-input" />
                    </div>

                    <transition name="el-fade-in">
                        <div v-if="errorMsg" class="error-badge">
                            <span class="error-dot"></span> {{ errorMsg }}
                        </div>
                    </transition>

                    <button class="luxury-register-btn" :disabled="loading" @click="handleSignup">
                        <span class="btn-text" v-if="!loading">即 刻 注 册</span>
                        <span class="btn-loading" v-else>正在建立档案...</span>
                        <div class="btn-shimmer"></div>
                    </button>

                    <div class="login-footer">
                        <span>已有账号？</span>
                        <a href="/login" class="gold-link">立即登录</a>
                    </div>
                </el-form>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref } from 'vue'
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleSignup = async () => {
    errorMsg.value = ''
    if (!username.value || !password.value || !confirmPassword.value) {
        errorMsg.value = '请填写所有字段'
        return
    }
    if (password.value !== confirmPassword.value) {
        errorMsg.value = '两次输入的密码不一致'
        return
    }
    loading.value = true
    try {
        const resp = await fetch('/java-api/auth/register', {
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
            let msg = '注册失败：服务器错误'
            try {
                const text = await resp.text()
                if (text) msg = text
            } catch { /* ignore */ }
            errorMsg.value = msg
            return
        }

        const data = await resp.json()
        if (data && data.message && data.message.includes('成功')) {
            // 注册成功，跳转登录页
            window.location.href = '/login'
        } else {
            errorMsg.value = data?.message || '注册失败'
        }
    } catch (e) {
        errorMsg.value = '注册失败：' + (e?.message || '网络异常')
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
/* --- 全局背景与布局 --- */
.chat-page {
    min-height: 100vh;
    width: 100vw;
    background: #020b14;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Inter", "PingFang SC", sans-serif;
    position: relative;
    overflow: hidden;
}

.luxury-overlay {
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 50% 50%, #04213a 0%, #020b14 100%);
    z-index: 1;
}

.glow-point {
    position: absolute;
    width: 500px;
    height: 500px;
    border-radius: 50%;
    filter: blur(100px);
    z-index: 2;
    opacity: 0.12;
}

.p3 {
    background: #409eff;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

/* --- 注册卡片 --- */
.luxury-register-card {
    position: relative;
    z-index: 10;
    width: 100%;
    max-width: 420px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(30px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 32px;
    padding: 40px 45px;
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Logo 动效 */
.logo-aura {
    width: 76px;
    height: 76px;
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(255, 255, 255, 0.05) 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
    border: 1px solid rgba(212, 175, 55, 0.25);
}

.logo-icon {
    font-size: 32px;
    filter: drop-shadow(0 0 8px rgba(212, 175, 55, 0.4));
}

/* 标题排版 */
.login-title {
    font-size: 26px;
    font-weight: 800;
    color: #fff;
    letter-spacing: 5px;
    margin-bottom: 12px;
}

.brand-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    margin-bottom: 8px;
}

.divider-line {
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
}

.divider-text {
    font-size: 9px;
    color: #d4af37;
    font-weight: 700;
    letter-spacing: 3px;
}

.login-subtitle {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.35);
    margin-bottom: 35px;
    letter-spacing: 1px;
}

/* --- 输入项定制 --- */
.input-group {
    width: 100%;
    margin-bottom: 20px;
}

.input-label {
    display: block;
    font-size: 9px;
    color: #d4af37;
    font-weight: 700;
    margin-bottom: 6px;
    letter-spacing: 1.5px;
    opacity: 0.8;
}

:deep(.luxury-input .el-input__wrapper) {
    background-color: rgba(255, 255, 255, 0.04) !important;
    box-shadow: none !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    padding: 6px 14px !important;
    transition: all 0.3s;
}

:deep(.luxury-input .el-input__wrapper.is-focus) {
    border-color: #d4af37 !important;
    background-color: rgba(255, 255, 255, 0.07) !important;
}

:deep(.luxury-input .el-input__inner) {
    color: #fff !important;
    font-size: 14px !important;
}

/* --- 注册按钮：纯白高亮 --- */
.luxury-register-btn {
    width: 100%;
    height: 50px;
    background: #fff;
    color: #020b14;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 3px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    margin-top: 15px;
}

.luxury-register-btn:hover:enabled {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(255, 255, 255, 0.15);
    filter: brightness(1.05);
}

.luxury-register-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-shimmer {
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.03), transparent);
    transform: skewX(-25deg);
    animation: shimmer 4s infinite;
}

@keyframes shimmer {
    0% {
        left: -100%;
    }

    40%,
    100% {
        left: 150%;
    }
}

/* --- 错误提示与底部 --- */
.error-badge {
    background: rgba(245, 108, 108, 0.08);
    border: 1px solid rgba(245, 108, 108, 0.15);
    color: #f89898;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.error-dot {
    width: 5px;
    height: 5px;
    background: #f56c6c;
    border-radius: 50%;
}

.login-footer {
    margin-top: 25px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.3);
}

.gold-link {
    color: #d4af37;
    text-decoration: none;
    margin-left: 8px;
    font-weight: 600;
    transition: opacity 0.2s;
}

.gold-link:hover {
    opacity: 0.8;
    text-decoration: underline;
}

/* 移动端优化 */
@media (max-width: 480px) {
    .luxury-register-card {
        padding: 30px 25px;
        margin: 20px;
    }
}
</style>
