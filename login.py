import flet as ft
import os
import winreg
import threading
import time
import asyncio
from pathlib import Path
import json

class WeChatPathDetector:
    """微信路径检测器"""
    
    def __init__(self):
        self.common_paths = [
            r"C:\Program Files\Tencent\WeChat\WeChat.exe",
            r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
            r"D:\Program Files\Tencent\WeChat\WeChat.exe",
            r"D:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
            r"C:\Program Files\Tencent\Weixin\Weixin.exe",
            r"C:\Program Files (x86)\Tencent\Weixin\Weixin.exe",
            r"D:\Program Files\Tencent\Weixin\Weixin.exe",
            r"D:\Program Files (x86)\Tencent\Weixin\Weixin.exe",
        ]
    
    def detect_from_registry(self):
        """从注册表检测微信路径"""
        try:
            # 尝试从注册表获取微信安装路径
            key_paths = [
                r"SOFTWARE\Tencent\WeChat",
                r"SOFTWARE\WOW6432Node\Tencent\WeChat",
            ]
            
            for key_path in key_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                        wechat_exe = os.path.join(install_path, "WeChat.exe")
                        if os.path.exists(wechat_exe):
                            return wechat_exe
                except (FileNotFoundError, OSError):
                    continue
        except Exception as e:
            print(f"注册表检测失败: {e}")
        return None
    
    def detect_from_common_paths(self):
        """从常见路径检测微信"""
        for path in self.common_paths:
            if os.path.exists(path):
                return path
        return None
    
    def auto_detect(self):
        """自动检测微信路径"""
        # 先尝试注册表
        path = self.detect_from_registry()
        if path:
            return path
        
        # 再尝试常见路径
        path = self.detect_from_common_paths()
        if path:
            return path
        
        return None
    
    def validate_path(self, path):
        """验证微信路径是否有效"""
        if not path:
            return False
        
        if not os.path.exists(path):
            return False
        
        if not path.lower().endswith('wechat.exe'):
            return False
        
        return True

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_file = "config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
        
        return {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def get_wechat_path(self):
        """获取微信路径"""
        return self.config.get('wechat_path', '')
    
    def set_wechat_path(self, path):
        """设置微信路径"""
        self.config['wechat_path'] = path
        return self.save_config()

class TypewriterText:
    """打字机效果文本组件"""
    
    def __init__(self, page, sentences, size=16, color=ft.Colors.GREY_600):
        self.page = page
        self.sentences = sentences
        self.size = size
        self.color = color
        self.current_text = ""
        self.cursor_visible = True
        self.is_running = True
        
        # 创建文本控件
        self.text_control = ft.Text(
            value="",
            size=self.size,
            color=self.color,
            font_family="SourceHanFont",
        )
        
        # 启动打字机效果
        self.start_typewriter()
    
    def get_control(self):
        """获取文本控件"""
        return self.text_control
    
    def start_typewriter(self):
        """启动打字机效果"""
        def typewriter_thread():
            sentence_index = 0
            while self.is_running:
                try:
                    sentence = self.sentences[sentence_index]
                    
                    # 打字效果
                    for i in range(len(sentence) + 1):
                        if not self.is_running:
                            break
                        self.current_text = sentence[:i]
                        self.update_display()
                        time.sleep(0.1)
                    
                    # 停留时间
                    time.sleep(2)
                    
                    # 删除效果
                    for i in range(len(sentence), -1, -1):
                        if not self.is_running:
                            break
                        self.current_text = sentence[:i]
                        self.update_display()
                        time.sleep(0.05)
                    
                    # 切换到下一个句子
                    sentence_index = (sentence_index + 1) % len(self.sentences)
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"打字机效果错误: {e}")
                    time.sleep(1)
        
        # 在后台线程中运行
        thread = threading.Thread(target=typewriter_thread, daemon=True)
        thread.start()
        
        # 光标闪烁
        def cursor_blink():
            while self.is_running:
                try:
                    self.cursor_visible = not self.cursor_visible
                    self.update_display()
                    time.sleep(0.5)
                except Exception as e:
                    print(f"光标闪烁错误: {e}")
                    time.sleep(1)
        
        cursor_thread = threading.Thread(target=cursor_blink, daemon=True)
        cursor_thread.start()
    
    def update_display(self):
        """更新显示"""
        try:
            cursor = "|" if self.cursor_visible else " "
            display_text = self.current_text + cursor
            self.text_control.value = display_text
            self.page.update()
        except Exception as e:
            print(f"显示更新错误: {e}")
    
    def stop(self):
        """停止打字机效果"""
        self.is_running = False

