<template>
    <router-link to="/" class="site-logo-anchor-right" aria-label="返回首页">
        <div class="gold-line"></div>
        <div class="anchor-content">
            <div class="anchor-text">
                <span class="label-en">HOME</span>
                <span class="label-cn">返回首页</span>
            </div>
            <img class="anchor-img" :src="logoUrl" alt="法影智芒" />
        </div>
    </router-link>
</template>

<script setup>
import logoUrl from '@/assets/logo.png'
</script>

<style scoped>
.site-logo-anchor-right {
    position: fixed;
    /* 放在右侧偏上位置（15%高度），完美避开底部的输入框区域 */
    top: 15vh;
    right: 0;
    z-index: 10000;
    text-decoration: none;
    display: flex;
    align-items: center;
    /* 悬停时往左探出一点，增加人性化互动 */
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.anchor-content {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(10, 25, 41, 0.75);
    /* 深邃极夜蓝背景 */
    backdrop-filter: blur(12px);
    padding: 10px 12px 10px 20px;
    border-radius: 12px 0 0 12px;
    /* 镜像圆角：左侧圆 */
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-right: none;
    /* 贴边不需要边框 */
    box-shadow: -4px 0 24px rgba(0, 0, 0, 0.4);
}

.anchor-img {
    width: 46px;
    height: 46px;
    object-fit: contain;
    border-radius: 8px;
    /* 柔和的白光，取代生硬的蓝色阴影 */
    filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.1));
}

.anchor-text {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-end;
    /* 文字向右对齐，靠近 Logo */
}

.label-en {
    font-size: 9px;
    color: #d4af37;
    /* 统一香槟金 */
    font-weight: 800;
    letter-spacing: 2px;
    line-height: 1;
    margin-bottom: 4px;
}

.label-cn {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
    letter-spacing: 1px;
}

.gold-line {
    width: 3px;
    height: 32px;
    background: linear-gradient(to bottom, transparent, #d4af37, transparent);
    margin-right: -1px;
    /* 贴合内容区 */
    border-radius: 2px;
    z-index: 2;
}

/* --- 交互感增强 --- */

.site-logo-anchor-right:hover {
    /* 悬停时轻微向左探出，告知用户可点击 */
    transform: translateX(-6px);
}

.site-logo-anchor-right:hover .anchor-content {
    background: rgba(15, 35, 55, 0.95);
    border-color: rgba(212, 175, 55, 0.4);
}

/* 移动端适配 */
@media (max-width: 600px) {
    .site-logo-anchor-right {
        top: 20px;
        /* 手机端挪到顶部 */
    }

    .anchor-content {
        padding: 6px 8px 6px 12px;
        gap: 8px;
    }

    .anchor-img {
        width: 32px;
        height: 32px;
    }

    .label-cn {
        font-size: 11px;
    }

    .label-en {
        display: none;
        /* 移动端精简文字 */
    }
}
</style>