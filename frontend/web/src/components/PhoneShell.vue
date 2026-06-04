<template>
  <div class="screen-label">LifeTrace · Hi-Fi Prototype</div>
  <div class="phone">
    <div class="stars"></div>
    <StatusBar />
    <TopBar />
    <main>
      <HomePage />
      <CalendarPage />
      <ReviewPage />
      <SearchPage />
      <SummaryPage />
      <PermissionPage />
      <StatePages />
    </main>
    <BottomNav />
    <div class="account-scrim" id="accountScrim"></div>
    <aside class="account-panel" id="accountPanel" aria-label="账户面板">
      <div class="account-head">
        <div class="account-avatar">新</div>
        <div>
          <h2>刘新康</h2>
          <span>LifeTrace 账号 · 本地优先</span>
        </div>
      </div>
      <div class="account-card">
        <div class="account-row">
          <span>账号状态</span>
          <b>已连接</b>
        </div>
        <div class="account-row">
          <span>数据范围</span>
          <b>照片 / 位置 / 使用线索</b>
        </div>
      </div>
      <div class="account-section-title">收藏的每日回顾</div>
      <div class="account-favorites" id="accountFavorites"></div>
      <div class="account-actions">
        <button class="account-action" data-go="permissionPage" id="accountSettingsBtn">设置</button>
      </div>
    </aside>
    <div class="toast" id="toast">已收藏这段记忆</div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import BottomNav from './BottomNav.vue';
import StatusBar from './StatusBar.vue';
import TopBar from './TopBar.vue';
import CalendarPage from '../pages/CalendarPage.vue';
import HomePage from '../pages/HomePage.vue';
import PermissionPage from '../pages/PermissionPage.vue';
import ReviewPage from '../pages/ReviewPage.vue';
import SearchPage from '../pages/SearchPage.vue';
import StatePages from '../pages/StatePages.vue';
import SummaryPage from '../pages/SummaryPage.vue';

const runtimeScripts = [
  'lifetrace-api.js',
  'scripts/core-navigation.js',
  'scripts/calendar-page.js',
  'scripts/review-search.js',
  'scripts/summary-page.js',
  'scripts/favorite-init.js'
];

function loadClassicScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

onMounted(async () => {
  for (const script of runtimeScripts) {
    await loadClassicScript(script);
  }
});
</script>
