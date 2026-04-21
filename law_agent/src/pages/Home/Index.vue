<template>
    <div class="home-bg" :class="{ 'fade-out': pageFade }">
        <div class="glow-sphere"></div>

        <div class="top-bar">
            <template v-if="!isLogged">
                <button class="nav-btn nav-btn-primary" @click="fadeAndGo(goLogin)">登 录</button>
                <button class="nav-btn nav-btn-outline" @click="fadeAndGo(goRegister)">注 册</button>
            </template>
            <template v-else>
                <div class="user-status">
                    <span class="status-dot"></span>
                    <button class="nav-btn-text" @click="handleLogout">退出登录</button>
                </div>
            </template>
        </div>

        <div class="home-card">
            <div class="logo-wrapper">
                <img class="home-logo" :src="logoUrl" alt="法影智芒" />
            </div>
            <h1 class="brand-title">法影智芒</h1>
            <p class="subtitle">法律 AI 协作平台</p>

            <div class="action-area">
                <button class="luxury-chat-btn" @click="goChat">
                    <span class="btn-content">进入智能体对话</span>
                    <span class="btn-shimmer"></span>
                </button>
                <transition name="fade">
                    <div v-if="notLogged" class="not-logged-msg">
                        <i class="el-icon-warning-outline"></i> 未登录，请先登录
                    </div>
                </transition>
            </div>
        </div>

        <footer class="home-footer">© 2026 法影智芒 · 智慧法律新范式</footer>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import logoUrl from '@/assets/logo.png'
const router = useRouter()
const pageFade = ref(false)
const notLogged = ref(false)
const isLogged = ref(Boolean(localStorage.getItem('authToken')))
const goChat = () => {
    const token = localStorage.getItem('authToken')
    if (!token) {
        // 先展示未登录提示，短暂等待后触发淡出动画并跳转到登录页（登录后会 redirect 回 /chat）
        notLogged.value = true
        setTimeout(() => {
            fadeAndGo(() => router.push({ name: 'login', query: { redirect: '/chat' } }))
        }, 800)
        return
    }
    // 已登录：走正常的淡出动画再进入聊天页
    fadeAndGo(() => router.push('/chat'))
}
const goLogin = () => fadeAndGo(() => router.push('/login'))
const goRegister = () => fadeAndGo(() => router.push('/register'))
// 登出逻辑：清除 token 并直接回到首页（replace，避免历史记录混乱）
const handleLogout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('username')
    isLogged.value = false
    pageFade.value = false
    router.replace({ name: 'home' }).catch(() => { window.location.href = '/' })
}

// 监听 storage 事件以响应其他标签页的登录状态变化
onMounted(() => {
    const onStorage = (e) => {
        if (e.key === 'authToken') {
            isLogged.value = Boolean(e.newValue)
        }
    }
    window.addEventListener('storage', onStorage)
    // 清理
    onBeforeUnmount(() => window.removeEventListener('storage', onStorage))
})
const fadeAndGo = (fn) => {
    pageFade.value = true
    // 在动画结束后执行导航，捕获可能的导航失败并恢复状态
    setTimeout(async () => {
        try {
            const result = fn()
            if (result && typeof result.then === 'function') {
                await result
            }
        } catch (e) {
            console.error('导航失败：', e)
            pageFade.value = false
            return
        }

        // 如果导航在短时间内未完成（极端情况），作为兜底恢复动画
        setTimeout(() => {
            if (pageFade.value) pageFade.value = false
        }, 2000)
    }, 350)
}
</script>

<style scoped>
/* --- 基础与背景 --- */
.home-bg {
    min-height: 100vh;
    width: 100vw;
    /* 奢华深邃渐变 */
    background: radial-gradient(circle at 50% 50%, #0a2e4e 0%, #041628 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    font-family: "Inter", "PingFang SC", sans-serif;
}

/* 背景装饰光晕 */
.glow-sphere {
    position: absolute;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(64, 158, 255, 0.05) 0%, transparent 70%);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    pointer-events: none;
}

/* --- 顶部导航 --- */
.top-bar {
    position: absolute;
    top: 40px;
    right: 60px;
    display: flex;
    gap: 24px;
    z-index: 10;
}

.nav-btn {
    border-radius: 40px;
    padding: 8px 32px;
    font-size: 15px;
    font-weight: 500;
    letter-spacing: 1px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.nav-btn-primary {
    background: #fff;
    color: #04213a;
}

.nav-btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    background: #e8f3ff;
}

.nav-btn-outline {
    background: transparent;
    color: #fff;
}

.nav-btn-outline:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #fff;
}

.user-status {
    display: flex;
    align-items: center;
    gap: 10px;
    color: rgba(255, 255, 255, 0.8);
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #67c23a;
    border-radius: 50%;
    box-shadow: 0 0 10px #67c23a;
}

.nav-btn-text {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    font-size: 14px;
}

/* --- 主体卡片 (玻璃拟态) --- */
.home-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 40px;
    padding: 60px 50px;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 420px;
    box-shadow:
        0 20px 50px rgba(0, 0, 0, 0.3),
        inset 0 0 0 1px rgba(255, 255, 255, 0.5);
    position: relative;
    z-index: 5;
}

.logo-wrapper {
    position: relative;
    margin-bottom: 30px;
}

.logo-wrapper::after {
    content: '';
    position: absolute;
    inset: -10px;
    border: 1px solid rgba(64, 158, 255, 0.2);
    border-radius: 35px;
    animation: rotate 10s linear infinite;
}

@keyframes rotate {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}

.home-logo {
    width: 140px;
    height: 140px;
    object-fit: cover;
    border-radius: 30px;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.brand-title {
    font-size: 28px;
    color: #1a1a1a;
    font-weight: 800;
    margin-bottom: 8px;
    letter-spacing: 2px;
}

.subtitle {
    font-size: 16px;
    color: #888;
    margin-bottom: 45px;
    letter-spacing: 4px;
    text-transform: uppercase;
}

/* --- 奢华按钮 --- */
.luxury-chat-btn {
    position: relative;
    width: 100%;
    height: 56px;
    background: #1a1a1a;
    color: #fff;
    border: none;
    border-radius: 16px;
    font-size: 17px;
    font-weight: 600;
    cursor: pointer;
    overflow: hidden;
    transition: all 0.3s;
}

.luxury-chat-btn:hover {
    transform: scale(1.02);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
    background: #333;
}

.btn-shimmer {
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(90deg,
            transparent,
            rgba(255, 255, 255, 0.2),
            transparent);
    transform: skewX(-20deg);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% {
        left: -100%;
    }

    50% {
        left: 150%;
    }

    100% {
        left: 150%;
    }
}

/* --- 错误提示 --- */
.not-logged-msg {
    margin-top: 15px;
    color: #f56c6c;
    font-size: 14px;
    font-weight: 500;
}

/* --- 页脚 --- */
.home-footer {
    position: absolute;
    bottom: 30px;
    color: rgba(255, 255, 255, 0.3);
    font-size: 12px;
    letter-spacing: 1px;
}

/* --- 切换动画 --- */
.fade-out {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: #041628;
    animation: luxuryFade 0.5s forwards ease-in-out;
}

@keyframes luxuryFade {
    from {
        opacity: 1;
        transform: scale(1);
    }

    to {
        opacity: 0;
        transform: scale(1.05);
        filter: blur(10px);
    }
}

/* Vue 过渡动画 */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.5s;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>