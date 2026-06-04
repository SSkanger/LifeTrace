<template>
<section class="page" id="summaryPage">
        <div class="section-title">
          <h2>生活总结</h2><span>按时间回看</span>
        </div>

        <div class="summary-list">
          <button class="summary-card primary-summary" data-summary="current-week">
            <div class="summary-card-head">
              <h3>本周总结</h3>
              <time>5 月 26 日 - 6 月 1 日</time>
            </div>
            <p>整理这一周出现较多的地点、日程和照片线索，生成一段适合快速回看的生活概览。</p>
            <div class="summary-tags"><span class="summary-tag">课程与项目</span><span class="summary-tag">图书馆</span><span class="summary-tag">晚间活动</span></div>
          </button>

          <button class="summary-card" data-summary="weekly">
            <div class="summary-card-head">
              <h3>周度总结</h3>
              <span class="summary-arrow">查看 ›</span>
            </div>
            <p>按周查看生活节奏，可以切换到上一周或更早的周度总结。</p>
            <div class="summary-tags"><span class="summary-tag">小组任务</span><span class="summary-tag">校园照片</span></div>
          </button>

          <button class="summary-card" data-summary="monthly">
            <div class="summary-card-head">
              <h3>月度总结</h3>
              <span class="summary-arrow">查看 ›</span>
            </div>
            <p>默认查看本月，也可以在详情页切换到其它月份的总结。</p>
            <div class="summary-tags"><span class="summary-tag">月度回顾</span><span class="summary-tag">生活轨迹</span></div>
          </button>
        </div>

        <div class="summary-panel" id="summaryPanel">
          <div class="summary-panel-bar">
            <button class="summary-panel-back" id="summaryPanelBack">‹</button>
            <div class="summary-panel-title">
              <h2 id="summaryPanelTitle">本周总结</h2>
              <span id="summaryPanelMeta">5 月 26 日 - 6 月 1 日</span>
            </div>
          </div>
          <div id="summaryMonthPicker" class="month-picker" style="display:none">
            <div class="period-selector">
              <div class="year-row">
                <button class="year-chip active" data-year="2025">2025</button>
                <button class="year-chip" data-year="2024">2024</button>
                <button class="year-chip" data-year="2023">2023</button>
              </div>
              <div class="month-grid">
                <button class="month-chip" data-month="1">1 月</button>
                <button class="month-chip" data-month="2">2 月</button>
                <button class="month-chip" data-month="3">3 月</button>
                <button class="month-chip" data-month="4">4 月</button>
                <button class="month-chip active" data-month="5">5 月</button>
                <button class="month-chip" data-month="6">6 月</button>
                <button class="month-chip" data-month="7">7 月</button>
                <button class="month-chip" data-month="8">8 月</button>
                <button class="month-chip" data-month="9">9 月</button>
                <button class="month-chip" data-month="10">10 月</button>
                <button class="month-chip" data-month="11">11 月</button>
                <button class="month-chip" data-month="12">12 月</button>
              </div>
            </div>
          </div>
          <div id="summaryWeekPicker" class="month-picker" style="display:none">
            <div class="week-list">
              <button class="week-chip active" data-week="0">本周</button>
              <button class="week-chip" data-week="1">上周</button>
              <button class="week-chip" data-week="2">前两周</button>
              <button class="week-chip" data-week="3">前三周</button>
            </div>
          </div>
          <div id="summaryPanelBody"></div>
        </div>
      </section>
</template>
