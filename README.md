# 🧀 奶酪云工具箱

> 多功能图片/PDF/Excel处理桌面应用

基于 **PySide6** 开发的跨平台桌面工具箱，支持 Windows 7/10/11 和 macOS。

---

## ✨ 功能列表

### 🖼️ 图片工具
| 功能 | 说明 |
|------|------|
| **图片压缩** | 智能压缩，视觉无损/均衡/极致压缩模式 |
| **格式转换** | JPG ↔ PNG ↔ WebP ↔ ICO ↔ PDF |
| **添加水印** | 文字水印/图片水印，支持位置、透明度调整 |

### 📄 PDF工具
| 功能 | 说明 |
|------|------|
| **PDF拆分** | 按页码范围拆分PDF |
| **PDF合并** | 多个PDF合并为一个 |
| **PDF转Word** | 保持排版转换为Word文档 |

### 📊 Excel工具
| 功能 | 说明 |
|------|------|
| **Excel预览** | 快速预览Excel内容 |
| **生成图表** | 根据数据生成可视化图表 |

---

## 🚀 运行方式

### 方式一：源码运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行程序
python main.py
```

### 方式二：打包后运行

直接双击 `CheeseCloudTools.exe` (Windows) 或 `CheeseCloudTools.app` (macOS)

---

## 📁 目录结构

```
nly-tool/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖列表
├── README.md              # 项目说明
│
├── core/                   # 核心模块
│   ├── config.py          # 全局配置管理
│   ├── logger.py          # 日志系统
│   └── error_handler.py   # 错误处理
│
├── ui/                     # 界面模块
│   ├── main_window.py     # 主窗口
│   ├── sidebar.py         # 侧边栏
│   ├── tool_list.py       # 工具列表
│   ├── workspace.py       # 工作区
│   ├── settings.py        # 设置页面
│   ├── image_preview.py   # 图片预览组件
│   └── animations.py      # 动画效果
│
├── tools/                  # 工具实现
│   ├── image/             # 图片工具
│   │   ├── compress.py    # 压缩
│   │   ├── convert.py     # 格式转换
│   │   └── watermark.py   # 水印
│   ├── pdf/               # PDF工具
│   │   ├── split.py       # 拆分
│   │   ├── merge.py       # 合并
│   │   └── to_word.py     # 转Word
│   └── excel/             # Excel工具
│       ├── preview.py     # 预览
│       └── chart.py       # 图表
│
├── resources/              # 资源文件
│   └── style.qss          # 样式表
│
├── image/                  # 图片资源
│   └── 生成奶酪商城官方店介绍.png  # 应用图标
│
├── config/                 # 配置文件（运行时生成）
├── logs/                   # 日志文件（运行时生成）
│
├── build_app.py           # 打包脚本
├── build.bat              # Windows打包快捷方式
├── build.sh               # macOS/Linux打包快捷方式
│
└── .github/
    └── workflows/
        └── build.yml      # GitHub Actions 自动打包
```

---

## 🌐 一键打包所有平台（GitHub Actions）

> **推荐方式**：使用 GitHub Actions 云端打包，可在 Windows 上一次性打包所有平台！

### 使用方法

1. **将代码推送到 GitHub 仓库**

2. **手动触发打包**：
   - 进入仓库 → `Actions` → `🧀 打包所有平台`
   - 点击 `Run workflow` → `Run workflow`

3. **自动触发打包**（推送版本标签时）：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

### 打包产物

| 平台 | 文件名 |
|------|--------|
| Windows 64位 | `CheeseCloudTools-Windows-x64.zip` |
| macOS Intel | `CheeseCloudTools-macOS-Intel.zip` |
| macOS Apple Silicon | `CheeseCloudTools-macOS-AppleSilicon.zip` |
| Linux 64位 | `CheeseCloudTools-Linux-x64.zip` |

### 下载位置

- **手动触发**：Actions → 对应工作流 → Artifacts
- **Tag 触发**：自动创建 Release，在 Releases 页面下载

---

## 📦 本地打包命令

### Windows 用户

```bash
# 方式1：双击运行
build.bat

# 方式2：命令行 - 打包当前平台
python build_app.py

# 方式3：指定平台
python build_app.py --platform win64   # Windows 64位
python build_app.py --platform win32   # Windows 32位

# 一键打包所有支持的版本
python build_app.py --all

