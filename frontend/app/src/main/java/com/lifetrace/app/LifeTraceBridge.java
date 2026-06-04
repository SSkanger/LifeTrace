package com.lifetrace.app;

import android.webkit.JavascriptInterface;

public class LifeTraceBridge {
    private final LifeTraceRepository repository;

    public LifeTraceBridge(LifeTraceRepository repository) {
        this.repository = repository;
    }

    @JavascriptInterface
    public String getTodayOverview() {
        return repository.getTodayOverview();
    }

    @JavascriptInterface
    public String getCalendarMonth(int year, int month) {
        return repository.getCalendarMonth(year, month);
    }

    @JavascriptInterface
    public String getDailyReview(String date) {
        return repository.getDailyReview(date);
    }

    @JavascriptInterface
    public String searchMemories(String query) {
        return repository.searchMemories(query);
    }

    @JavascriptInterface
    public String getWeeklySummary(int offset) {
        return repository.getWeeklySummary(offset);
    }

    @JavascriptInterface
    public String getMonthlySummary(int year, int month) {
        return repository.getMonthlySummary(year, month);
    }

    @JavascriptInterface
    public boolean saveMemory(String date) {
        return repository.saveMemory(date);
    }
}
