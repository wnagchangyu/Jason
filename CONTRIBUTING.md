# 改代码 / 加功能指南

这份文档写给"过几个月回来改东西的自己"，照着做就不会漏步骤。

## 一、目录分工

| 目录 | 是什么 |
| --- | --- |
| `dafeiyu-pet/` | Windows 桌面版。核心是 `pet.py`，纯 ctypes 调 user32/gdi32 |
| `dafeiyu-pet-android/` | 安卓版。核心是 `PetService.java`（悬浮窗）和 `MainActivity.java`（界面） |
| `dafeiyu-pet/assets/sprites/` | **母版立绘**（透明 PNG，240px 高） |
| `dafeiyu-pet-android/app/src/main/assets/sprites/` | 安卓工程里的副本 |

> 两边立绘是**两份拷贝**，不是软链。改了母版一定要同步过去，否则手机上还是旧表情。

## 二、本地环境

**电脑版**

```bash
pip install pillow
python dafeiyu-pet/pet.py
```

**安卓版**

- JDK 17 或 21
- Android SDK：platform-34 + build-tools 34.0.0
- Gradle 8.7+（AGP 8.5.2）

打包：

```bash
cd dafeiyu-pet-android
gradle assembleDebug
```

产物 `app/build/outputs/apk/debug/app-debug.apk`。

> 本机已经配好一套环境（`重新打包.bat` 里写死了路径），双击即可。换电脑就用 Android Studio 打开工程。

## 三、常见改动

### 1. 加 / 换表情（最容易漏同步）

```
① 白底立绘放进  dafeiyu-pet/assets/raw/xxx.jpg
② 跑            python dafeiyu-pet/build_assets.py
③ 得到           dafeiyu-pet/assets/sprites/xxx.png（自动抠背景、裁边、统一高度）
④ 拷一份到       dafeiyu-pet-android/app/src/main/assets/sprites/xxx.png
⑤ 安卓端加名字    PetService.java 的 EXPRESSIONS 数组
⑥ 两边重新打包
```

`build_assets.py` 做的事：从四边 flood fill 去白底 → 只保留最大连通区域（去掉散落的星星、特效符号）→ 边缘轻微羽化 → 按内容裁边 → 缩放到统一高度。

### 2. 改台词

| 平台 | 位置 |
| --- | --- |
| 电脑 | `pet.py` 里的 `LINES_IDLE` / `LINES_CLICK` / `LINES_DRAG` / `LINES_GREET` / `LINES_MOOD` |
| 安卓 | `PetService.java` 里的 `LINES_IDLE` / `LINES_CLICK` / `LINES_DRAG` / `greeting()` |

### 3. 改大小

| 平台 | 怎么改 |
| --- | --- |
| 电脑 | 右键菜单「大小」，或改 `%APPDATA%\dafeiyu-pet\config.json` 的 `scale` |
| 安卓 | `MainActivity.java` 的 `SIZES` 数组（默认 `{0.55, 0.75, 1.0, 1.3}`）；`PetService` 里 `BASE_WIDTH_DP = 150f` 是基准宽度 |

### 4. 发版

安卓端每次发版记得改 `app/build.gradle.kts`：

```kotlin
versionCode = 3        // 每次 +1
versionName = "1.2"    // 给用户看的
```

`versionCode` 不变的话，手机上装不上去（会提示已安装更高版本）。

## 四、提交与发布

```bash
git add -A
git commit -m "feat: 加了 5 个新表情"
git push
```

提交信息用 `feat / fix / docs / chore` 开头，后面写中文说明。

**发布一个可下载的版本**：

1. 打开 <https://github.com/wnagchangyu/Jason/releases/new>
2. `Choose a tag` 输入 `v1.2` → 点 `Create new tag on publish`
3. Title 写「大肥鱼桌宠 v1.2」
4. 描述里列本次改动（一两句就行）
5. 把 `大肥鱼桌宠-1.2.apk` 拖到下方附件区
6. `Publish release`

手机上以后点 release 链接就能直接下载安装，不用进仓库翻文件。

## 五、不要提交的东西

已经在 `.gitignore` 里排除，别手动加回来：

- `app/build/`、`.gradle/`、`.idea/`
- `local.properties`（里面是绝对路径，换机器会失效）
- `dafeiyu-pet/config.json`（运行时记的位置和大小）
- `__pycache__/`、`*.log`

APK 是可以提交的（6.6 MB），方便别人直接下载；不想让仓库变大，也可以只在 Release 里挂。

## 六、几个坑

- **安卓悬浮窗是矩形**：透明区域也会挡住触摸，所以窗口已经压到立绘大小，改大小时别只看好看不看误触
- **国产 ROM 会杀后台**：MIUI / ColorOS / EMUI 需要手动给自启动和电池白名单
- **电脑版透明**：靠 `UpdateLayeredWindow` 逐像素 alpha，不要把窗口改成 `WS_EX_TRANSPARENT`，那样整个窗口都会点击穿透
- **素材版权**：立绘来自公开表情包，自用没问题，别商用
