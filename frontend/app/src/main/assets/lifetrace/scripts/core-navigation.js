const pages = [...document.querySelectorAll('.page')];
    const navs = [...document.querySelectorAll('.nav-btn')];
    const routeMap = {
      home: 'homePage', calendar: 'calendarPage', review: 'reviewPage', search: 'searchPage', summary: 'summaryPage', permission: 'permissionPage', error: 'stateErrorPage', empty: 'stateEmptyPage', success: 'stateSuccessPage'
    };
    const nameMap = Object.fromEntries(Object.entries(routeMap).map(([k, v]) => [v, k]));
    const api = window.LifeTraceClient || {};
    let selectedReviewData = null;
    let latestSearchResults = [];
    let reviewBackContext = { targetPage: 'calendarPage' };

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      }[ch]));
    }

    function loadTodaySummary() {
      if (!api.getTodayOverview) return;
      const data = api.getTodayOverview();
      const summary = data.homeTodaySummary || data;
      if (!summary) return;
      document.getElementById('todaySummaryTitle').textContent = summary.headline || data.title || '今日摘要';
      document.getElementById('todaySummaryText').textContent = summary.paragraph || data.text || '';
      const tags = summary.chips || data.tags || [];
      document.getElementById('todaySummaryTags').innerHTML = tags.map((tag, index) => `<span class="chip${index === 1 ? ' cool' : ''}">${escapeHtml(tag)}</span>`).join('');
    }

    function playNavMotion(btn) {
      if (!btn) return;
      btn.classList.remove('nav-bounce');
      void btn.offsetWidth;
      btn.classList.add('nav-bounce');
      setTimeout(() => btn.classList.remove('nav-bounce'), 380);
    }

    function go(id, push = true, motionTarget = null) {
      pages.forEach(p => p.classList.toggle('active', p.id === id));
      const activeNav = id.includes('calendar') || id === 'reviewPage' || id === 'stateLoadingPage' || id === 'stateEmptyPage' ? 'calendarPage' : id.includes('search') ? 'searchPage' : id.includes('summary') ? 'summaryPage' : id === 'homePage' ? 'homePage' : '';
      navs.forEach(n => n.classList.toggle('active', n.dataset.go === activeNav));
      const backBtn = document.getElementById('backBtn');
      const topbar = document.querySelector('.topbar');
      const isMainPage = ['homePage', 'calendarPage', 'searchPage', 'summaryPage'].includes(id);
      if (topbar) {
        topbar.classList.toggle('subpage-mode', !isMainPage);
        topbar.classList.remove('permission-mode');
      }
      if (backBtn) {
        backBtn.classList.toggle('is-hidden', isMainPage);
      }
      playNavMotion(motionTarget || navs.find(n => n.dataset.go === activeNav));
      document.querySelector('main').scrollTop = 0;
      if (id === 'searchPage') {
        clearSearchPage();
      }
      if (push) location.hash = nameMap[id] || id.replace('Page', '');
      if (id === 'reviewPage') {
        renderTimeline();
        updateFavoriteButton();
      }
    }

    function setReviewBackContext(context) {
      if (!context) return;
      reviewBackContext = typeof context === 'string' ? { targetPage: context } : context;
    }

    window.setReviewBackContext = setReviewBackContext;

    document.addEventListener('click', e => {
      const target = e.target.closest('[data-go]');
      if (target) {
        if (target.classList.contains('nav-btn') && window.closeTimelineDetail) {
          window.closeTimelineDetail(true);
        }
        if (target.dataset.go === 'reviewPage') {
          const activePage = pages.find(p => p.classList.contains('active'));
          setReviewBackContext((activePage && activePage.id) || 'calendarPage');
        }
        go(target.dataset.go, true, target.classList.contains('nav-btn') ? target : null);
        if (target.classList.contains('nav-btn')) target.blur();
      }
    });
    document.getElementById('backBtn').onclick = () => handleBack();

    function handleBack() {
      const activePage = pages.find(p => p.classList.contains('active'));
      const id = activePage ? activePage.id : 'homePage';
      const backMap = {
        calendarPage: 'homePage',
        reviewPage: 'calendarPage',
        searchPage: 'homePage',
        summaryPage: 'homePage',
        permissionPage: 'homePage',
        stateLoadingPage: 'calendarPage',
        stateErrorPage: 'permissionPage',
        stateEmptyPage: 'calendarPage',
        stateSuccessPage: 'reviewPage'
      };
      if (id === 'homePage') return;
      if (id === 'reviewPage') {
        const context = reviewBackContext || { targetPage: 'calendarPage' };
        go(context.targetPage || 'calendarPage');
        if (context.restore && context.targetPage === 'summaryPage' && window.restoreSummaryPanel) {
          setTimeout(() => window.restoreSummaryPanel(context.restore), 0);
        }
        reviewBackContext = { targetPage: 'calendarPage' };
        return;
      }
      go(backMap[id] || 'homePage');
    }

    function clearSearchPage() {
      document.getElementById('searchEntryInput').value = '';
      document.getElementById('searchInput').value = '';
      document.getElementById('searchResults').innerHTML = '';
      document.getElementById('searchGuide').style.display = '';
      document.getElementById('searchPanel').classList.remove('active', 'closing');
    }

    function openSearchPanel(query = '') {
      const panel = document.getElementById('searchPanel');
      const input = document.getElementById('searchInput');
      panel.classList.remove('closing');
      panel.classList.add('active');
      document.getElementById('searchResults').innerHTML = '';
      document.getElementById('searchGuide').style.display = '';
      input.value = query;
      setTimeout(() => input.focus(), 0);
    }

    function closeSearchPanel() {
      const panel = document.getElementById('searchPanel');
      panel.classList.add('closing');
      setTimeout(() => {
        panel.classList.remove('active', 'closing');
        document.getElementById('searchInput').value = '';
        document.getElementById('searchResults').innerHTML = '';
        document.getElementById('searchGuide').style.display = '';
      }, 280);
    }

    function submitSearch() {
      const query = document.getElementById('searchInput').value.trim();
      if (!query) {
        document.getElementById('searchResults').innerHTML = '';
        document.getElementById('searchGuide').style.display = '';
        return;
      }
      showToast('正在匹配照片、位置和日程线索…');
      latestSearchResults = api.searchMemories ? api.searchMemories(query) : [];
      setTimeout(renderResults, 320);
    }

    function boot() {
      const hash = location.hash.replace('#', '');
      const page = routeMap[hash] || (document.getElementById(hash) ? hash : 'homePage');
      go(page, false);
      if (page === 'searchPage') setTimeout(clearSearchPage, 0);
    }
    window.addEventListener('hashchange', boot);
    window.addEventListener('pageshow', () => {
      if (document.getElementById('searchPage').classList.contains('active')) clearSearchPage();
    });

