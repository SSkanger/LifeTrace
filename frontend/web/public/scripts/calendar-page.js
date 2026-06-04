const daysEl = document.getElementById('calendarDays');
    const calendarTitle = document.getElementById('calendarTitle');
    let currentYear = 2026;
    let currentMonth = 4;
    const memoryDaysByMonth = {
      '2026-5': new Set((api.getCalendarMonth ? api.getCalendarMonth(2026, 5).memoryDays : [18, 19, 20, 21, 22, 23, 24]) || [])
    };
    let selectedDay = null;
    const savedDaysStorageKey = 'lifetrace-user-saved-days-v2';
    const savedDays = new Set(JSON.parse(localStorage.getItem(savedDaysStorageKey) || '[]').map(d => typeof d === 'number' ? `2026-5-${d}` : d));

    function monthKey() {
      return `${currentYear}-${currentMonth + 1}`;
    }

    function selectedDateText(day = selectedDay) {
      return `${currentYear} 年 ${currentMonth + 1} 月 ${day} 日`;
    }

    function selectedIsoDate(day = selectedDay) {
      if (day === null) return '';
      return `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }

    function dayKey(day) {
      return `${monthKey()}-${day}`;
    }

    function currentMemoryDays() {
      if (!memoryDaysByMonth[monthKey()] && api.getCalendarMonth) {
        const data = api.getCalendarMonth(currentYear, currentMonth + 1);
        memoryDaysByMonth[monthKey()] = new Set(data.memoryDays || []);
      }
      return memoryDaysByMonth[monthKey()] || new Set();
    }

    function updateSelectedDayCopy() {
      const selectedSection = document.querySelectorAll('#calendarPage .section-title')[1];
      const selectedTitle = selectedSection && selectedSection.querySelector('h2');
      const selectedMeta = selectedSection && selectedSection.querySelector('span');
      const reviewTitle = document.querySelector('#reviewPage .section-title h2');
      const selectedSummary = document.getElementById('selectedDaySummary');
      if (selectedDay === null) {
        if (selectedTitle) selectedTitle.textContent = '请选择想要回看的日期';
        if (selectedMeta) selectedMeta.textContent = '点击日期后查看线索';
        if (reviewTitle) reviewTitle.textContent = '日期回看';
        if (selectedSummary) selectedSummary.style.display = 'none';
        return;
      }
      if (selectedTitle) selectedTitle.textContent = `已选择 ${currentMonth + 1} 月 ${selectedDay} 日`;
      selectedReviewData = api.getDailyReview ? api.getDailyReview(selectedIsoDate()) : null;
      const hasData = selectedReviewData && selectedReviewData.hasData !== false && currentMemoryDays().has(selectedDay);
      if (selectedMeta) selectedMeta.textContent = hasData ? `${selectedReviewData.clueCount || 0} 条线索` : '线索较少';
      if (reviewTitle) reviewTitle.textContent = selectedDateText();
      if (selectedSummary) {
        selectedSummary.style.display = '';
        if (hasData) {
          const summary = selectedReviewData.selectedDaySummary || {};
          selectedSummary.innerHTML = `
            <div class="card-title">${escapeHtml(summary.headline || '摘要')}</div>
            <p>${escapeHtml(summary.abstract || '这一天已有可回看的生活线索。')}</p>
          `;
        } else {
          selectedSummary.innerHTML = `
            <div class="card-title">摘要 <span class="badge">线索较少</span></div>
            <p>这一天目前只有少量生活线索，可能无法生成完整回顾。你仍然可以进入时间线查看已有片段。</p>
            <div class="summary-strip"><span class="chip">线索不足</span><span class="chip cool">可手动补充</span></div>
          `;
        }
      }
    }

    function renderCalendar() {
      daysEl.innerHTML = '';
      calendarTitle.textContent = `${currentYear} 年 ${currentMonth + 1} 月`;
      const firstWeekday = new Date(currentYear, currentMonth, 1).getDay();
      const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
      const daysInPrevMonth = new Date(currentYear, currentMonth, 0).getDate();
      for (let i = firstWeekday - 1; i >= 0; i--) {
        const b = document.createElement('button');
        b.className = 'day muted';
        b.textContent = daysInPrevMonth - i;
        daysEl.appendChild(b);
      }
      for (let d = 1; d <= daysInMonth; d++) {
        const b = document.createElement('button');
        b.className = 'day' + (d === selectedDay ? ' active-day' : '') + (savedDays.has(dayKey(d)) ? ' selected' : '');
        b.textContent = d;
        b.onclick = () => {
          selectedDay = d;
          renderCalendar();
          updateSelectedDayCopy();
          updateFavoriteButton();
        };
        daysEl.appendChild(b);
      }
    }

    function switchMonth(step) {
      currentMonth += step;
      if (currentMonth < 0) {
        currentMonth = 11;
        currentYear -= 1;
      }
      if (currentMonth > 11) {
        currentMonth = 0;
        currentYear += 1;
      }
      selectedDay = null;
      renderCalendar();
      updateSelectedDayCopy();
      updateFavoriteButton();
      const animClass = step > 0 ? 'month-slide-left' : 'month-slide-right';
      daysEl.classList.remove('month-slide-left', 'month-slide-right');
      void daysEl.offsetWidth;
      daysEl.classList.add(animClass);
    }

    daysEl.addEventListener('animationend', () => {
      daysEl.classList.remove('month-slide-left', 'month-slide-right');
    });
    document.getElementById('prevMonthBtn').onclick = () => switchMonth(-1);
    document.getElementById('nextMonthBtn').onclick = () => switchMonth(1);
    renderCalendar();
    updateSelectedDayCopy();

