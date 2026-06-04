const events = [
      { time: '08:10', type: 'study', title: '早课与通勤', text: '从宿舍到教学楼，课程表显示上午有一节专业课。手机使用较少，状态比较集中。', tags: ['课程表', '教学楼', '低切换'] },
      { time: '15:20', type: 'study', title: '图书馆停留 2 小时 48 分钟', text: '位置停留显示你在图书馆区域待到傍晚，期间多次打开文档与浏览器。', tags: ['图书馆', '资料整理', '学习'], photo: { style: 'library', title: '图书馆自习区照片', meta: '照片元数据 · 15:37' } },
      { time: '18:34', type: 'life', title: '校园晚霞照片', text: '傍晚离开图书馆后，你在校园路口短暂停留，并拍下了一张晚霞照片。', tags: ['照片', '晚霞', '校园'], photo: { style: 'sunset', title: '校园路口的晚霞', meta: '相册照片 · 18:34' } },
      { time: '21:12', type: 'life', title: '操场附近散步聊天', text: '晚上位置轨迹在操场附近缓慢移动，手机几乎没有再切换应用，可能是一段放松时间。', tags: ['散步', '朋友', '休息'], photo: { style: 'walk', title: '操场附近夜间照片', meta: '照片线索 · 21:18' } }
    ];
    function renderEventPhoto(photo) {
      if (!photo) return '';
      const style = escapeHtml(photo.style || 'memory');
      const title = escapeHtml(photo.title || '照片线索');
      const meta = escapeHtml(photo.meta || '照片线索');
      const src = photo.src || photo.url || photo.path || '';
      const image = src ? `<img src="${escapeHtml(src)}" alt="${title}" loading="lazy">` : '';
      return `<div class="event-photo ${style}${src ? ' has-image' : ''}">${image}<div class="photo-caption"><b>${title}</b><span>${meta}</span></div></div>`;
    }

    function ensureTimelineDetailPanel() {
      let panel = document.getElementById('timelineDetailPanel');
      if (panel) return panel;
      panel = document.createElement('div');
      panel.className = 'timeline-detail-panel';
      panel.id = 'timelineDetailPanel';
      panel.innerHTML = `
        <div class="timeline-detail-bar">
          <button class="timeline-detail-back" id="timelineDetailBack">&#8249;</button>
          <div class="timeline-detail-title">
            <h2 id="timelineDetailTitle">\u7247\u6bb5\u8be6\u60c5</h2>
            <span id="timelineDetailMeta">\u65f6\u95f4\u7ebf\u7247\u6bb5</span>
          </div>
        </div>
        <div id="timelineDetailBody"></div>`;
      document.querySelector('.phone').appendChild(panel);
      document.getElementById('timelineDetailBack').onclick = closeTimelineDetail;
      return panel;
    }

    function closeTimelineDetail() {
      const panel = document.getElementById('timelineDetailPanel');
      if (!panel) return;
      panel.classList.add('closing');
      setTimeout(() => panel.classList.remove('active', 'closing'), 280);
    }

    function normalizeList(value) {
      if (!value) return [];
      return Array.isArray(value) ? value : [value];
    }

    function renderDetailEvidence(ev) {
      const evidence = [
        ...normalizeList(ev.evidence),
        ...normalizeList(ev.sourceItems).map(item => `${item.label || ''}${item.value ? ': ' + item.value : ''}`),
        ...normalizeList(ev.locations).map(item => item.name || item.label || item),
        ...normalizeList(ev.apps).map(item => item.name ? `${item.name}${item.duration ? ' / ' + item.duration : ''}` : item)
      ].filter(Boolean);
      if (!evidence.length) {
        evidence.push(
          `\u65f6\u95f4\u6807\u8bb0: ${ev.time || ev.timeRange || '-'}`,
          `\u7247\u6bb5\u7c7b\u578b: ${ev.type || '\u8bb0\u5fc6\u7247\u6bb5'}`
        );
      }
      return evidence.map(item => `<div class="detail-evidence">${escapeHtml(item)}</div>`).join('');
    }

    function openTimelineDetail(ev) {
      const panel = ensureTimelineDetailPanel();
      const time = ev.time || ev.timeRange || '';
      const title = ev.title || '\u7247\u6bb5\u8be6\u60c5';
      const text = ev.detail || ev.detailText || ev.text || ev.description || '';
      const tags = ev.tags || [];
      document.getElementById('timelineDetailTitle').textContent = title;
      document.getElementById('timelineDetailMeta').textContent = time ? `${time} · \u6bcf\u65e5\u6982\u89c8\u65f6\u95f4\u7ebf` : '\u6bcf\u65e5\u6982\u89c8\u65f6\u95f4\u7ebf';
      document.getElementById('timelineDetailBody').innerHTML = `
        <div class="detail-hero">
          <div class="event-time">${escapeHtml(time)}</div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(text)}</p>
          <div class="tags">${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}</div>
        </div>
        ${renderEventPhoto(ev.photo || (ev.photos && ev.photos[0]))}
        <div class="detail-section-title"><h3>\u7ebf\u7d22\u6765\u6e90</h3><span>\u4f4d\u7f6e / App / \u7167\u7247</span></div>
        <div class="detail-evidence-list">${renderDetailEvidence(ev)}</div>
        <div class="detail-section-title"><h3>\u8bb0\u5fc6\u89e3\u8bfb</h3><span>LifeTrace</span></div>
        <div class="card"><p>${escapeHtml(ev.insight || ev.summary || '\u8fd9\u4e2a\u65f6\u95f4\u6bb5\u7531\u65f6\u95f4\u3001\u4f4d\u7f6e\u3001App \u4f7f\u7528\u548c\u7167\u7247\u7ebf\u7d22\u5171\u540c\u7ec4\u6210\uff0c\u9002\u5408\u4f5c\u4e3a\u5f53\u5929\u56de\u987e\u4e2d\u7684\u72ec\u7acb\u7247\u6bb5\u7ee7\u7eed\u8ffd\u6eaf\u3002')}</p></div>`;
      panel.classList.remove('closing');
      panel.classList.add('active');
      panel.scrollTop = 0;
    }

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
        const photoHtml = renderEventPhoto(ev.photo || (ev.photos && ev.photos[0]));
        const tags = ev.tags || [];
        item.innerHTML = `<div class="card"><div class="event-time">${escapeHtml(ev.time || ev.timeRange || '')}</div><h3>${escapeHtml(ev.title)}</h3><p>${escapeHtml(ev.text || ev.description || '')}</p>${photoHtml}<div class="tags">${tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}</div></div>`;
        item.onclick = () => openTimelineDetail(ev);
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
    ensureTimelineDetailPanel();
    document.getElementById('timelineDetailBack').onclick = closeTimelineDetail;