class LoginPage:
    """登录页面"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.detector = WeChatPathDetector()
        self.config_manager = ConfigManager()
        self.current_mode = "login"  # login, register, recharge
        
        # 配置自定义字体
        self.setup_fonts()
        
        # 打字机效果的句子
        self.typewriter_sentences = [
            "微信自动化一体化解决方案",
            "专业级微信管理工具",
            "智能化消息处理平台",
            "企业级自动化服务",
            "高效便捷的微信助手"
        ]
        
        # UI组件
        self.username_field = ft.TextField(
            label="用户名",
            hint_text="请输入用户名",
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.INDIGO_400,
            text_style=ft.TextStyle(font_family="AlimamaFont", size=14),
            label_style=ft.TextStyle(font_family="AlimamaFont", size=12, color=ft.Colors.INDIGO_600),
            width=250,
            height=55,
            bgcolor=ft.Colors.GREY_50,
            border_radius=15,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
            prefix_icon=ft.Icons.PERSON_OUTLINE,
        )
        
        self.password_field = ft.TextField(
            label="密码",
            hint_text="请输入密码",
            password=True,
            can_reveal_password=True,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.INDIGO_400,
            text_style=ft.TextStyle(font_family="AlimamaFont", size=14),
            label_style=ft.TextStyle(font_family="AlimamaFont", size=12, color=ft.Colors.INDIGO_600),
            width=250,
            height=55,
            bgcolor=ft.Colors.GREY_50,
            border_radius=15,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
            prefix_icon=ft.Icons.LOCK_OUTLINE,
        )
        
        # 注册界面的确认密码字段
        self.confirm_password_field = ft.TextField(
            label="确认密码",
            hint_text="请再次输入密码",
            password=True,
            can_reveal_password=True,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.INDIGO_400,
            text_style=ft.TextStyle(font_family="AlimamaFont", size=14),
            label_style=ft.TextStyle(font_family="AlimamaFont", size=12, color=ft.Colors.INDIGO_600),
            width=250,
            height=55,
            bgcolor=ft.Colors.GREY_50,
            border_radius=15,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            visible=False,
        )
        
        # 微信路径字段
        self.wechat_path_field = ft.TextField(
            label="微信路径",
            hint_text="自动检测中...",
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.GREEN_400,
            text_style=ft.TextStyle(font_family="AlimamaFont", size=14),
            label_style=ft.TextStyle(font_family="AlimamaFont", size=12, color=ft.Colors.GREEN_600),
            width=320,
            height=55,
            bgcolor=ft.Colors.GREY_50,
            border_radius=15,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
            prefix_icon=ft.Icons.FOLDER_OUTLINED,
            suffix_icon=ft.Icons.FOLDER_OPEN,
            read_only=True,
            on_click=self.browse_wechat_path,
        )
        

        
        # 充值界面的账号密码字段
        self.recharge_username_field = ft.TextField(
            label="账号",
            hint_text="请输入账号",
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.ORANGE_400,
            text_style=ft.TextStyle(font_family="AlimamaFont", size=14),
            label_style=ft.TextStyle(font_family="AlimamaFont", size=12, color=ft.Colors.ORANGE_600),
            width=250,
            height=55,
            bgcolor=ft.Colors.GREY_50,
            border_radius=15,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            visible=False,
        )
        
        self.recharge_password_field = ft.TextField(
            label="密码",
            hint_text="请输入密码",
            password=True,
            can_reveal_password=True,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.ORANGE_400,
            text_style=ft.TextStyle(font_family="AlimamaFont", size=14),
            label_style=ft.TextStyle(font_family="AlimamaFont", size=12, color=ft.Colors.ORANGE_600),
            width=250,
            height=55,
            bgcolor=ft.Colors.GREY_50,
            border_radius=15,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            visible=False,
        )
        
        self.card_key_field = ft.TextField(
            label="卡密",
            hint_text="请输入充值卡密",
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.ORANGE_400,
            text_style=ft.TextStyle(font_family="AlimamaFont", size=14),
            label_style=ft.TextStyle(font_family="AlimamaFont", size=12, color=ft.Colors.ORANGE_600),
            width=250,
            height=55,
            bgcolor=ft.Colors.GREY_50,
            border_radius=15,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
            prefix_icon=ft.Icons.CARD_GIFTCARD_OUTLINED,
            visible=False,
        )
        
        self.status_text = ft.Text(
            value="",
            color=ft.Colors.BLUE_600,
            size=14,
            font_family="AlimamaFont",
        )
        
        # 自动检测微信路径
        self.auto_detect_wechat_path()
        
        self.setup_ui()
    
    def auto_detect_wechat_path(self):
        """自动检测微信路径"""
        def detect_async():
            # 先从配置文件加载
            saved_path = self.config_manager.get_wechat_path()
            if saved_path and self.detector.validate_path(saved_path):
                self.wechat_path_field.value = saved_path
                self.wechat_path_field.hint_text = "已检测到微信路径"
                self.page.update()
                return
            
            # 自动检测
            detected_path = self.detector.auto_detect()
            if detected_path:
                self.wechat_path_field.value = detected_path
                self.wechat_path_field.hint_text = "已自动检测到微信路径"
                self.config_manager.set_wechat_path(detected_path)
            else:
                self.wechat_path_field.hint_text = "未检测到微信，请手动选择路径"
                self.wechat_path_field.read_only = False
            
            self.page.update()
        
        # 在后台线程中执行检测
        threading.Thread(target=detect_async, daemon=True).start()
    
    def browse_wechat_path(self, e):
        """浏览选择微信路径"""
        def pick_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                selected_path = e.files[0].path
                if self.detector.validate_path(selected_path):
                    self.wechat_path_field.value = selected_path
                    self.wechat_path_field.hint_text = "已选择微信路径"
                    self.config_manager.set_wechat_path(selected_path)
                    self.status_text.value = "微信路径设置成功"
                    self.status_text.color = ft.Colors.GREEN_600
                else:
                    self.status_text.value = "选择的文件不是有效的微信程序"
                    self.status_text.color = ft.Colors.RED_600
                self.page.update()
        
        file_picker = ft.FilePicker(on_result=pick_file_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        
        file_picker.pick_files(
            dialog_title="选择微信程序",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["exe"],
            initial_directory="C:\\Program Files"
        )
    
    def setup_fonts(self):
        """配置自定义字体"""
        try:
            # 添加自定义字体
            title_font_path = "font/阿里妈妈数黑体.ttf"
            content_font_path = "font/SourceHanSansSC-Normal-2.otf"
            
            if os.path.exists(title_font_path):
                self.page.fonts = {
                    "AlimamaFont": title_font_path,
                    "SourceHanFont": content_font_path
                }
                print("自定义字体加载成功")
            else:
                print("字体文件未找到，使用默认字体")
        except Exception as e:
            print(f"字体配置失败: {e}")
    
    def setup_ui(self):
        """设置UI界面"""
        self.page.title = "WxQuantum - 专业级微信管理工具"
        self.page.window.width = 800
        self.page.window.height = 500
        self.page.window.resizable = False
        self.page.window.center()
        self.page.window.title_bar_hidden = True
        self.page.window.frameless = True
        self.page.window.always_on_top = False
        self.page.window.bgcolor = ft.Colors.TRANSPARENT
        self.page.padding = 0
        self.page.spacing = 0
        
        # 设置渐变背景
        self.page.bgcolor = ft.Colors.TRANSPARENT
        
        # 创建主容器引用
        self.main_container = ft.Container()
        self.build_ui()
        
        self.page.add(self.main_container)
        self.page.update()
    
    def build_ui(self):
        """构建UI界面"""
        # 主容器 - 水平布局
        self.main_container.content = ft.Row([
            # 左侧导航栏
            ft.Container(
                content=ft.Column([
                    # Logo区域
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Image(
                                    src="logo.png",
                                    width=200,
                                    height=100,
                                    fit=ft.ImageFit.CONTAIN,
                                ),
                                border_radius=10,
                            ),
                            # 打字机效果文本
                            TypewriterText(
                                page=self.page,
                                sentences=self.typewriter_sentences,
                                size=12,
                                color=ft.Colors.INDIGO_600
                            ).get_control(),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        ),
                        padding=ft.padding.only(top=10, bottom=10),
                    ),
                    
                    # 主要功能区
                     ft.Container(
                         content=ft.Column([
                             ft.Text(
                                 "主要功能",
                                 size=12,
                                 weight=ft.FontWeight.BOLD,
                                 color=ft.Colors.GREY_600,
                                 font_family="SourceHanFont",
                             ),
                             self.create_nav_button("登录", "login", ft.Icons.LOGIN),
                             self.create_nav_button("注册", "register", ft.Icons.PERSON_ADD),
                             self.create_nav_button("充值", "recharge", ft.Icons.PAYMENT),
                         ],
                         spacing=12,
                         ),
                         padding=ft.padding.symmetric(horizontal=20),
                     ),
                     
                     # 分隔线
                     ft.Container(
                         content=ft.Divider(
                             height=1,
                             color=ft.Colors.GREY_300,
                         ),
                         padding=ft.padding.symmetric(horizontal=30),
                     ),
                     
                     # 信息功能区
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    "软件信息",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREY_600,
                                    font_family="SourceHanFont",
                                ),
                                self.create_nav_button("关于软件", "about", ft.Icons.INFO_OUTLINE),
                            ],
                            spacing=12,
                            ),
                            padding=ft.padding.symmetric(horizontal=20),
                        ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                ),
                width=200,
                bgcolor=ft.Colors.WHITE,
                border_radius=ft.border_radius.only(top_left=20, bottom_left=20),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                ),
                padding=ft.padding.all(20),
            ),
            
            # 右侧内容区域
            ft.Container(
                content=ft.Column([
                    # 标题栏 - 添加拖拽功能
                     ft.WindowDragArea(
                         content=ft.Container(
                             content=ft.Row([
                                 ft.Text(
                                     self.get_title_text(),
                                     size=24,
                                     weight=ft.FontWeight.BOLD,
                                     color=ft.Colors.INDIGO_800,
                                     font_family="AlimamaFont",
                                 ),
                                 ft.Container(expand=True),
                                 # 关闭按钮
                                 ft.IconButton(
                                     icon=ft.Icons.CLOSE,
                                     icon_color=ft.Colors.GREY_600,
                                     on_click=lambda _: self.page.window.close(),
                                 ),
                             ]),
                             padding=ft.padding.only(top=20, left=30, right=20, bottom=10),
                         ),
                     ),
                    
                    # 内容区域 - 添加滚动功能
                    ft.Container(
                        content=ft.ListView(
                            controls=[self.get_content_area()],
                            expand=True,
                            auto_scroll=False,
                            spacing=0,
                        ),
                        padding=ft.padding.only(left=30, right=30, top=10, bottom=10),
                        expand=True,
                        animate_opacity=300,
                        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    ),
                    
                    # 操作按钮和状态（仅在功能页面显示）
                    ft.Container(
                        content=self.get_action_area(),
                        padding=ft.padding.only(left=30, right=30, bottom=10, top=10),
                    ) if self.current_mode in ["login", "register", "recharge"] else ft.Container(),
                ]),
                width=600,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[
                        ft.Colors.BLUE_50,
                        ft.Colors.INDIGO_50,
                        ft.Colors.PURPLE_50,
                    ],
                ),
                border_radius=ft.border_radius.only(top_right=20, bottom_right=20),
            ),
        ],
        spacing=0,
        )
        
        self.main_container.width = 800
        self.main_container.height = 500
        self.main_container.bgcolor = ft.Colors.TRANSPARENT
        self.main_container.border_radius = 20
        self.main_container.shadow = ft.BoxShadow(
            spread_radius=3,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
        )
    
    def switch_mode(self, mode):
        """切换功能模式"""
        self.current_mode = mode
        
        # 更新字段可见性
        if mode == "login":
            self.username_field.visible = True
            self.password_field.visible = True
            self.confirm_password_field.visible = False
            self.wechat_path_field.visible = True
            self.recharge_username_field.visible = False
            self.recharge_password_field.visible = False
            self.card_key_field.visible = False
        elif mode == "register":
            self.username_field.visible = True
            self.password_field.visible = True
            self.confirm_password_field.visible = True
            self.wechat_path_field.visible = False
            self.recharge_username_field.visible = False
            self.recharge_password_field.visible = False
            self.card_key_field.visible = False
        elif mode == "recharge":
            self.username_field.visible = False
            self.password_field.visible = False
            self.confirm_password_field.visible = False
            self.wechat_path_field.visible = False
            self.recharge_username_field.visible = True
            self.recharge_password_field.visible = True
            self.card_key_field.visible = True
        
        # 重新构建UI以更新导航按钮状态
        self.build_ui()
        self.page.update()
    
    def get_button_text(self):
        """获取按钮文本"""
        if self.current_mode == "login":
            return "登录"
        elif self.current_mode == "register":
            return "注册"
        else:
            return "充值"
    
    def get_button_color(self):
        """获取按钮颜色"""
        if self.current_mode == "recharge":
            return ft.Colors.ORANGE_600
        else:
            return ft.Colors.BLUE_600
    
    def create_nav_button(self, text, mode, icon):
        """创建导航按钮"""
        is_active = self.current_mode == mode
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    icon,
                    size=18,
                    color=ft.Colors.BLUE_600 if is_active else ft.Colors.GREY_500,
                ),
                ft.Text(
                    text,
                    size=14,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                    color=ft.Colors.BLUE_600 if is_active else ft.Colors.GREY_600,
                    font_family="SourceHanFont",
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=12,
            ),
            width=150,
            height=45,
            alignment=ft.alignment.center_left,
            padding=ft.padding.symmetric(horizontal=15),
            border=ft.border.only(
                left=ft.BorderSide(3, ft.Colors.BLUE_600) if is_active else ft.BorderSide(3, ft.Colors.TRANSPARENT)
            ),
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_600) if is_active else ft.Colors.TRANSPARENT,
            on_click=lambda e: self.switch_mode(mode),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )
    
    def get_title_text(self):
          """获取标题文本"""
          title_map = {
              "login": "用户登录",
              "register": "用户注册", 
              "recharge": "账户充值",
              "about": "关于软件",
              "manual": "使用说明",
              "disclaimer": "免责声明"
          }
          return title_map.get(self.current_mode, "WxQuantum")
     
    def get_content_area(self):
        """根据当前模式获取内容区域"""
        content = None
        
        if self.current_mode == "login":
            content = ft.Column([
                self.username_field,
                self.password_field,
                self.wechat_path_field,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            )
        elif self.current_mode == "register":
            content = ft.Column([
                self.username_field,
                self.password_field,
                self.confirm_password_field,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            )
        elif self.current_mode == "recharge":
            content = ft.Column([
                self.recharge_username_field,
                self.recharge_password_field,
                self.card_key_field,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            )
        elif self.current_mode == "about":
            content = self.create_about_content()
        elif self.current_mode == "manual":
            content = self.create_manual_content()
        elif self.current_mode == "disclaimer":
            content = self.create_disclaimer_content()
        else:
            content = ft.Container()
        
        # 为所有内容添加居中布局容器 - 基于整个窗口居中
        return ft.Container(
            content=ft.Column([
                ft.Container(height=50),  # 顶部间距
                content,
                ft.Container(height=50),  # 底部间距
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
            width=540,  # 固定宽度确保居中
        )
     
    def create_about_content(self):
        """创建关于软件内容"""
        return ft.Container(
            content=ft.ListView([
                # 关于软件部分
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "WxQuantum 微信自动化助手",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO_800,
                            font_family="AlimamaFont",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),
                        ft.Text(
                            "版本信息",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "• 当前版本：v1.0.0\n• 发布日期：2024年1月\n• 开发团队：WxQuantum Team",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "软件简介",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "WxQuantum是一款专业的微信自动化助手工具，致力于为用户提供高效、安全、便捷的微信自动化解决方案。\n\n主要功能包括：\n• 智能消息处理\n• 自动化操作流程\n• 数据统计分析\n• 多账号管理\n• 安全防护机制",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "技术特色",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "• 基于Python开发，性能稳定可靠\n• 采用Flet框架，界面美观现代\n• 支持多种操作系统\n• 模块化设计，易于扩展\n• 完善的错误处理机制",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=10,
                    ),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE),
                    border_radius=15,
                    border=ft.border.all(1, ft.Colors.BLUE_200),
                    margin=ft.margin.only(bottom=20),
                ),
                
                # 使用说明部分
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "使用说明",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_800,
                            font_family="AlimamaFont",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "快速开始",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "1. 注册账号：首次使用请先注册账号\n2. 登录系统：使用注册的用户名和密码登录\n3. 充值激活：购买卡密进行账号充值激活\n4. 开始使用：登录成功后即可使用各项功能",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "注意事项",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "• 请确保网络连接稳定\n• 建议关闭杀毒软件的实时防护\n• 首次运行可能需要管理员权限\n• 请勿在虚拟机中运行本软件\n• 使用过程中请勿频繁切换账号",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "常见问题",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "Q: 忘记密码怎么办？\nA: 请联系客服重置密码\n\nQ: 软件无法启动？\nA: 请检查系统兼容性和权限设置\n\nQ: 功能使用异常？\nA: 请确保微信版本兼容并重启软件",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=10,
                    ),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREEN),
                    border_radius=15,
                    border=ft.border.all(1, ft.Colors.GREEN_200),
                    margin=ft.margin.only(bottom=20),
                ),
                
                # 免责声明部分
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "免责声明",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_800,
                            font_family="AlimamaFont",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "重要提醒",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "本软件仅供学习和研究使用，请用户严格遵守相关法律法规。使用本软件所产生的一切后果由用户自行承担，开发者不承担任何责任。",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "使用条款",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "1. 用户应合法合规使用本软件\n2. 禁止用于任何违法违规活动\n3. 禁止恶意传播或商业盗用\n4. 使用过程中产生的风险自负\n5. 开发者保留最终解释权",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            "风险提示",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "• 使用自动化工具存在账号风险\n• 请谨慎评估使用场景和频率\n• 建议使用小号进行测试\n• 如遇封号等问题概不负责\n• 请定期备份重要数据",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=10,
                    ),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.RED),
                    border_radius=15,
                    border=ft.border.all(1, ft.Colors.RED_200),
                    margin=ft.margin.only(bottom=20),
                ),
                
                # 联系我们部分
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "联系我们",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO_600,
                            font_family="SourceHanFont",
                        ),
                        ft.Text(
                            "如有任何问题或建议，请通过以下方式联系我们：\n• 邮箱：support@wxquantum.com\n• 官网：www.wxquantum.com\n• QQ群：123456789",
                            size=14,
                            color=ft.Colors.GREY_700,
                            font_family="SourceHanFont",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=10,
                    ),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PURPLE),
                    border_radius=15,
                    border=ft.border.all(1, ft.Colors.PURPLE_200),
                ),
            ],
            expand=True,
            auto_scroll=False,
            spacing=0,
            ),
            expand=True,
        )
    
    def create_manual_content(self):
        """创建使用说明内容"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "使用说明",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.INDIGO_800,
                        font_family="SourceHanFont",
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "操作指南",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.INDIGO_700,
                        font_family="SourceHanFont",
                    ),
                    ft.Text(
                        "1. 新用户请先点击'注册'创建账户\n2. 已有账户用户可直接登录\n3. 充值功能支持卡密充值方式\n4. 请确保微信已正确安装并可正常使用",
                        size=14,
                        color=ft.Colors.GREY_600,
                        font_family="SourceHanFont",
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "注意事项",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_700,
                        font_family="SourceHanFont",
                    ),
                    ft.Text(
                        "• 请勿在公共网络环境下使用\n• 定期更新软件版本以获得最佳体验\n• 如遇问题请及时联系技术支持\n• 建议在使用前关闭杀毒软件的实时防护",
                        size=14,
                        color=ft.Colors.GREY_600,
                        font_family="SourceHanFont",
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=8,
                ),
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                padding=ft.padding.all(25),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                ),
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    def create_disclaimer_content(self):
        """创建免责声明内容"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "免责声明",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_800,
                        font_family="SourceHanFont",
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "重要提示",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700,
                        font_family="SourceHanFont",
                    ),
                    ft.Text(
                        "本软件仅供学习和研究使用，不得用于任何商业用途或非法活动。使用本软件所产生的一切风险和后果，均由用户自行承担，开发团队不承担任何责任。",
                        size=14,
                        color=ft.Colors.GREY_700,
                        font_family="SourceHanFont",
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "法律条款",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700,
                        font_family="SourceHanFont",
                    ),
                    ft.Text(
                        "• 严禁逆向工程、反编译或破解本软件\n• 严禁将本软件用于任何违法违规活动\n• 违反上述条款者，我们将保留追究法律责任的权利\n• 本软件的最终解释权归开发团队所有",
                        size=14,
                        color=ft.Colors.GREY_700,
                        font_family="SourceHanFont",
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "风险提示",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_700,
                        font_family="SourceHanFont",
                    ),
                    ft.Text(
                        "• 使用本软件可能存在账号安全风险\n• 请确保在安全的网络环境下使用\n• 建议定期备份重要数据\n• 如发现异常情况请立即停止使用",
                        size=14,
                        color=ft.Colors.GREY_700,
                        font_family="SourceHanFont",
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=8,
                ),
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                padding=ft.padding.all(25),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                ),
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def get_action_area(self):
        """获取操作按钮区域"""
        return ft.Column([
            ft.Container(
                content=ft.Text(
                    self.get_button_text(),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    font_family="SourceHanFont",
                ),
                width=280,
                height=50,
                bgcolor=self.get_button_color(),
                border_radius=25,
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.3, self.get_button_color()),
                ),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[
                        self.get_button_color(),
                        ft.Colors.with_opacity(0.8, self.get_button_color()),
                    ],
                ),
                on_click=self.handle_action,
            ),
            ft.Container(
                content=self.status_text,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=15),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    def update_ui_elements(self):
        """更新UI元素"""
        # 重新构建UI以更新所有元素
        self.build_ui()
        self.page.update()
    
    def handle_action(self, e):
        """处理操作"""
        if self.current_mode == "login":
            self.handle_login()
        elif self.current_mode == "register":
            self.handle_register()
        else:
            self.handle_recharge()
    
    def handle_login(self):
        """处理登录"""
        username = self.username_field.value
        password = self.password_field.value
        wechat_path = self.wechat_path_field.value
        
        if not username or not password:
            self.status_text.value = "请输入用户名和密码"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        if not wechat_path:
            self.status_text.value = "请选择微信路径"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        # 验证微信路径
        if not self.wechat_detector.validate_path(wechat_path):
            self.status_text.value = "微信路径无效，请重新选择"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        self.status_text.value = "正在登录..."
        self.status_text.color = ft.Colors.BLUE_600
        self.page.update()
        
        # 保存微信路径到配置
        self.config_manager.set_wechat_path(wechat_path)
        
        # 这里添加实际的登录逻辑
        # 模拟登录成功
        self.status_text.value = "登录成功！"
        self.status_text.color = ft.Colors.GREEN_600
        self.page.update()
    
    def handle_register(self):
        """处理注册"""
        username = self.username_field.value
        password = self.password_field.value
        confirm_password = self.confirm_password_field.value
        
        if not username or not password:
            self.status_text.value = "请输入用户名和密码"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        if not confirm_password:
            self.status_text.value = "请确认密码"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        if password != confirm_password:
            self.status_text.value = "两次输入的密码不一致"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        self.status_text.value = "正在注册..."
        self.status_text.color = ft.Colors.BLUE_600
        self.page.update()
        
        # 这里添加实际的注册逻辑
        # 模拟注册成功
        self.status_text.value = "注册成功！"
        self.status_text.color = ft.Colors.GREEN_600
        self.page.update()
    
    def handle_recharge(self):
        """处理充值"""
        username = self.recharge_username_field.value
        password = self.recharge_password_field.value
        card_key = self.card_key_field.value
        
        if not username or not password:
            self.status_text.value = "请输入账号和密码"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        if not card_key:
            self.status_text.value = "请输入卡密"
            self.status_text.color = ft.Colors.RED_600
            self.page.update()
            return
        
        self.status_text.value = "正在验证账号..."
        self.status_text.color = ft.Colors.ORANGE_600
        self.page.update()
        
        # 这里添加实际的账号验证逻辑
        # 模拟验证成功后进行充值
        self.status_text.value = "正在充值..."
        self.page.update()
        
        # 这里添加实际的充值逻辑
        # 模拟充值成功
        self.status_text.value = "充值成功！"
        self.status_text.color = ft.Colors.GREEN_600
        self.page.update()

def main(page: ft.Page):
    """主函数"""
    login_page = LoginPage(page)

if __name__ == "__main__":
    ft.app(target=main, port=8550)