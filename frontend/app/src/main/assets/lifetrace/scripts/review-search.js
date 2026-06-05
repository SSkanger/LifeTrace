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
      if (!src) return '';
      const image = src ? `<img src="${escapeHtml(src)}" alt="${title}" loading="lazy">` : '';
      return `<div class="event-photo ${style}${src ? ' has-image' : ''}">${image}<div class="photo-caption"><b>${title}</b><span>${meta}</span></div></div>`;
    }

    function ensureTimelineDetailPanel() {
      let panel = document.getElementById('timelineDetailPanel');
      if (panel) {
        ensureDetailEditor(panel);
        return panel;
      }
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
        <div id="timelineDetailBody"></div>
        <div class="detail-edit-panel" id="detailEditPanel">
          <div class="detail-edit-head">
            <button id="detailEditCancel">\u53d6\u6d88</button>
            <strong>\u7f16\u8f91\u7247\u6bb5</strong>
            <button id="detailEditDone">\u5b8c\u6210</button>
          </div>
          <label class="detail-time-field" id="detailTimeField"><span>\u65f6\u95f4</span><input id="detailEditTime" autocomplete="off" inputmode="none" readonly><div class="time-wheel" id="detailTimeWheel"><div class="time-picker-summary"><strong id="detailActiveTimeText">08:10</strong><button type="button" id="detailTimeNow">\u73b0\u5728</button></div><div class="time-mode"><button type="button" data-time-part="start">\u5f00\u59cb\u65f6\u95f4</button><button type="button" data-time-part="end">\u7ed3\u675f\u65f6\u95f4</button></div><div class="time-wheel-head"><span>\u65f6</span><span>\u5206</span></div><div class="time-wheel-columns"><div class="time-scroll" id="detailWheelHour" data-max="23"></div><div class="time-scroll" id="detailWheelMinute" data-max="59"></div></div></div><em class="detail-edit-error" id="detailEditTimeError"></em></label>
          <label><span>\u5730\u70b9</span><input id="detailEditLocation" autocomplete="off"></label>
          <label><span>\u4e3b\u9898</span><input id="detailEditTitle" autocomplete="off"></label>
          <label class="detail-edit-text"><span>\u5185\u5bb9</span><textarea id="detailEditText"></textarea></label>
        </div>`;
      document.querySelector('.phone').appendChild(panel);
      document.getElementById('timelineDetailBack').onclick = closeTimelineDetail;
      document.getElementById('detailEditCancel').onclick = closeDetailEditor;
      document.getElementById('detailEditDone').onclick = saveDetailEditor;
      bindTimelineDetailPanel(panel);
      return panel;
    }

    function bindTimelineDetailPanel(panel) {
      if (!panel || panel.dataset.heroEditBound === 'true') return;
      panel.dataset.heroEditBound = 'true';
      panel.addEventListener('click', event => {
        if (isDetailHeroEvent(event)) {
          openDetailEditor();
        }
      });
      panel.addEventListener('touchend', event => {
        if (isDetailHeroEvent(event)) {
          event.preventDefault();
          openDetailEditor();
        }
      });
    }

    function isDetailHeroEvent(event) {
      if (event.target.closest && event.target.closest('#detailEditPanel')) return false;
      const hero = document.getElementById('detailHeroCard');
      if (!hero) return false;
      if (event.target.closest && event.target.closest('#detailHeroCard')) return true;
      const point = event.changedTouches ? event.changedTouches[0] : event;
      if (!point || point.clientX == null || point.clientY == null) return false;
      const rect = hero.getBoundingClientRect();
      return point.clientX >= rect.left && point.clientX <= rect.right && point.clientY >= rect.top && point.clientY <= rect.bottom;
    }

    function ensureDetailEditor(panel = document.getElementById('timelineDetailPanel')) {
      if (!panel) return null;
      let editor = document.getElementById('detailEditPanel');
      if (!editor) {
        editor = document.createElement('div');
        editor.className = 'detail-edit-panel';
        editor.id = 'detailEditPanel';
        editor.innerHTML = `
          <div class="detail-edit-head">
            <button id="detailEditCancel">\u53d6\u6d88</button>
            <strong>\u7f16\u8f91\u7247\u6bb5</strong>
            <button id="detailEditDone">\u5b8c\u6210</button>
          </div>
          <label class="detail-time-field" id="detailTimeField"><span>\u65f6\u95f4</span><input id="detailEditTime" autocomplete="off" inputmode="none" readonly><div class="time-wheel" id="detailTimeWheel"><div class="time-picker-summary"><strong id="detailActiveTimeText">08:10</strong><button type="button" id="detailTimeNow">\u73b0\u5728</button></div><div class="time-mode"><button type="button" data-time-part="start">\u5f00\u59cb\u65f6\u95f4</button><button type="button" data-time-part="end">\u7ed3\u675f\u65f6\u95f4</button></div><div class="time-wheel-head"><span>\u65f6</span><span>\u5206</span></div><div class="time-wheel-columns"><div class="time-scroll" id="detailWheelHour" data-max="23"></div><div class="time-scroll" id="detailWheelMinute" data-max="59"></div></div></div><em class="detail-edit-error" id="detailEditTimeError"></em></label>
          <label><span>\u5730\u70b9</span><input id="detailEditLocation" autocomplete="off"></label>
          <label><span>\u4e3b\u9898</span><input id="detailEditTitle" autocomplete="off"></label>
          <label class="detail-edit-text"><span>\u5185\u5bb9</span><textarea id="detailEditText"></textarea></label>`;
        panel.appendChild(editor);
      }
      document.getElementById('detailEditCancel').onclick = closeDetailEditor;
      document.getElementById('detailEditDone').onclick = saveDetailEditor;
      document.getElementById('detailEditTime').oninput = () => setTimeInputError('');
      initTimePicker();
      bindTimelineDetailPanel(panel);
      return editor;
    }

    function closeTimelineDetail(immediate = false) {
      const panel = document.getElementById('timelineDetailPanel');
      if (!panel) return;
      closeDetailEditor();
      if (immediate) {
        panel.classList.remove('active', 'closing');
        return;
      }
      panel.classList.add('closing');
      setTimeout(() => panel.classList.remove('active', 'closing'), 280);
    }

    window.closeTimelineDetail = closeTimelineDetail;

    function normalizeList(value) {
      if (!value) return [];
      return Array.isArray(value) ? value : [value];
    }

    function sourceItemValue(ev, pattern) {
      const item = normalizeList(ev.sourceItems).find(source => pattern.test(`${source.label || ''}${source.type || ''}`));
      return item ? (item.value || item.name || item.label || '') : '';
    }

    function firstSourceText(value) {
      const item = normalizeList(value)[0];
      if (!item) return '';
      return typeof item === 'string' ? item : (item.name || item.label || item.value || '');
    }

    function detailSources(ev, time) {
      const photo = ev.photo || (ev.photos && ev.photos[0]);
      const photoText = photo && (photo.src || photo.url || photo.path)
        ? (photo.meta || photo.title || '\u5df2\u5339\u914d\u7167\u7247')
        : '';
      return {
        time: time || '-',
        location: ev.location || firstSourceText(ev.locations) || sourceItemValue(ev, /\u4f4d\u7f6e|\u5730\u70b9|location/i) || '\u672a\u6807\u8bb0\u5730\u70b9',
        app: firstSourceText(ev.apps) || sourceItemValue(ev, /App|\u5e94\u7528/i) || '',
        photo: photoText
      };
    }

    function renderDetailEvidence(sources) {
      const rows = [
        ['\u65f6\u95f4', sources.time, 'detailEvidenceTime', 'time'],
        ['\u5730\u70b9', sources.location, 'detailEvidenceLocation', 'location'],
        ['\u7167\u7247', sources.photo, '', 'photo']
      ].filter(row => row[1]);
      return rows.map(([label, value, id, field]) => `<div class="detail-evidence"><b>${label}</b><span class="detail-editable" contenteditable="true" data-edit-field="${field}"${id ? ` id="${id}"` : ''}>${escapeHtml(value)}</span></div>`).join('');
    }

    function bindDetailEditing(panel) {
      const titleNode = document.getElementById('timelineDetailTitle');
      const metaNode = document.getElementById('timelineDetailMeta');
      const updateMeta = () => {
        const time = panel.querySelector('[data-edit-field="time"]')?.textContent.trim();
        const location = document.getElementById('detailEvidenceLocation')?.textContent.trim();
        metaNode.textContent = [time, location].filter(Boolean).join(' / ') || '\u6bcf\u65e5\u6982\u89c8\u65f6\u95f4\u7ebf';
      };
      panel.querySelectorAll('[data-edit-field]').forEach(node => {
        node.addEventListener('input', () => {
          const value = node.textContent.trim();
          if (node.dataset.editField === 'time') {
            panel.querySelectorAll('[data-edit-field="time"]').forEach(peer => {
              if (peer !== node) peer.textContent = value || '-';
            });
            const heroTime = document.getElementById('detailHeroTime');
            if (heroTime) heroTime.textContent = value || '-';
            updateMeta();
          }
          if (node.dataset.editField === 'location') {
            updateMeta();
          }
          if (node.dataset.editField === 'title') {
            titleNode.textContent = value || '\u7247\u6bb5\u8be6\u60c5';
          }
        });
      });
    }

    function openDetailEditor() {
      const editor = ensureDetailEditor();
      if (!editor) return;
      document.getElementById('detailEditTime').value = document.getElementById('detailHeroTime')?.textContent.trim() || '';
      syncTimePickerFromInput();
      document.getElementById('detailEditLocation').value = document.getElementById('detailEvidenceLocation')?.textContent.trim() || '';
      document.getElementById('detailEditTitle').value = document.getElementById('detailHeroTitle')?.textContent.trim() || '';
      document.getElementById('detailEditText').value = document.getElementById('detailHeroText')?.textContent.trim() || '';
      editor.classList.add('active');
      document.getElementById('detailTimeField')?.classList.remove('picking');
      setTimeInputError('');
    }

    window.openTimelineDetailEditor = openDetailEditor;

    function closeDetailEditor() {
      document.getElementById('detailEditPanel')?.classList.remove('active');
      document.getElementById('detailTimeField')?.classList.remove('picking');
    }

    function padTime(value) {
      return String(value).padStart(2, '0');
    }

    function initTimePicker() {
      const timeInput = document.getElementById('detailEditTime');
      const field = document.getElementById('detailTimeField');
      const wheel = document.getElementById('detailTimeWheel');
      const controls = ['detailWheelHour', 'detailWheelMinute'].map(id => document.getElementById(id));
      if (!timeInput || !field || !wheel || controls.some(item => !item)) return;
      controls.forEach(control => {
        if (!control.children.length) {
          const max = Number(control.dataset.max || 59);
          control.innerHTML = Array.from({ length: max + 1 }, (_, value) => `<button type="button" data-value="${padTime(value)}">${padTime(value)}</button>`).join('');
        }
        control.onscroll = () => {
          clearTimeout(control._snapTimer);
          control._snapTimer = setTimeout(() => {
            const value = Math.round(control.scrollTop / 32);
            setWheelValue(control, value);
            syncTimeFromPicker();
          }, 80);
        };
        control.onclick = event => {
          const option = event.target.closest('button');
          if (!option) return;
          setWheelValue(control, Number(option.dataset.value));
          syncTimeFromPicker();
        };
      });
      wheel.querySelectorAll('[data-time-part]').forEach(button => {
        button.onclick = () => setActiveTimePart(button.dataset.timePart);
      });
      document.getElementById('detailTimeNow').onclick = event => {
        event.stopPropagation();
        const now = new Date();
        setWheelValue(document.getElementById('detailWheelHour'), now.getHours());
        setWheelValue(document.getElementById('detailWheelMinute'), now.getMinutes());
        syncTimeFromPicker();
      };
      wheel.onclick = event => event.stopPropagation();
      timeInput.onclick = event => {
        event.stopPropagation();
        field.classList.add('picking');
      };
      field.querySelector('span').onclick = event => {
        event.stopPropagation();
        field.classList.add('picking');
      };
      ['detailEditLocation', 'detailEditTitle', 'detailEditText'].forEach(id => {
        const node = document.getElementById(id);
        if (node) node.onfocus = () => field.classList.remove('picking');
      });
    }

    function setWheelValue(control, value) {
      const max = Number(control.dataset.max || 59);
      const safeValue = Math.max(0, Math.min(max, Number(value) || 0));
      control.dataset.value = padTime(safeValue);
      control.scrollTop = safeValue * 32;
      control.querySelectorAll('button').forEach(button => {
        button.classList.toggle('active', button.dataset.value === control.dataset.value);
      });
    }

    function parseTimeValue(value) {
      const time = normalizeTimeInput(value);
      const [start = '08:10', end = start] = time.split('-');
      const startMatch = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(start);
      const endMatch = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(end);
      const safeStart = startMatch || /^([01]\d|2[0-3]):([0-5]\d)$/.exec('08:10');
      const safeEnd = endMatch || safeStart;
      return {
        startHour: safeStart[1],
        startMinute: safeStart[2],
        endHour: safeEnd[1],
        endMinute: safeEnd[2]
      };
    }

    function syncTimePickerFromInput() {
      const parts = parseTimeValue(document.getElementById('detailEditTime')?.value || '');
      const wheel = document.getElementById('detailTimeWheel');
      wheel.dataset.startHour = parts.startHour;
      wheel.dataset.startMinute = parts.startMinute;
      wheel.dataset.endHour = parts.endHour;
      wheel.dataset.endMinute = parts.endMinute;
      setActiveTimePart(wheel.dataset.activePart || 'start');
      updateTimeInputFromState();
    }

    function setActiveTimePart(part) {
      const wheel = document.getElementById('detailTimeWheel');
      const activePart = part === 'end' ? 'end' : 'start';
      wheel.dataset.activePart = activePart;
      wheel.querySelectorAll('[data-time-part]').forEach(button => {
        button.classList.toggle('active', button.dataset.timePart === activePart);
      });
      setWheelValue(document.getElementById('detailWheelHour'), Number(wheel.dataset[`${activePart}Hour`] || 8));
      setWheelValue(document.getElementById('detailWheelMinute'), Number(wheel.dataset[`${activePart}Minute`] || 10));
      updateActiveTimeText();
    }

    function syncTimeFromPicker() {
      const wheel = document.getElementById('detailTimeWheel');
      const activePart = wheel.dataset.activePart === 'end' ? 'end' : 'start';
      wheel.dataset[`${activePart}Hour`] = document.getElementById('detailWheelHour').dataset.value || '08';
      wheel.dataset[`${activePart}Minute`] = document.getElementById('detailWheelMinute').dataset.value || '10';
      updateTimeInputFromState();
    }

    function updateActiveTimeText() {
      const wheel = document.getElementById('detailTimeWheel');
      const hour = document.getElementById('detailWheelHour')?.dataset.value || '08';
      const minute = document.getElementById('detailWheelMinute')?.dataset.value || '10';
      const label = wheel.dataset.activePart === 'end' ? '\u7ed3\u675f ' : '\u5f00\u59cb ';
      const text = document.getElementById('detailActiveTimeText');
      if (text) text.textContent = `${label}${hour}:${minute}`;
    }

    function updateTimeInputFromState() {
      const wheel = document.getElementById('detailTimeWheel');
      const startHour = wheel.dataset.startHour || '08';
      const startMinute = wheel.dataset.startMinute || '10';
      const endHour = wheel.dataset.endHour || startHour;
      const endMinute = wheel.dataset.endMinute || startMinute;
      const start = `${startHour}:${startMinute}`;
      const end = `${endHour}:${endMinute}`;
      document.getElementById('detailEditTime').value = start === end ? start : `${start}-${end}`;
      updateActiveTimeText();
      setTimeInputError('');
    }

    function normalizeTimeInput(value) {
      return value.trim().replace(/[：]/g, ':').replace(/[—–~～至到]/g, '-').replace(/\s+/g, '');
    }

    function minutesOf(time) {
      const [hour, minute] = time.split(':').map(Number);
      return hour * 60 + minute;
    }

    function validateTimeInput(value) {
      const time = normalizeTimeInput(value);
      const pattern = /^([01]\d|2[0-3]):[0-5]\d(-([01]\d|2[0-3]):[0-5]\d)?$/;
      if (!pattern.test(time)) {
        return { valid: false, message: '\u8bf7\u8f93\u5165 08:10 \u6216 07:10-08:15 \u8fd9\u6837\u7684\u65f6\u95f4\u683c\u5f0f' };
      }
      const parts = time.split('-');
      if (parts.length === 2 && minutesOf(parts[1]) < minutesOf(parts[0])) {
        return { valid: false, message: '\u7ed3\u675f\u65f6\u95f4\u4e0d\u80fd\u65e9\u4e8e\u5f00\u59cb\u65f6\u95f4' };
      }
      return { valid: true, value: time };
    }

    function setTimeInputError(message) {
      const input = document.getElementById('detailEditTime');
      const error = document.getElementById('detailEditTimeError');
      if (input) input.classList.toggle('invalid', Boolean(message));
      if (error) error.textContent = message;
    }

    function saveDetailEditor() {
      const timeCheck = validateTimeInput(document.getElementById('detailEditTime').value);
      if (!timeCheck.valid) {
        setTimeInputError(timeCheck.message);
        document.getElementById('detailEditTime').focus();
        return;
      }
      const time = timeCheck.value;
      const location = document.getElementById('detailEditLocation').value.trim() || '\u672a\u6807\u8bb0\u5730\u70b9';
      const title = document.getElementById('detailEditTitle').value.trim() || '\u7247\u6bb5\u8be6\u60c5';
      const text = document.getElementById('detailEditText').value.trim();
      document.getElementById('detailHeroTime').textContent = time;
      document.getElementById('detailHeroTitle').textContent = title;
      document.getElementById('detailHeroText').textContent = text;
      document.getElementById('timelineDetailTitle').textContent = title;
      document.getElementById('timelineDetailMeta').textContent = [time, location].filter(Boolean).join(' / ');
      document.getElementById('detailEvidenceTime').textContent = time;
      document.getElementById('detailEvidenceLocation').textContent = location;
      closeDetailEditor();
    }

    function openTimelineDetail(ev) {
      const panel = ensureTimelineDetailPanel();
      const time = ev.time || ev.timeRange || '';
      const title = ev.title || '\u7247\u6bb5\u8be6\u60c5';
      const text = ev.detail || ev.detailText || ev.text || ev.description || '';
      const tags = ev.tags || [];
      const sources = detailSources(ev, time);
      document.getElementById('timelineDetailTitle').textContent = title;
      document.getElementById('timelineDetailMeta').textContent = [sources.time, sources.location].filter(Boolean).join(' / ');
      document.getElementById('timelineDetailBody').innerHTML = `
        <div class="detail-hero" id="detailHeroCard" role="button" tabindex="0" onclick="window.openTimelineDetailEditor && window.openTimelineDetailEditor()">
          <div class="event-time" id="detailHeroTime">${escapeHtml(sources.time)}</div>
          <h3 id="detailHeroTitle">${escapeHtml(title)}</h3>
          <p id="detailHeroText">${escapeHtml(text)}</p>
          <div class="tags">${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}</div>
        </div>
        ${renderEventPhoto(ev.photo || (ev.photos && ev.photos[0]))}
        <div class="detail-section-title"><h3>\u7ebf\u7d22\u6765\u6e90</h3><span>\u65f6\u95f4 / \u5730\u70b9 / \u7167\u7247</span></div>
        <div class="detail-evidence-list">${renderDetailEvidence(sources)}</div>
        <div class="detail-section-title"><h3>\u8bb0\u5fc6\u89e3\u8bfb</h3><span>LifeTrace</span></div>
        <div class="card"><p>${escapeHtml(ev.insight || ev.summary || '\u8fd9\u4e2a\u65f6\u95f4\u6bb5\u7531\u65f6\u95f4\u3001\u4f4d\u7f6e\u3001App \u4f7f\u7528\u548c\u7167\u7247\u7ebf\u7d22\u5171\u540c\u7ec4\u6210\uff0c\u9002\u5408\u4f5c\u4e3a\u5f53\u5929\u56de\u987e\u4e2d\u7684\u72ec\u7acb\u7247\u6bb5\u7ee7\u7eed\u8ffd\u6eaf\u3002')}</p></div>`;
      bindDetailEditing(panel);
      const heroCard = document.getElementById('detailHeroCard');
      if (heroCard) {
        heroCard.onclick = openDetailEditor;
        heroCard.ontouchend = event => {
          event.preventDefault();
          openDetailEditor();
        };
        heroCard.onkeydown = event => {
          if (event.key === 'Enter' || event.key === ' ') openDetailEditor();
        };
      }
      closeDetailEditor();
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
