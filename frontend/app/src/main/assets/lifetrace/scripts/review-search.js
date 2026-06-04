const events = [
      { time: '08:10', type: 'study', title: '早课与通勤', text: '从宿舍到教学楼，课程表显示上午有一节专业课。手机使用较少，状态比较集中。', tags: ['课程表', '教学楼', '低切换'] },
      { time: '15:20', type: 'study', title: '图书馆停留 2 小时 48 分钟', text: '位置停留显示你在图书馆区域待到傍晚，期间多次打开文档与浏览器。', tags: ['图书馆', '资料整理', '学习'], photo: { style: 'library', title: '图书馆自习区照片', meta: '照片元数据 · 15:37' } },
      { time: '18:34', type: 'life', title: '校园晚霞照片', text: '傍晚离开图书馆后，你在校园路口短暂停留，并拍下了一张晚霞照片。', tags: ['照片', '晚霞', '校园'], photo: { style: 'sunset', title: '校园路口的晚霞', meta: '相册照片 · 18:34' } },
      { time: '21:12', type: 'life', title: '操场附近散步聊天', text: '晚上位置轨迹在操场附近缓慢移动，手机几乎没有再切换应用，可能是一段放松时间。', tags: ['散步', '朋友', '休息'], photo: { style: 'walk', title: '操场附近夜间照片', meta: '照片线索 · 21:18' } }
    ];
    function renderTimeline() {
      const list = document.getElementById('timelineList');
      list.innerHTML = '';
      if (!selectedReviewData && api.getDailyReview) {
        selectedReviewData = api.getDailyReview(selectedIsoDate() || '2026-05-20');
      }
      const timelineEvents = selectedReviewData && selectedReviewData.events && selectedReviewData.events.length ? selectedReviewData.events : events;
      const reviewTitle = document.querySelector('#reviewPage .section-title h2');
      if (reviewTitle && selectedReviewData && selectedReviewData.date) {
        reviewTitle.textContent = selectedReviewData.date;
      }
      timelineEvents.forEach(ev => {
        const item = document.createElement('div');
        item.className = 'event';
        const photoHtml = ev.photo ? `<div class="event-photo ${ev.photo.style}"><div class="photo-caption"><b>${ev.photo.title}</b><span>${ev.photo.meta}</span></div></div>` : '';
        const tags = ev.tags || [];
        item.innerHTML = `<div class="card"><div class="event-time">${escapeHtml(ev.time || ev.timeRange || '')}</div><h3>${escapeHtml(ev.title)}</h3><p>${escapeHtml(ev.text || ev.description || '')}</p>${photoHtml}<div class="tags">${tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}</div></div>`;
        item.onclick = () => showToast('已打开片段详情：' + ev.title);
        list.appendChild(item);
      });
    }
    function renderResults() {
      const box = document.getElementById('searchResults');
      if (!document.getElementById('searchInput').value.trim()) {
        box.innerHTML = '';
        document.getElementById('searchGuide').style.display = '';
        return;
      }
      document.getElementById('searchGuide').style.display = 'none';
      if (!latestSearchResults.length) {
        box.innerHTML = `<div class="card"><p>暂时没有匹配到可展示的记忆片段。</p></div>`;
        return;
      }
      box.innerHTML = latestSearchResults.map(result => {
        const sources = result.sourceItems || [];
        return `<button class="result-card" data-go="${escapeHtml(result.targetPage || 'reviewPage')}">
          <div class="card-title">${escapeHtml(result.title)} ${result.badge ? `<span class="badge">${escapeHtml(result.badge)}</span>` : ''}</div>
          <p>${escapeHtml(result.summary || '')}</p>
          <div class="source-list">${sources.map(item => `<div class="source"><b>${escapeHtml(item.label)}</b><span>${escapeHtml(item.value)}</span></div>`).join('')}</div>
        </button>`;
      }).join('');
    }
    document.getElementById('searchEntryInput').onclick = () => openSearchPanel(document.getElementById('searchEntryInput').value.trim());
    document.getElementById('searchEntryInput').onfocus = () => openSearchPanel(document.getElementById('searchEntryInput').value.trim());
    document.getElementById('searchEntryBtn').onclick = () => {
      openSearchPanel(document.getElementById('searchEntryInput').value.trim());
      submitSearch();
    };
    document.getElementById('searchPanelBack').onclick = () => {
      closeSearchPanel();
      document.getElementById('searchEntryInput').value = '';
    };
    document.getElementById('searchBtn').onclick = submitSearch;
    document.getElementById('searchInput').onkeydown = e => {
      if (e.key === 'Enter') submitSearch();
    };
    document.querySelectorAll('.search-chip, .search-discovery button').forEach(chip => {
      chip.onclick = () => {
        document.getElementById('searchInput').value = chip.textContent.trim();
        submitSearch();
      };
    });
    document.querySelectorAll('.example-chip').forEach(chip => {
      chip.onclick = () => {
        openSearchPanel(chip.textContent.trim());
        submitSearch();
      };
    });

