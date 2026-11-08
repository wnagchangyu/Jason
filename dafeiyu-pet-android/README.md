# 大肥鱼桌宠 · 安卓版 🐋📱

把桌面上那只大肥鱼搬到手机上：**悬浮在所有应用之上**，能拖、能戳、会说话。

> 和电脑版共用同一套立绘素材，代码是纯 Java + 原生 API，不依赖任何第三方库。

## ✅ 已经打好包了（v1.1 · 2026-11-08）

`大肥鱼桌宠-1.1.apk`（6.65 MB）就在本文件夹里，直接装就行：

1. 传到手机（数据线 / 微信文件传输助手 / QQ 我的电脑）
2. 点开安装，允许「未知来源安装」
3. 打开 App → **开启悬浮窗权限** → 返回 → **叫她出来**

**嫌大/嫌小**：App 首页有「大小」四个档——迷你(55%) / 小(75%) / 标准(100%) / 大(130%)，
点一下立刻生效，桌宠运行中也实时变。

用的是本机已有的 JDK 21 + 本地 Gradle 8.8 + 临时下载的 Android SDK（platform-34 / build-tools 34.0.0），
**没有依赖 Android Studio**。改完代码想重新打包：双击 `重新打包.bat` 即可。

## 效果

- 悬浮窗（`TYPE_APPLICATION_OVERLAY`）飘在桌面、微信、抖音……任何界面上面
- 拖动换位置（自动记住）、单击有反应、双击比心、长按换表情
- 会呼吸浮动、随机自言自语、按时间段问候、偶尔自己溜达
- 说话用独立气泡窗口，气泡不挡触摸
- 后台常驻靠前台服务 + 通知，通知里有「让她回去」按钮

## 一、怎么打包成 APK

### 方案 0：直接双击 `重新打包.bat`（本机已配好环境）

用 JDK 21 + 本地 Gradle 8.8 + `android-build\sdk`（platform-34 / build-tools 34.0.0），
不联网也行（依赖已缓存进 `android-build\gradle-home`）。产物会复制成 `大肥鱼桌宠-1.0.apk`。

### 方案 A：Android Studio（换电脑时用）

1. 安装 [Android Studio](https://developer.android.com/studio)（自带 SDK、Gradle、JDK）
2. 打开 Studio → `File ▸ Open` → 选中这个 `dafeiyu-pet-android` 文件夹
3. 等右下角 Gradle 同步完成（第一次要联网下依赖，约几分钟）
4. 菜单 `Build ▸ Build Bundle(s) / APK(s) ▸ Build APK(s)`
5. 完成后点提示里的 `locate`，APK 在：
   ```
   app/build/outputs/apk/debug/app-debug.apk
   ```

### 方案 B：命令行（已装 SDK 的话）

```bash
# 项目里没带 gradle wrapper，先生成一次
gradle wrapper --gradle-version 8.7

./gradlew assembleDebug        # Windows: gradlew.bat assembleDebug
```

产物同上：`app/build/outputs/apk/debug/app-debug.apk`。

> 想装到手机上自己用，debug 包就够，不需要签名配置。

## 二、装到手机

1. 把 `app-debug.apk` 传到手机（数据线拷贝 / 微信「文件传输助手」/ QQ「我的电脑」都行）
2. 手机上点开安装，允许「安装未知来源应用」
3. 打开 App → 点 **开启悬浮窗权限** → 在系统页面里允许「显示在其他应用上层」
4. 回到 App → 点 **叫她出来**
5. 如果通知没出来：Android 13+ 要在系统设置里给这个 App 开通知权限（前台服务需要它常驻）

## 三、手机上怎么玩

| 操作 | 效果 |
| --- | --- |
| 拖动 | 换位置（松手自动记住） |
| 单击 | 被戳的反应 + 台词 |
| 双击 | 比心 ❤ |
| 长按 | 换个表情 |
| 通知栏「让她回去」 | 关掉桌宠 |
| App 里「让她回去」 | 同上 |

## 四、改东西

- **换表情 / 加表情**：把透明 PNG 放进 `app/src/main/assets/sprites/`，文件名即表情名；再在
  `PetService.java` 的 `EXPRESSIONS` 数组里加一行就行。
- **改台词**：`PetService.java` 里的 `LINES_IDLE` / `LINES_CLICK` / `LINES_DRAG` / `greeting()`。
- **改大小**：`MainActivity` 里的 `petWidth = 150f * density`，调大调小随你。
- **去掉自动溜达**：`updateWander()` 里把 `wanderVx` 恒置 0。

素材和电脑版完全一样，桌面版新增表情后，重跑一次 `build_assets.py` 再把 `assets/sprites/*.png` 拷过来即可。

## 五、已知限制

- 悬浮窗是**矩形**：立绘四周透明的地方也会挡住触摸（安卓悬浮窗没有逐像素穿透），所以窗口已经压到立绘大小；嫌挡就拖到角落。
- 转屏后位置不会自动重排（重启桌宠即可）。
- 部分国产系统（MIUI / ColorOS / EMUI）会限制后台，需要在「电池 / 自启动」里放行，否则锁屏后被清理。

## 六、目录

```
dafeiyu-pet-android/
├─ settings.gradle.kts
├─ build.gradle.kts
├─ gradle.properties
├─ app/
│  ├─ build.gradle.kts
│  └─ src/main/
│     ├─ AndroidManifest.xml
│     ├─ java/com/dafeiyu/pet/
│     │  ├─ MainActivity.java   权限、开关、状态
│     │  ├─ PetService.java     悬浮窗 + 动画 + 气泡 + 触摸
│     │  └─ PetView.java        只负责画
│     ├─ assets/sprites/*.png   24 张透明立绘
│     └─ res/                   图标、文案、主题
```

## 七、不装 Android Studio 的替代办法

- 找一台装了 Android Studio 的电脑，把整个文件夹拷过去按方案 A 打包，再把 APK 拿回来装（最快）。
- 或者把项目推到 GitHub，用免费的 Actions 跑 `./gradlew assembleDebug`，从构建产物里下载 APK。
