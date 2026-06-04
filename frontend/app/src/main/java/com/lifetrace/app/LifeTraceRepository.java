package com.lifetrace.app;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URLEncoder;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class LifeTraceRepository {
    private static final String BACKEND_BASE_URL = "http://10.0.2.2:8787";
    private static final int CONNECT_TIMEOUT_MS = 4500;
    private static final int READ_TIMEOUT_MS = 12000;

    public String getTodayOverview() {
        return getBackendData("/api/today-overview", "{}");
    }

    public String getCalendarMonth(int year, int month) {
        return getBackendData("/api/calendar-month?year=" + year + "&month=" + month, "{}");
    }

    public String getDailyReview(String date) {
        String safeDate = encode(date == null ? "" : date);
        return getBackendData("/api/daily-review?date=" + safeDate, "{}");
    }

    public String searchMemories(String query) {
        String safeQuery = encode(query == null ? "" : query);
        String data = getBackendData("/api/search-memories?query=" + safeQuery, "{}");
        try {
            JSONArray results = new JSONObject(data).optJSONArray("searchResults");
            return results == null ? "[]" : results.toString();
        } catch (JSONException e) {
            return "[]";
        }
    }

    public String getWeeklySummary(int offset) {
        return getBackendData("/api/weekly-summary?offset=" + offset, "{}");
    }

    public String getMonthlySummary(int year, int month) {
        return getBackendData("/api/monthly-summary?year=" + year + "&month=" + month, "{}");
    }

    public boolean saveMemory(String date) {
        return date != null && date.length() > 0;
    }

    private String getBackendData(String path, String fallback) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(BACKEND_BASE_URL + path);
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(CONNECT_TIMEOUT_MS);
            connection.setReadTimeout(READ_TIMEOUT_MS);
            connection.setRequestProperty("Accept", "application/json");

            int statusCode = connection.getResponseCode();
            InputStream stream = statusCode >= 200 && statusCode < 300
                    ? connection.getInputStream()
                    : connection.getErrorStream();
            String body = readAll(stream);
            if (statusCode < 200 || statusCode >= 300) {
                return fallback;
            }

            JSONObject envelope = new JSONObject(body);
            if (!envelope.optBoolean("ok", false) || !envelope.has("data")) {
                return fallback;
            }
            Object data = envelope.get("data");
            if (data instanceof JSONObject || data instanceof JSONArray) {
                return data.toString();
            }
            return fallback;
        } catch (Exception e) {
            return fallback;
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private String readAll(InputStream stream) throws IOException {
        if (stream == null) {
            return "";
        }
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
        }
        return builder.toString();
    }

    private String encode(String value) {
        try {
            return URLEncoder.encode(value, StandardCharsets.UTF_8.name());
        } catch (IOException e) {
            return "";
        }
    }
}
