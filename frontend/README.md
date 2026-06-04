# LifeTrace Android Frontend

这是从 `LifeTrace_recovered_from_browser.html` 迁移出的安卓前端工程骨架。

## 运行方式

1. 用 Android Studio 打开当前 `frontend/` 目录。
2. 等待 Gradle 同步。
3. 选择安卓模拟器或真机运行 `app`。

当前工程使用原生 Android `WebView` 加载本地前端资源：

```text
app/src/main/assets/lifetrace/index.html
```

这样做的原因是当前 HTML 原型已经有完整视觉和交互，先以安卓壳承载可以最大程度保持界面一致，同时项目已经具备安卓 APP 结构。

## 组件化前端源码

为了让前端代码更符合正常项目开发方式，当前已经新增 Vue/Vite 源码工程：

```text
web/
```

推荐开发链路：

```text
web/src Vue 组件源码
  -> npm run build
  -> app/src/main/assets/lifetrace
  -> Android WebView
  -> APK
```

也就是说，手机上运行 APK 时仍然加载本地静态资源，不依赖 `npm run dev`。

开发 Vue 前端时：

```powershell
cd frontend/web
npm install
npm run dev
```

构建到 Android assets 时：

```powershell
cd frontend/web
npm run build
```

注意：`web/vite.config.js` 里的 `base: './'` 必须保留，否则真机通过 WebView 加载本地文件时可能找不到 JS/CSS。

## 接口层

前端可以通过下面这个对象调用安卓侧接口：

```js
window.LifeTraceAPI
```

安卓侧接口位置：

```text
app/src/main/java/com/lifetrace/app/LifeTraceBridge.java
app/src/main/java/com/lifetrace/app/LifeTraceRepository.java
```

目前接口包括：

- `getTodayOverview()`
- `getCalendarMonth(year, month)`
- `getDailyReview(date)`
- `searchMemories(query)`
- `getWeeklySummary(offset)`
- `getMonthlySummary(year, month)`
- `saveMemory(date)`

现在 `LifeTraceRepository` 返回的是 mock JSON。后续接后端时，把这里替换成网络请求或本地数据库读取即可。