# 清理构建缓存
python build_app.py --clean
```

### macOS 用户

```bash
# 添加执行权限
chmod +x build.sh

# 方式1：快捷脚本
./build.sh

# 方式2：命令行
python3 build_app.py                       # 自动识别
python3 build_app.py --platform mac_x64    # Intel Mac
python3 build_app.py --platform mac_arm64  # Apple Silicon (M1/M2/M3)

# 一键打包
python3 build_app.py --all

# 清理构建缓存
python3 build_app.py --clean
```

### Linux 用户

```bash
chmod +x build.sh
./build.sh

# 或
python3 build_app.py --platform linux64
```

### 打包参数说明

| 参数 | 说明 |
|------|------|
| `--platform win64` | Windows 64位 |
| `--platform win32` | Windows 32位 |
| `--platform mac_x64` | macOS Intel |
| `--platform mac_arm64` | macOS Apple Silicon |
| `--platform linux64` | Linux 64位 |
| `--platform current` | 当前系统（默认） |
| `--all` / `-a` | 打包当前系统所有支持的架构 |
| `--clean` / `-c` | 清理构建缓存 |

---

## 📂 打包结果

打包完成后，可执行文件位于 `dist/` 目录：

```
dist/
├── win64/                  # Windows 64位
│   └── CheeseCloudTools/
│       ├── CheeseCloudTools.exe    ← 主程序
│       └── _internal/              ← 依赖文件
│           ├── image/
│           ├── resources/
│           └── ...
│
├── win32/                  # Windows 32位
│   └── CheeseCloudTools/
│
├── mac_x64/                # macOS Intel
│   └── CheeseCloudTools.app/
│
├── mac_arm64/              # macOS Apple Silicon
│   └── CheeseCloudTools.app/
│
└── linux64/                # Linux 64位
    └── CheeseCloudTools/
```

---

## ⚠️ 注意事项

### 跨平台打包
- ❌ **无法在 Windows 上打包 macOS 版本**
- ❌ **无法在 macOS 上打包 Windows 版本**
- ✅ 每个平台需要在对应系统上执行打包命令

### Windows 兼容性
| 版本 | 32位 | 64位 |
|------|------|------|
| Windows 7 | ✅ | ✅ |
| Windows 10 | ✅ | ✅ |
| Windows 11 | ❌ | ✅ |

> **提示**：Windows 7 可能需要安装 Visual C++ Redistributable

### macOS 兼容性
| 芯片 | 打包命令 |
|------|------|
| Intel (x86_64) | `--platform mac_x64` |
| Apple Silicon (M1/M2/M3) | `--platform mac_arm64` |

### 32位版本打包
Windows 32位版本需要在 **32位 Python 环境** 中打包：

```bash
# 1. 安装32位Python
# 2. 使用32位Python运行打包
C:\Python312-32\python.exe build_app.py --platform win32
```

---

## 📋 文件清单

| 文件 | 用途 |
|------|------|
| `main.py` | 程序主入口 |
| `requirements.txt` | Python依赖列表 |
| `README.md` | 项目说明文档 |
| `build_app.py` | 跨平台打包脚本 |
| `build.bat` | Windows快捷打包 |
| `build.sh` | macOS/Linux快捷打包 |
| `.github/workflows/build.yml` | **GitHub Actions 云端打包配置** |
| `resources/style.qss` | 界面样式表 |
| `image/生成奶酪商城官方店介绍.png` | 应用图标 |

---

## 🐛 常见问题

### Q: 打包后运行闪退
**A:** 在命令行运行 exe 查看错误信息：
```bash
cd dist\win64\CheeseCloudTools
CheeseCloudTools.exe
```

### Q: 图标不显示
**A:** 确保 `image/生成奶酪商城官方店介绍.png` 文件存在

### Q: 打包文件太大
**A:** 正常现象，PySide6 和依赖库较大（约200-400MB）

### Q: Windows Defender 报警
**A:** 这是 PyInstaller 打包的常见误报，可以添加白名单

### Q: macOS 提示"无法验证开发者"
**A:** 右键点击应用 → 打开，或在系统设置中允许

---

## 📄 许可证

- **GUI框架**: PySide6 (LGPL，可商用)
- **项目**: MIT License

---

## 👨‍💻 作者

**奶酪源码** - 让工具更简单

