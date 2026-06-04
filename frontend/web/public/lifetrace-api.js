(function () {
  const nativeApi = window.LifeTraceAPI;

  function parseJson(value, fallback) {
    try {
      return JSON.parse(value);
    } catch (error) {
      return fallback;
    }
  }

  window.LifeTraceClient = {
    getTodayOverview() {
      if (nativeApi && nativeApi.getTodayOverview) {
        return parseJson(nativeApi.getTodayOverview(), {});
      }
      return {
        title: "今天的大部分时间，你在学习与整理之间切换",
        text: "下午在图书馆停留较久，傍晚短暂停留并拍下晚霞；晚上和朋友散步后，手机应用切换明显减少。"
      };
    },

    getCalendarMonth(year, month) {
      if (nativeApi && nativeApi.getCalendarMonth) {
        return parseJson(nativeApi.getCalendarMonth(year, month), {});
      }
      return { year, month, memoryDays: [2, 5, 7, 11, 14, 16, 19, 24, 27, 30] };
    },

    getDailyReview(date) {
      if (nativeApi && nativeApi.getDailyReview) {
        return parseJson(nativeApi.getDailyReview(date), {});
      }
      return { date, events: [] };
    },

    searchMemories(query) {
      if (nativeApi && nativeApi.searchMemories) {
        return parseJson(nativeApi.searchMemories(query), []);
      }
      return [];
    },

    getWeeklySummary(offset) {
      if (nativeApi && nativeApi.getWeeklySummary) {
        return parseJson(nativeApi.getWeeklySummary(offset), {});
      }
      return {};
    },

    getMonthlySummary(year, month) {
      if (nativeApi && nativeApi.getMonthlySummary) {
        return parseJson(nativeApi.getMonthlySummary(year, month), {});
      }
      return {};
    },

    saveMemory(date) {
      if (nativeApi && nativeApi.saveMemory) {
        return nativeApi.saveMemory(date);
      }
      return true;
    }
  };
})();
