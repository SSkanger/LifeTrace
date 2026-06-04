# LifeTrace WebView Frontend

这里是 LifeTrace 的规范化 WebView 前端源码工程。

当前 Android APK 实际加载的是：

```text
frontend/app/src/main/assets/lifetrace/index.html
```

本目录用于后续组件化开发，技术栈为：

```text
Vue 3
Vite
Android WebView assets
```

## 目录

```text
web/
  index.html
  vite.config.js
  package.json
  public/
    lifetrace-api.js
    scripts/
  src/
    App.vue
    main.js
    components/
    pages/
    styles/
```

## 开发

```powershell
cd frontend/web
npm install
npm run dev
```

## 构建到 Android assets

```powershell
cd frontend/web
npm run build
```

构建输出目录已经配置为：

```text
frontend/app/src/main/assets/lifetrace
```

因此 APK 打包时仍然通过 WebView 加载本地文件：

```text
file:///android_asset/lifetrace/index.html
```

## 重要约束

- `vite.config.js` 必须保留 `base: './'`，否则真机加载本地 assets 时可能找不到 JS/CSS。
- Android 真机不应该依赖 `npm run dev`。
- 如果没有远程后端，APK 应该依赖本地 mock/fallback 数据。
- 当前迁移先保持视觉和 DOM 结构不变，后续再逐步把旧脚本逻辑改成 Vue 状态管理。
