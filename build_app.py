"""
奶酪云工具箱 - 打包脚本
支持 Windows (7/10/11) 32位/64位, macOS 打包

使用方法:
    python build_app.py              # 打包当前平台
    python build_app.py --all        # 尝试打包所有平台（需要对应环境）
    python build_app.py --platform win64   # 指定平台
"""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

# 项目配置
APP_NAME = "奶酪云工具箱"
APP_NAME_EN = "CheeseCloudTools"
VERSION = "1.0.0"
AUTHOR = "奶酪源码"
DESCRIPTION = "多功能图片/PDF/Excel处理工具"

# 路径配置
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
ICON_SOURCE = PROJECT_ROOT / "image" / "生成奶酪商城官方店介绍.png"
ICON_DIR = PROJECT_ROOT / "build_icons"

# 需要包含的数据文件
DATA_FILES = [
    ("resources", "resources"),
    ("image", "image"),
]


def create_icon_dir():
    """创建图标目录"""
    ICON_DIR.mkdir(exist_ok=True)


def convert_png_to_ico(png_path: Path, ico_path: Path, sizes=None):
    """将PNG转换为ICO格式（Windows图标）"""
    if sizes is None:
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    try:
        from PIL import Image
        
        img = Image.open(png_path)
        
        # 创建不同尺寸的图标
        icon_images = []
        for size in sizes:
            resized = img.copy()
            resized.thumbnail(size, Image.Resampling.LANCZOS)
            # 确保尺寸正确
            if resized.size != size:
                new_img = Image.new('RGBA', size, (0, 0, 0, 0))
                offset = ((size[0] - resized.size[0]) // 2, 
                         (size[1] - resized.size[1]) // 2)
                new_img.paste(resized, offset)
                resized = new_img
            icon_images.append(resized)
        
        # 保存为ICO
        icon_images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.size[0], img.size[1]) for img in icon_images]
        )
        print(f"✅ 已创建 Windows 图标: {ico_path}")
        return True
    except Exception as e:
        print(f"❌ 创建 ICO 失败: {e}")
        return False


