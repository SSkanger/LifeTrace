<template>
<section class="page" id="homePage">
        <div class="hero">
          <div class="eyebrow">Memory rebuilt from your traces</div>
          <h1>今天，想看什么？</h1>
          <p class="lead">从已授权的照片、位置、日程与使用线索中，自动整理值得回看的生活片段。</p>
        </div>

        <div class="section-title">
          <h2>快速进入</h2><span>回看 · 搜索 · 总结</span>
        </div>
        <div class="grid-2">
          <button class="action-card" data-go="calendarPage"><span class="action-icon">◷</span>
            <div>
              <div class="action-title">选择日期</div>
              <div class="action-sub">回顾任意一天</div>
            </div>
          </button>
          <button class="action-card" data-go="reviewPage"><span class="action-icon">✦</span>
            <div>
              <div class="action-title">今日回看</div>
              <div class="action-sub">进行今日回顾</div>
            </div>
          </button>
          <button class="action-card" data-go="searchPage"><span class="action-icon">⌕</span>
            <div>
              <div class="action-title">记忆搜索</div>
              <div class="action-sub">搜索往日经历</div>
            </div>
          </button>
          <button class="action-card" data-go="summaryPage"><span class="action-icon">⌁</span>
            <div>
              <div class="action-title">近期总结</div>
              <div class="action-sub">查看近期生活总结</div>
            </div>
          </button>
        </div>

        <div class="section-title">
          <h2>今日摘要</h2>
        </div>
        <div class="card gold" id="todaySummaryCard">
          <div class="card-title" id="todaySummaryTitle">今天的大部分时间，你在学习与整理之间切换 </div>
          <p id="todaySummaryText">下午在图书馆停留较久，傍晚短暂停留并拍下晚霞；晚上和朋友散步后，手机应用切换明显减少。</p>
          <div class="summary-strip" id="todaySummaryTags"><span class="chip">图书馆 2h 48m</span><span class="chip cool">晚霞照片</span><span class="chip">晚间散步</span></div>
        </div>
      </section>
</template>
