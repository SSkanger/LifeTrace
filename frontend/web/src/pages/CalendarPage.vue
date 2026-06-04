<template>
<section class="page active" id="calendarPage">
        <div class="section-title">
          <h2>日期回顾</h2>
        </div>
        <div class="calendar">
          <div class="calendar-head"><button class="chev" id="prevMonthBtn" aria-label="上个月">‹</button><strong id="calendarTitle">2025 年 5 月</strong><button class="chev" id="nextMonthBtn" aria-label="下个月">›</button></div>
          <div class="week">
            <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
          </div>
          <div class="days" id="calendarDays"><button class="day muted">27</button><button class="day muted">28</button><button class="day muted">29</button><button class="day muted">30</button><button class="day">1</button><button class="day">2</button><button class="day">3</button><button class="day">4</button><button class="day">5</button><button class="day">6</button><button class="day">7</button><button class="day">8</button><button class="day">9</button><button class="day">10</button><button class="day">11</button><button class="day">12</button><button class="day">13</button><button class="day">14</button><button class="day">15</button><button class="day">16</button><button class="day">17</button><button class="day">18</button><button class="day">19</button><button class="day">20</button><button class="day">21</button><button class="day">22</button><button class="day">23</button><button class="day">24</button><button class="day">25</button><button class="day">26</button><button class="day">27</button><button class="day">28</button><button class="day">29</button><button class="day active-day">30</button><button class="day">31</button></div>
        </div>
        <div class="section-title">
          <h2>已选择 5 月 30 日</h2><span>4 条线索</span>
        </div>
        <div class="card gold" id="selectedDaySummary" style="">
            <div class="card-title">摘要</div>
            <p>这一天整理到图书馆停留、课程资料、校园照片和晚间散步等线索。你可以继续查看完整时间线，或将这一天加入收藏。</p>
          </div>
        <button class="primary" style="width:100%;margin-top:13px" data-go="reviewPage">查看回忆</button>
      </section>
</template>
