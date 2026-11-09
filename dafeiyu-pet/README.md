# 大肥鱼桌宠 🐋

把「大肥鱼」放到你的 Windows 桌面上当桌宠：真·透明背景、始终置顶、能拖能戳会说话。

**造型**：本体取自官方角色设定图的**正面全身站姿**（有裙摆、白丝、小皮鞋，会呼吸、会小跳、会歪头）。
设定图原文件在 `assets/source/character_sheet.jpg`。

![预览](assets/preview.png)

## 快速开始

- **桌面快捷方式**：桌面上已经有「大肥鱼桌宠」了，双击即可（没有黑框、无控制台）
- **文件夹里**：双击 `大肥鱼桌宠.lnk`（同上）
- **备用**：双击 `start_pet.bat`（会闪一下黑框）
- **重新生成快捷方式**：右键 `install.ps1` →「使用 PowerShell 运行」
  - 想开机自动出现：`powershell -ExecutionPolicy Bypass -File install.ps1 -Startup`

> 注：本机 Windows 已移除 VBScript 引擎，所以启动器用原生快捷方式而不是 .vbs。

## 怎么玩

| 操作 | 效果 |
| --- | --- |
| 左键拖动 | 把她挪到任意位置（会自动记住） |
| 单击 | 被戳一下的反应 + 台词 |
| 双击 | 比心 ❤ |
| 右键 | 菜单：说句话 / 换表情 / 大小 / 随机走动 / 安静模式 / 藏起来 10 分钟 / 退出 |
| 透明处点击 | 直接穿透到下面的窗口，不会挡住你干活 |

## 她会做什么

- **会换表情**：开心笑、比心、害羞、生气、睡着、疑惑 —— 六张脸轮流换，被戳时随机切一张
- 待机时**轻轻左右摇摆 + 上下呼吸**，走路时幅度更大，像真的在挪步
- **被戳一下会弹一下**（横向撑开、纵向压扁再回弹）
- 隔一会儿自言自语（按时间段问候：早上好 / 中午了 / 晚上好 / 这么晚还不睡）
- 开着「随机走动」时会在屏幕底部溜达

右键菜单里的开关：**待机小动作**（晃/跳）、**表情贴纸**（另外弹出半身表情，默认关闭）。

## 自定义

- **换本体**：把新的设定图放到 `assets/source/character_sheet.jpg`（正面视图在左上），跑
  ```
  python build_body.py
  ```
  会裁出正面全身、去白底、生成 `assets/full/body.png`。裁剪范围在脚本里的 `CROP` 调。
  歪头/蹦跳/害羞这几个姿势是运行时旋转缩放生成的，改 `pet.py` 的 `BODY_POSES`。
- **24 张半身表情**：还在 `assets/sprites/` 里，暂时没用上，以后想加「说话时冒出表情」可以直接接。
- **改台词**：打开 `pet.py`，改 `LINES_IDLE` / `LINES_CLICK` / `LINES_DRAG` / `LINES_GREET` 就行。
- **改大小**：右键菜单「大小」，或编辑 `%APPDATA%\dafeiyu-pet\config.json` 里的 `scale`。
- **换 Python**：快捷方式指向 `install.ps1` 里 `$cands` 的第一个存在的 pythonw。

## 文件说明

```
dafeiyu-pet/
├─ pet.py             主程序（Win32 分层窗口，逐像素透明）
├─ build_assets.py    素材处理：白底 jpg → 透明 png
├─ 大肥鱼桌宠.lnk      双击启动（目标指向 pythonw，无黑框）
├─ start_pet.bat      备用启动方式
├─ install.ps1        创建 / 重建快捷方式，可选开机自启
├─ assets/
│  ├─ raw/            原始表情图
│  ├─ sprites/        处理好的透明立绘
│  ├─ preview.png     预览图
│  └─ icon.ico        快捷方式图标
└─ config.json        运行时自动生成（位置、大小、开关）
```

## 说明

- 只依赖 Python 3 + Pillow（DSH 自带运行时即可），不装 Electron、不联网。
- 单实例：重复双击不会开出第二只。
- 卸载：右键「退出」，删掉文件夹即可（配置在 `%APPDATA%\dafeiyu-pet`）。
