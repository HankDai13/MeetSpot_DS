# 前端图标与资源说明

本文件用于说明前端静态资源的放置与可选优化，适用于 **厦门大学人工智能系《数据结构》大作业** 提交材料。

## 当前状态
- Favicon 不是课程必需项，可不提供。
- 若需要完整展示，可添加 favicon 以提升页面完整度。

## 可选配置（如需美化）
- 推荐生成以下文件到 `public/`：
  - `favicon.ico`
  - `favicon-16x16.png`
  - `favicon-32x32.png`
  - `apple-touch-icon.png`
  - `android-chrome-192x192.png`
  - `android-chrome-512x512.png`

在 HTML `<head>` 中添加：
```html
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
```

## 说明
本项目重点为数据结构与算法实现，前端资源仅作为演示辅助。
