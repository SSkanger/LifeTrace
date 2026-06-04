function showToast(text) { const t = document.getElementById('toast'); t.textContent = text; t.classList.add('active'); setTimeout(() => t.classList.remove('active'), 1600); }
    function favoriteDateLabel(key) {
      const match = String(key).match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
      if (!match) return key;
      return `${match[1]} 年 ${match[2]} 月 ${match[3]} 日`;
    }

    function favoriteDateIso(key) {
      const match = String(key).match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
      if (!match) return '';
      return `${match[1]}-${String(match[2]).padStart(2, '0')}-${String(match[3]).padStart(2, '0')}`;
    }

    function renderAccountFavorites() {
      const box = document.getElementById('accountFavorites');
      if (!box) return;
      const items = [...savedDays].sort().reverse();
      if (!items.length) {
        box.innerHTML = '<div class="account-empty">还没有收藏的每日回顾</div>';
        return;
      }
      box.innerHTML = items.map(key => `
        <button class="favorite-entry" data-favorite-date="${favoriteDateIso(key)}">
          <span><b>${escapeHtml(favoriteDateLabel(key))}</b><em>每日回顾</em></span>
          <i>›</i>
        </button>
      `).join('');
    }

    function openAccountPanel() {
      renderAccountFavorites();
      document.getElementById('accountPanel')?.classList.add('active');
      document.getElementById('accountScrim')?.classList.add('active');
    }

    function closeAccountPanel() {
      document.getElementById('accountPanel')?.classList.remove('active');
      document.getElementById('accountScrim')?.classList.remove('active');
    }

    document.getElementById('profileBtn')?.addEventListener('click', openAccountPanel);
    document.getElementById('accountScrim')?.addEventListener('click', closeAccountPanel);
    document.getElementById('accountSettingsBtn')?.addEventListener('click', closeAccountPanel);
    document.getElementById('accountFavorites')?.addEventListener('click', e => {
      const entry = e.target.closest('[data-favorite-date]');
      if (!entry) return;
      closeAccountPanel();
      openDailyReview(entry.dataset.favoriteDate, { targetPage: 'homePage' });
    });

    function updateFavoriteButton() {
      const btn = document.getElementById('saveMemoryBtn');
      if (!btn) return;
      const isFavorited = selectedDay !== null && savedDays.has(dayKey(selectedDay));
      btn.textContent = isFavorited ? '已收藏' : '收藏记忆';
      btn.classList.toggle('is-favorited', isFavorited);
    }
    function playFavoriteMotion(btn, isFavorited, e) {
      const rect = btn.getBoundingClientRect();
      btn.style.setProperty('--tap-x', `${e.clientX - rect.left}px`);
      btn.style.setProperty('--tap-y', `${e.clientY - rect.top}px`);
      btn.classList.remove('pulse', 'unpulse');
      void btn.offsetWidth;
      btn.classList.add(isFavorited ? 'pulse' : 'unpulse');
      setTimeout(() => btn.classList.remove('pulse', 'unpulse'), 460);
    }
    document.getElementById('saveMemoryBtn').onclick = e => {
      if (selectedDay === null) selectedDay = 14;
      const key = dayKey(selectedDay);
      const isFavorited = !savedDays.has(key);
      if (isFavorited) {
        savedDays.add(key);
      } else {
        savedDays.delete(key);
      }
      localStorage.setItem(savedDaysStorageKey, JSON.stringify([...savedDays]));
      renderCalendar();
      updateSelectedDayCopy();
      updateFavoriteButton();
      renderAccountFavorites();
      playFavoriteMotion(e.currentTarget, isFavorited, e);
    };
    loadTodaySummary();
    boot();
    updateFavoriteButton();

