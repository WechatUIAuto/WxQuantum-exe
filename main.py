#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WxQuantum-exe 主程序入口
微信自动化一体化EXE解决方案
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """主函数"""
    try:
        # 导入登录模块
        from login import main as login_main
        import flet as ft
        
        print("启动 WxQuantum...")
        print("正在加载登录界面...")
        
        # 启动登录界面
        ft.app(target=login_main)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()