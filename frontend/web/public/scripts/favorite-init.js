function showToast(text) { const t = document.getElementById('toast'); t.textContent = text; t.classList.add('active'); setTimeout(() => t.classList.remove('active'), 1600); }
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
      playFavoriteMotion(e.currentTarget, isFavorited, e);
    };
    loadTodaySummary();
    boot();
    updateFavoriteButton();

