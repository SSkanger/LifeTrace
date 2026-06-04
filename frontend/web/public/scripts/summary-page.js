const summaryCopy = {
      currentWeek: {
        title: '本周总结',
        meta: '5 月 26 日 - 6 月 1 日',
        body: `
          <div class="summary-hero-detail">
            <div class="summary-kicker">THIS WEEK</div>
            <h3>这一周更像是在推进任务，也在慢慢恢复</h3>
            <p>这一周的记录更偏向课程推进和项目整理。图书馆、教学楼和宿舍之间的切换较多，晚间出现了几次散步和照片线索。</p>
          </div>
          <div class="summary-tags"><span class="summary-tag">图书馆</span><span class="summary-tag">课程资料</span><span class="summary-tag">晚间散步</span></div>
          <div class="summary-section-title"><h3>本周重点</h3><span>适合快速讲解</span></div>
          <div class="card"><div class="summary-story"><div class="story-row"><b>主线</b><p>课程表、位置停留和少量照片显示，本周和教学楼、图书馆相关的线索较多。</p></div><div class="story-row"><b>补充</b><p>部分日期只有位置或日程线索，具体做了什么仍需要用户确认或补充。</p></div></div></div>
          <div class="summary-section-title"><h3>每日概述</h3><span>左右滑动查看</span></div>
          <div class="daily-overview-track">
            <div class="daily-overview-card"><b>周一</b><p>课程表显示上午有课，位置线索主要在教学楼附近。</p><span>课程表 · 教学楼</span></div>
            <div class="daily-overview-card"><b>周二</b><p>记录较少，只能看到宿舍和教学楼之间的短距离切换。</p><span>线索较少</span></div>
            <div class="daily-overview-card"><b>周三</b><p>下午在图书馆区域停留较久，傍晚有一张校园照片。</p><span>图书馆 · 照片</span></div>
            <div class="daily-overview-card"><b>周四</b><p>日程和位置线索较稳定，但缺少照片，具体活动不做判断。</p><span>日程 · 位置</span></div>
            <div class="daily-overview-card"><b>周五</b><p>教学楼和图书馆相关线索较多，晚间手机使用切换减少。</p><span>地点 · 使用线索</span></div>
            <div class="daily-overview-card"><b>周六</b><p>生活线索更分散，出现短暂出行和少量照片记录。</p><span>出行 · 照片</span></div>
            <div class="daily-overview-card"><b>周日</b><p>记录以宿舍附近和少量日程线索为主，适合作为待补充日期。</p><span>待补充</span></div>
          </div>`
      },
      weekly: {
        title: '周度总结',
        meta: '按周查看生活节奏',
        body: `
          <div class="card gold">
            <div class="card-title">最近一周</div>
            <p>最近一周的主要线索集中在学习场景和小组任务。相比单日回顾，周度总结更适合看出一段时间内重复出现的地点和生活节奏。</p>
          </div>
          <div class="summary-list" style="margin-top:12px">
            <button class="summary-card"><div class="summary-card-head"><h3>5 月 26 日 - 6 月 1 日</h3><span class="summary-arrow">当前周</span></div><p>课程推进、图书馆停留和晚间活动较多。</p></button>
            <button class="summary-card"><div class="summary-card-head"><h3>5 月 19 日 - 5 月 25 日</h3><span class="summary-arrow">查看 ›</span></div><p>小组作业和资料整理线索更明显。</p></button>
          </div>`
      }
    };

    let selectedSummaryYear = '2025';
    let selectedSummaryMonth = '5';
    let selectedSummaryWeek = '0';
    const monthlyCopy = {
      '2025-5': {
        meta: '2025 年 5 月',
        title: '这个月，你主要在学习和恢复之间切换',
        overview: '这个月的记录主要围绕课程推进、图书馆停留和小组任务展开。月中之后，晚间散步和校园照片出现得更多，生活节奏从集中学习逐渐变得更有恢复感。',
        rhythm: '前半月更像任务推进期，后半月出现更多放松片段，尤其是晚间散步和校园照片。',
        places: '图书馆、教学楼和宿舍是最常出现的地点，操场附近在晚上出现过几次。',
        review: '适合继续查看 5 月 14 日、5 月 24 日和有晚霞照片的日期。',
        tags: ['课程推进', '图书馆', '校园照片', '晚间散步']
      },
      '2025-4': {
        meta: '2025 年 4 月',
        title: '这个月更像一段稳定适应期',
        overview: '4 月的线索更偏向课程适应和资料整理，教学楼与宿舍之间的切换较多，照片记录相对较少。',
        rhythm: '生活节奏比较稳定，日程线索比照片线索更完整。',
        places: '教学楼和宿舍出现频率较高，图书馆停留相对分散。',
        review: '适合继续查看课程较密集的几天，补充当时的主观感受。',
        tags: ['教学楼', '课程适应', '资料整理']
      },
      '2025-3': {
        meta: '2025 年 3 月',
        title: '这个月记录了新阶段的开始',
        overview: '3 月更像是新阶段的开始，日程线索比较分散，适合用来回看开学后的生活变化。',
        rhythm: '记录密度不算高，但能看出从假期状态回到校园生活的过渡。',
        places: '宿舍、教学楼和食堂线索较多，户外照片较少。',
        review: '适合用作学期开始的基准总结。',
        tags: ['开学', '日程变化', '生活节奏']
      }
    };

    const fallbackMonthlyCopy = {
      title: '这个月的线索还不够完整',
      overview: '这个月份目前整理到的线索较少，可以先作为预览页保留。真实 demo 中可以根据该月的日期回顾自动生成完整总结。',
      rhythm: '暂时没有足够连续的线索判断生活节奏。',
      places: '地点线索较少，建议进入具体日期查看。',
      review: '可以通过日期回顾补充更多片段。',
      tags: ['线索较少', '可补充']
    };

    const weeklyCopy = {
      0: {
        meta: '5 月 26 日 - 6 月 1 日',
        overview: '本周的记录更偏向课程推进和项目整理。图书馆、教学楼和宿舍之间的切换较多，晚间出现了几次散步和照片线索。',
        focus: '项目推进和课程资料整理是这一周最明显的主线。',
        review: '可以重点回看周三和周五的学习片段。'
      },
      1: {
        meta: '5 月 19 日 - 5 月 25 日',
        overview: '这一周的小组任务线索更明显，日程和地点记录集中在教学楼、图书馆和宿舍。',
        focus: '小组协作、资料整理和课后复盘比较突出。',
        review: '适合回看小组讨论和资料整理的连续片段。'
      },
      2: {
        meta: '5 月 12 日 - 5 月 18 日',
        overview: '这一周出现了较完整的日期回顾，学习线索和生活照片都有记录。',
        focus: '图书馆停留和晚间散步让这一周比较容易被重新想起。',
        review: '5 月 14 日是这一周最适合作为样例展示的日期。'
      },
      3: {
        meta: '5 月 5 日 - 5 月 11 日',
        overview: '这一周记录较分散，主要能看到课程、作业和少量校园活动。',
        focus: '课程节奏比较稳定，但生活片段需要更多补充。',
        review: '适合作为“线索较少但仍可整理”的展示。'
      }
    };

    function renderMonthlySummary(year = selectedSummaryYear, month = selectedSummaryMonth) {
      selectedSummaryYear = String(year);
      selectedSummaryMonth = String(month);
      const data = monthlyCopy[`${selectedSummaryYear}-${selectedSummaryMonth}`] || { ...fallbackMonthlyCopy, meta: `${selectedSummaryYear} 年 ${selectedSummaryMonth} 月` };
      document.getElementById('summaryPanelTitle').textContent = '月度总结';
      document.getElementById('summaryPanelMeta').textContent = data.meta;
      document.querySelectorAll('.year-chip').forEach(chip => chip.classList.toggle('active', chip.dataset.year === selectedSummaryYear));
      document.querySelectorAll('.month-chip').forEach(chip => chip.classList.toggle('active', chip.dataset.month === selectedSummaryMonth));
      document.getElementById('summaryPanelBody').innerHTML = `
        <div class="summary-hero-detail">
          <div class="summary-kicker">MONTHLY REVIEW</div>
          <h3>${data.title}</h3>
          <p>${data.overview}</p>
        </div>
        <div class="summary-tags">${data.tags.map(tag => `<span class="summary-tag">${tag}</span>`).join('')}</div>
        <div class="summary-section-title"><h3>月度脉络</h3><span>由日期回顾整理</span></div>
        <div class="card">
          <div class="summary-story">
            <div class="story-row"><b>生活节奏</b><p>${data.rhythm}</p></div>
            <div class="story-row"><b>常出现地点</b><p>${data.places}</p></div>
            <div class="story-row"><b>继续回看</b><p>${data.review}</p></div>
          </div>
        </div>
        <div class="summary-section-title"><h3>推荐查看</h3><span>进入具体日期</span></div>
        <div class="summary-memory-list">
          <button class="summary-memory" data-go="calendarPage"><span><b>5 月 14 日 · 图书馆之后的晚霞</b><span>完整时间线和照片线索比较清楚</span></span><i>›</i></button>
          <button class="summary-memory" data-go="calendarPage"><span><b>5 月 24 日 · 小组任务整理</b><span>适合回看课程推进过程</span></span><i>›</i></button>
        </div>
        <div class="summary-note" style="margin-top:16px">也可以用自然语言搜索这个月相关的地点、照片或日程片段。</div>`;
    }

    function formatIsoDate(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }

    function todayIsoDate() {
      const override = window.LifeTraceToday || document.body.dataset.today || '';
      if (/^\d{4}-\d{2}-\d{2}$/.test(override)) return override;
      return formatIsoDate(new Date());
    }

    function currentWeekDates() {
      const today = new Date(`${todayIsoDate()}T00:00:00`);
      const day = today.getDay() || 7;
      const monday = new Date(today);
      monday.setDate(today.getDate() - day + 1);
      return Array.from({ length: 7 }, (_, index) => {
        const date = new Date(monday);
        date.setDate(monday.getDate() + index);
        return formatIsoDate(date);
      });
    }

    function visibleDailyOverviews(items) {
      const today = todayIsoDate();
      return items.filter((item, index) => {
        const date = dailyOverviewDate(item, index);
        return !/^\d{4}-\d{2}-\d{2}$/.test(date) || date <= today;
      });
    }

    function dailyOverviewDate(item, index) {
      return item.isoDate || item.targetDate || item.date || item.day || currentWeekDates()[index] || '';
    }

    function openDailyOverviewReview(date) {
      if (!date || !window.openDailyReview) return;
      document.getElementById('summaryPanel').classList.remove('active', 'closing');
      window.openDailyReview(date, {
        targetPage: 'summaryPage',
        restore: { panel: 'weekly', week: selectedSummaryWeek }
      });
    }

    function bindDailyOverviewClicks() {
      document.querySelectorAll('#summaryPanelBody .daily-overview-card').forEach((card, index) => {
        if (!card.dataset.reviewDate) {
          card.dataset.reviewDate = currentWeekDates()[index] || '';
        }
      });
    }

    function renderWeeklySummary(week = '0') {
      selectedSummaryWeek = String(week);
      const response = api.getWeeklySummary ? api.getWeeklySummary(Number(week)) : {};
      const data = response.weeklySummary || weeklyCopy[week] || weeklyCopy[0];
      const dailyOverviews = visibleDailyOverviews(data.dailyOverviews || []);
      const relatedMemories = data.relatedMemories || [];
      document.getElementById('summaryPanelTitle').textContent = '周度总结';
      document.getElementById('summaryPanelMeta').textContent = data.dateRange || data.meta || '';
      document.querySelectorAll('.week-chip').forEach(chip => chip.classList.toggle('active', chip.dataset.week === String(week)));
      document.getElementById('summaryPanelBody').innerHTML = `
        <div class="summary-hero-detail">
          <div class="summary-kicker">WEEKLY REVIEW</div>
          <h3>${escapeHtml(data.focus || data.meta || '周度总结')}</h3>
          <p>${escapeHtml(data.overview || '')}</p>
        </div>
        <div class="summary-section-title"><h3>这一周可以怎样理解</h3><span>最近四周</span></div>
        <div class="card">
          <div class="summary-story">
            <div class="story-row"><b>主要主线</b><p>${escapeHtml(data.focus || '')}</p></div>
            <div class="story-row"><b>适合回看</b><p>${escapeHtml(data.reviewSuggestion || data.review || '')}</p></div>
          </div>
        </div>
        <div class="summary-section-title"><h3>每日概述</h3><span>点击进入当天回顾</span></div>
        <div class="daily-overview-track">
          ${dailyOverviews.map((item, index) => `<button class="daily-overview-card" data-review-date="${escapeHtml(dailyOverviewDate(item, index))}"><b>${escapeHtml(item.weekday || item.date || item.targetDate || '')}</b><p>${escapeHtml(item.summary || '')}</p><span>${escapeHtml((item.tags || []).join(' · '))}</span></button>`).join('')}
        </div>
        <div class="summary-section-title"><h3>相关片段</h3><span>从日期中继续</span></div>
        <div class="summary-memory-list">
          ${relatedMemories.map(item => `<button class="summary-memory" data-go="calendarPage"><span><b>${escapeHtml(item.title)}</b><span>${escapeHtml(item.subtitle || item.targetDate || '')}</span></span><i>›</i></button>`).join('')}
        </div>`;
      bindDailyOverviewClicks();
    }

    function openSummaryPanel(type, initialDateMode = '') {
      const panel = document.getElementById('summaryPanel');
      const picker = document.getElementById('summaryMonthPicker');
      const weekPicker = document.getElementById('summaryWeekPicker');
      panel.classList.remove('closing');
      panel.classList.add('active');
      picker.style.display = type === 'monthly' ? '' : 'none';
      weekPicker.style.display = type === 'weekly' ? '' : 'none';
      if (type === 'monthly') {
        renderMonthlySummary('2025', '5');
        return;
      }
      if (type === 'weekly') {
        renderWeeklySummary('0');
        return;
      }
      weekPicker.style.display = 'none';
      const data = summaryCopy[type === 'current-week' ? 'currentWeek' : type] || summaryCopy.currentWeek;
      document.getElementById('summaryPanelTitle').textContent = data.title;
      document.getElementById('summaryPanelMeta').textContent = data.meta;
      document.getElementById('summaryPanelBody').innerHTML = data.body;
      bindDailyOverviewClicks();
    }

    function restoreSummaryPanel(context) {
      if (!context || context.panel !== 'weekly') return;
      openSummaryPanel('weekly');
      renderWeeklySummary(context.week || selectedSummaryWeek || '0');
    }

    window.restoreSummaryPanel = restoreSummaryPanel;

    function closeSummaryPanel() {
      const panel = document.getElementById('summaryPanel');
      panel.classList.add('closing');
      setTimeout(() => panel.classList.remove('active', 'closing'), 280);
    }

    document.querySelectorAll('[data-summary]').forEach(btn => {
      btn.onclick = () => openSummaryPanel(btn.dataset.summary);
    });
    document.getElementById('summaryPanelBack').onclick = closeSummaryPanel;
    document.querySelectorAll('.year-chip').forEach(chip => {
      chip.onclick = () => renderMonthlySummary(chip.dataset.year, selectedSummaryMonth);
    });
    document.querySelectorAll('.month-chip').forEach(chip => {
      chip.onclick = () => renderMonthlySummary(selectedSummaryYear, chip.dataset.month);
    });
    document.querySelectorAll('.week-chip').forEach(chip => {
      chip.onclick = () => renderWeeklySummary(chip.dataset.week);
    });
    document.getElementById('summaryPanelBody').addEventListener('click', e => {
      const card = e.target.closest('.daily-overview-card');
      if (!card) return;
      openDailyOverviewReview(card.dataset.reviewDate);
    });