def convert_png_to_icns(png_path: Path, icns_path: Path):
    """将PNG转换为ICNS格式（macOS图标）"""
    try:
        from PIL import Image
        
        img = Image.open(png_path)
        
        # macOS 需要特定尺寸
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        
        # 创建临时 iconset 目录
        iconset_dir = icns_path.parent / f"{icns_path.stem}.iconset"
        iconset_dir.mkdir(exist_ok=True)
        
        for size in sizes:
            # 标准分辨率
            resized = img.copy()
            resized.thumbnail((size, size), Image.Resampling.LANCZOS)
            resized.save(iconset_dir / f"icon_{size}x{size}.png")
            
            # 2x 分辨率 (Retina)
            if size <= 512:
                resized_2x = img.copy()
                resized_2x.thumbnail((size * 2, size * 2), Image.Resampling.LANCZOS)
                resized_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")
        
        # 使用 iconutil 转换（仅macOS可用）
        if platform.system() == "Darwin":
            subprocess.run(["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)])
            print(f"✅ 已创建 macOS 图标: {icns_path}")
        else:
            # 在非macOS上，复制PNG作为替代
            shutil.copy(png_path, icns_path.with_suffix('.png'))
            print(f"⚠️ 非macOS环境，已复制PNG: {icns_path.with_suffix('.png')}")
        
        # 清理临时目录
        shutil.rmtree(iconset_dir, ignore_errors=True)
        return True
    except Exception as e:
        print(f"❌ 创建 ICNS 失败: {e}")
        return False


def prepare_icons():
    """准备各平台图标"""
    create_icon_dir()
    
    ico_path = ICON_DIR / "app.ico"
    icns_path = ICON_DIR / "app.icns"
    
    if ICON_SOURCE.exists():
        convert_png_to_ico(ICON_SOURCE, ico_path)
        convert_png_to_icns(ICON_SOURCE, icns_path)
    else:
        print(f"⚠️ 图标源文件不存在: {ICON_SOURCE}")
    
    return ico_path, icns_path


def get_pyinstaller_args(target_platform: str, ico_path: Path, icns_path: Path):
    """获取 PyInstaller 参数"""
    
    # 基础参数
    args = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name", f"{APP_NAME_EN}",
        "--windowed",  # GUI应用，不显示控制台
        "--onedir",    # 打包为目录（更稳定）
    ]
    
    # 添加数据文件
    for src, dst in DATA_FILES:
        src_path = PROJECT_ROOT / src
        if src_path.exists():
            args.extend(["--add-data", f"{src_path}{os.pathsep}{dst}"])
    
    # 隐藏导入
    hidden_imports = [
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets", 
        "PIL",
        "PIL.Image",
        "fitz",
        "pandas",
        "openpyxl",
        "matplotlib",
        "matplotlib.backends.backend_qtagg",
    ]
    for hi in hidden_imports:
        args.extend(["--hidden-import", hi])
    
    # 平台特定参数
    if target_platform.startswith("win"):
        if ico_path.exists():
            args.extend(["--icon", str(ico_path)])
        # Windows 版本信息
        args.extend([
            "--version-file", str(PROJECT_ROOT / "version_info.txt"),
        ])
    elif target_platform.startswith("mac"):
        if icns_path.exists():
            args.extend(["--icon", str(icns_path)])
        # macOS bundle 标识符
        args.extend([
            "--osx-bundle-identifier", "com.naiyuanma.cheesetools",
        ])
    
    # 输出目录
    output_dir = DIST_DIR / target_platform
    args.extend(["--distpath", str(output_dir)])
    args.extend(["--workpath", str(BUILD_DIR / target_platform)])
    args.extend(["--specpath", str(BUILD_DIR)])
    
    # 主入口文件
    args.append(str(PROJECT_ROOT / "main.py"))
    
    return args


def create_version_info():
    """创建 Windows 版本信息文件"""
    version_parts = VERSION.split(".")
    while len(version_parts) < 4:
        version_parts.append("0")
    
    version_tuple = ", ".join(version_parts)
    
    content = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'080404b0',
          [
            StringStruct(u'CompanyName', u'{AUTHOR}'),
            StringStruct(u'FileDescription', u'{DESCRIPTION}'),
            StringStruct(u'FileVersion', u'{VERSION}'),
            StringStruct(u'InternalName', u'{APP_NAME_EN}'),
            StringStruct(u'LegalCopyright', u'Copyright (C) 2024 {AUTHOR}'),
            StringStruct(u'OriginalFilename', u'{APP_NAME_EN}.exe'),
            StringStruct(u'ProductName', u'{APP_NAME}'),
            StringStruct(u'ProductVersion', u'{VERSION}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
'''
    
    version_file = PROJECT_ROOT / "version_info.txt"
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已创建版本信息文件: {version_file}")


def build_for_platform(target_platform: str):
    """为指定平台打包"""
    print(f"\n{'='*50}")
    print(f"🔨 开始打包: {target_platform}")
    print(f"{'='*50}")
    
    # 准备图标
    ico_path, icns_path = prepare_icons()
    
    # 创建版本信息（Windows）
    if target_platform.startswith("win"):
        create_version_info()
    
    # 获取 PyInstaller 参数
    args = get_pyinstaller_args(target_platform, ico_path, icns_path)
    
    print(f"📦 执行命令: {' '.join(args)}")
    
    # 执行打包
    try:
        result = subprocess.run(args, check=True)
        print(f"\n✅ {target_platform} 打包成功!")
        print(f"📁 输出目录: {DIST_DIR / target_platform}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {target_platform} 打包失败: {e}")
        return False


def get_current_platform():
    """获取当前平台标识"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "windows":
        if machine in ["amd64", "x86_64"]:
            return "win64"
        else:
            return "win32"
    elif system == "darwin":
        if machine == "arm64":
            return "mac_arm64"
        else:
            return "mac_x64"
    elif system == "linux":
        if machine in ["amd64", "x86_64"]:
            return "linux64"
        else:
            return "linux32"
    
    return "unknown"


def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if ICON_DIR.exists():
        shutil.rmtree(ICON_DIR)
    print("✅ 清理完成")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="奶酪云工具箱打包脚本")
    parser.add_argument("--platform", "-p", 
                       choices=["win32", "win64", "mac_x64", "mac_arm64", "current"],
                       default="current",
                       help="目标平台")
    parser.add_argument("--all", "-a", action="store_true",
                       help="打包所有平台（需要对应环境）")
    parser.add_argument("--clean", "-c", action="store_true",
                       help="清理构建目录")
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════╗
║         奶酪云工具箱 - 打包工具              ║
║         版本: {VERSION}                         ║
╚══════════════════════════════════════════════╝
""")
    
    if args.clean:
        clean_build()
        return
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ 未安装 PyInstaller，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 确定要打包的平台
    if args.all:
        # 打包当前系统支持的所有架构
        system = platform.system().lower()
        if system == "windows":
            # Windows 可以同时打包 32位和64位（如果有对应Python）
            platforms = ["win64"]  # 默认打包64位
            print(f"📋 Windows 系统将打包: {platforms}")
            print(f"⚠️ 32位版本需要在32位Python环境中单独打包")
        elif system == "darwin":
            # macOS 
            machine = platform.machine().lower()
            if machine == "arm64":
                platforms = ["mac_arm64"]
            else:
                platforms = ["mac_x64"]
            print(f"📋 macOS 系统将打包: {platforms}")
        else:
            platforms = [get_current_platform()]
            print(f"📋 当前平台: {platforms}")
    elif args.platform == "current":
        platforms = [get_current_platform()]
    else:
        platforms = [args.platform]
    
    # 创建输出目录
    DIST_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)
    
    # 打包
    success_count = 0
    for plat in platforms:
        if build_for_platform(plat):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"📊 打包完成: {success_count}/{len(platforms)} 成功")
    print(f"📁 输出目录: {DIST_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

