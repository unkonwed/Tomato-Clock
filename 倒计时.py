import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import time
import threading
import math


class CircularProgressbar:
    def __init__(self, canvas, x, y, radius, thickness=20, bg_color='#34495e', fg_color='#3498db'):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.thickness = thickness
        self.bg_color = bg_color
        self.fg_color = fg_color

        # 创建背景圆环（总是显示完整圆环）
        self.bg_arc = self.canvas.create_arc(
            x - radius, y - radius,
            x + radius, y + radius,
            start=0, extent=359.99,
            width=thickness,
            style=tk.ARC,
            outline=bg_color
        )

        # 创建前景圆环（进度条）- 初始为完整圆环
        self.fg_arc = self.canvas.create_arc(
            x - radius, y - radius,
            x + radius, y + radius,
            start=90, extent=-360,  # 从12点方向开始，完整圆环
            width=thickness,
            style=tk.ARC,
            outline=fg_color
        )

        # 创建中心时间显示
        self.time_text = self.canvas.create_text(
            x, y,
            text="00:00:00",
            font=('Arial', 20, 'bold'),
            fill='#ecf0f1'
        )

        # 存储当前进度（0-100，0表示完整，100表示空）
        self.current_progress = 0

    def update_progress(self, progress):
        """更新进度条，progress为0-100的值，0表示完整圆环，100表示空圆环"""
        if progress < 0:
            progress = 0
        elif progress > 100:
            progress = 100

        self.current_progress = progress

        # 计算剩余的角度（从完整到空）
        remaining_angle = 360 * (1 - progress / 100)

        # 更新前景圆环的角度（从完整到逐渐减少）
        self.canvas.itemconfig(self.fg_arc, extent=-remaining_angle)

    def update_time(self, time_str):
        """更新中心显示的时间"""
        self.canvas.itemconfig(self.time_text, text=time_str)

    def update_colors(self, bg_color=None, fg_color=None):
        """更新圆环颜色"""
        if bg_color:
            self.bg_color = bg_color
            self.canvas.itemconfig(self.bg_arc, outline=bg_color)
        if fg_color:
            self.fg_color = fg_color
            self.canvas.itemconfig(self.fg_arc, outline=fg_color)

    def update_time_font(self, font_tuple):
        """更新时间显示的字体"""
        self.canvas.itemconfig(self.time_text, font=font_tuple)

    def reset_to_full(self):
        """重置为完整圆环"""
        self.update_progress(0)


class DesktopCountdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面倒计时器")
        self.root.geometry("400x350")
        self.root.configure(bg='#2c3e50')

        # 设置窗口无边框，可通过右上角按钮关闭
        self.root.overrideredirect(False)

        # 初始化变量
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.is_running = False
        self.is_paused = False
        self.paused_time = 0

        # 透明度设置
        self.transparency = 0.9

        # 圆环进度条颜色设置
        self.ring_bg_color = '#34495e'
        self.ring_fg_color = '#3498db'
        self.time_font_size = 20

        # 创建UI
        self.setup_ui()

        # 设置默认倒计时时间（10分钟）
        self.set_default_time()

    def setup_ui(self):
        # 主容器
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧倒计时显示区域
        left_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, borderwidth=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 创建Canvas用于绘制圆环进度条
        self.canvas = tk.Canvas(
            left_frame,
            width=250,
            height=250,
            bg='#34495e',
            highlightthickness=0
        )
        self.canvas.pack(expand=True, pady=20)

        # 创建圆环进度条
        self.progress_ring = CircularProgressbar(
            self.canvas,
            x=125, y=125,
            radius=100,
            thickness=20,
            bg_color=self.ring_bg_color,
            fg_color=self.ring_fg_color
        )

        # 右侧按钮区域
        right_frame = tk.Frame(main_frame, bg='#2c3e50')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # 按钮样式
        button_style = {
            'bg': '#3498db',
            'fg': 'white',
            'activebackground': '#2980b9',
            'activeforeground': 'white',
            'bd': 0,
            'padx': 10,
            'pady': 8,
            'width': 12,
            'font': ('Arial', 10)
        }

        # 创建按钮
        self.settings_btn = tk.Button(
            right_frame,
            text="⚙ 设置",
            command=self.show_settings,
            **button_style
        )
        self.settings_btn.pack(pady=5)

        self.start_btn = tk.Button(
            right_frame,
            text="▶ 开始",
            command=self.start_timer,
            **button_style
        )
        self.start_btn.pack(pady=5)

        self.pause_btn = tk.Button(
            right_frame,
            text="⏸ 暂停",
            command=self.pause_timer,
            state=tk.DISABLED,
            **button_style
        )
        self.pause_btn.pack(pady=5)

        self.reset_btn = tk.Button(
            right_frame,
            text="↻ 重置",
            command=self.reset_timer,
            **button_style
        )
        self.reset_btn.pack(pady=5)

        # 添加一个最小化按钮
        self.minimize_btn = tk.Button(
            right_frame,
            text="− 最小化",
            command=self.root.iconify,
            bg='#7f8c8d',
            fg='white',
            activebackground='#95a5a6',
            bd=0,
            padx=10,
            pady=5,
            width=12,
            font=('Arial', 9)
        )
        self.minimize_btn.pack(pady=(20, 5))

        # 添加一个关闭按钮
        self.close_btn = tk.Button(
            right_frame,
            text="× 关闭",
            command=self.root.destroy,
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            bd=0,
            padx=10,
            pady=5,
            width=12,
            font=('Arial', 9)
        )
        self.close_btn.pack(pady=5)

    def set_default_time(self):
        # 设置默认倒计时时间为10分钟
        self.total_seconds = 10 * 60
        self.remaining_seconds = self.total_seconds
        self.update_display()

    def update_display(self):
        # 更新倒计时显示
        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60

        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.progress_ring.update_time(time_str)

        # 更新圆环进度条（从完整到空）
        if self.total_seconds > 0:
            # 计算已过去的时间百分比（0-100）
            elapsed_percentage = ((self.total_seconds - self.remaining_seconds) / self.total_seconds) * 100
            self.progress_ring.update_progress(elapsed_percentage)
        else:
            self.progress_ring.update_progress(0)

    def show_settings(self):
        # 创建设置窗口
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("350x500")  # 增加高度以容纳更多选项
        settings_window.configure(bg='#ecf0f1')
        settings_window.transient(self.root)
        settings_window.grab_set()

        # 使设置窗口置顶
        settings_window.attributes('-topmost', True)

        # 设置窗口标题
        title_label = tk.Label(
            settings_window,
            text="倒计时设置",
            font=('Arial', 14, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        title_label.pack(pady=10)

        # 倒计时时间设置
        time_frame = tk.LabelFrame(
            settings_window,
            text="设置倒计时时间",
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Arial', 10)
        )
        time_frame.pack(fill=tk.X, padx=20, pady=10)

        # 小时输入
        hour_frame = tk.Frame(time_frame, bg='#ecf0f1')
        hour_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(hour_frame, text="小时:", bg='#ecf0f1').pack(side=tk.LEFT)
        self.hour_var = tk.StringVar(value="0")
        hour_spinbox = tk.Spinbox(
            hour_frame,
            from_=0,
            to=23,
            textvariable=self.hour_var,
            width=8
        )
        hour_spinbox.pack(side=tk.RIGHT)

        # 分钟输入
        minute_frame = tk.Frame(time_frame, bg='#ecf0f1')
        minute_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(minute_frame, text="分钟:", bg='#ecf0f1').pack(side=tk.LEFT)
        self.minute_var = tk.StringVar(value="10")
        minute_spinbox = tk.Spinbox(
            minute_frame,
            from_=0,
            to=59,
            textvariable=self.minute_var,
            width=8
        )
        minute_spinbox.pack(side=tk.RIGHT)

        # 秒输入
        second_frame = tk.Frame(time_frame, bg='#ecf0f1')
        second_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(second_frame, text="秒:", bg='#ecf0f1').pack(side=tk.LEFT)
        self.second_var = tk.StringVar(value="0")
        second_spinbox = tk.Spinbox(
            second_frame,
            from_=0,
            to=59,
            textvariable=self.second_var,
            width=8
        )
        second_spinbox.pack(side=tk.RIGHT)

        # 确认时间设置按钮
        confirm_time_btn = tk.Button(
            time_frame,
            text="确认时间设置",
            command=lambda: self.apply_time_settings(settings_window),
            bg='#2ecc71',
            fg='white',
            activebackground='#27ae60',
            bd=0,
            padx=10,
            pady=5,
            font=('Arial', 9)
        )
        confirm_time_btn.pack(pady=10)

        # 透明度设置
        transparency_frame = tk.LabelFrame(
            settings_window,
            text="窗口透明度",
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Arial', 10)
        )
        transparency_frame.pack(fill=tk.X, padx=20, pady=10)

        self.transparency_var = tk.DoubleVar(value=self.transparency)
        transparency_scale = tk.Scale(
            transparency_frame,
            from_=0.1,
            to=1.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.transparency_var,
            command=self.update_transparency,
            bg='#ecf0f1',
            length=200
        )
        transparency_scale.pack(pady=10)

        # 窗口置顶选项
        self.always_on_top_var = tk.BooleanVar(value=False)
        always_on_top_check = tk.Checkbutton(
            settings_window,
            text="窗口始终置顶",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        always_on_top_check.pack(pady=10)

        # 圆环进度条颜色设置
        ring_color_frame = tk.LabelFrame(
            settings_window,
            text="圆环进度条颜色设置",
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Arial', 10)
        )
        ring_color_frame.pack(fill=tk.X, padx=20, pady=10)

        # 背景色选择
        bg_color_frame = tk.Frame(ring_color_frame, bg='#ecf0f1')
        bg_color_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(bg_color_frame, text="背景圆环颜色:", bg='#ecf0f1').pack(side=tk.LEFT)
        bg_color_btn = tk.Button(
            bg_color_frame,
            text="选择颜色",
            command=lambda: self.choose_ring_color('bg'),
            bg=self.ring_bg_color,
            fg='white',
            bd=0,
            padx=10,
            pady=3
        )
        bg_color_btn.pack(side=tk.RIGHT)

        # 前景色选择
        fg_color_frame = tk.Frame(ring_color_frame, bg='#ecf0f1')
        fg_color_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(fg_color_frame, text="进度圆环颜色:", bg='#ecf0f1').pack(side=tk.LEFT)
        fg_color_btn = tk.Button(
            fg_color_frame,
            text="选择颜色",
            command=lambda: self.choose_ring_color('fg'),
            bg=self.ring_fg_color,
            fg='white',
            bd=0,
            padx=10,
            pady=3
        )
        fg_color_btn.pack(side=tk.RIGHT)

        # 时间字体大小设置
        font_frame = tk.LabelFrame(
            settings_window,
            text="时间字体大小",
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Arial', 10)
        )
        font_frame.pack(fill=tk.X, padx=20, pady=10)

        self.font_size_var = tk.StringVar(value=str(self.time_font_size))
        font_size_spinbox = tk.Spinbox(
            font_frame,
            from_=10,
            to=40,
            textvariable=self.font_size_var,
            width=8
        )
        font_size_spinbox.pack(pady=10)

        update_font_btn = tk.Button(
            font_frame,
            text="更新字体大小",
            command=self.update_time_font,
            bg='#9b59b6',
            fg='white',
            activebackground='#8e44ad',
            bd=0,
            padx=10,
            pady=5
        )
        update_font_btn.pack(pady=5)

        # 重置颜色按钮
        reset_colors_btn = tk.Button(
            settings_window,
            text="重置为默认颜色",
            command=self.reset_ring_colors,
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            bd=0,
            padx=10,
            pady=5
        )
        reset_colors_btn.pack(pady=5)

        # 关闭设置窗口按钮
        close_settings_btn = tk.Button(
            settings_window,
            text="关闭设置",
            command=settings_window.destroy,
            bg='#95a5a6',
            fg='white',
            bd=0,
            padx=20,
            pady=8
        )
        close_settings_btn.pack(pady=10)

    def apply_time_settings(self, settings_window):
        try:
            # 解析时间设置
            hours = int(self.hour_var.get())
            minutes = int(self.minute_var.get())
            seconds = int(self.second_var.get())

            if hours == 0 and minutes == 0 and seconds == 0:
                messagebox.showwarning("警告", "倒计时时间不能为0！")
                return

            # 计算总秒数
            self.total_seconds = hours * 3600 + minutes * 60 + seconds
            self.remaining_seconds = self.total_seconds

            # 重置计时器状态
            self.is_running = False
            self.is_paused = False
            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED, text="⏸ 暂停")

            # 重置圆环为完整状态
            self.progress_ring.reset_to_full()

            # 更新显示
            self.update_display()

            messagebox.showinfo("成功", f"已设置倒计时时间为：{hours:02d}:{minutes:02d}:{seconds:02d}")

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")

    def choose_ring_color(self, ring_type):
        """选择圆环颜色"""
        color_code = colorchooser.askcolor(title=f"选择{ring_type}圆环颜色")[1]
        if color_code:
            if ring_type == 'bg':
                self.ring_bg_color = color_code
                self.progress_ring.update_colors(bg_color=color_code)
            else:
                self.ring_fg_color = color_code
                self.progress_ring.update_colors(fg_color=color_code)

    def update_transparency(self, value):
        # 更新窗口透明度
        self.transparency = float(value)
        self.root.attributes('-alpha', self.transparency)

    def toggle_always_on_top(self):
        # 切换窗口置顶状态
        self.root.attributes('-topmost', self.always_on_top_var.get())

    def update_time_font(self):
        """更新时间显示的字体大小"""
        try:
            self.time_font_size = int(self.font_size_var.get())
            font_tuple = ('Arial', self.time_font_size, 'bold')
            self.progress_ring.update_time_font(font_tuple)
            messagebox.showinfo("成功", f"已更新字体大小为：{self.time_font_size}")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的字体大小！")

    def reset_ring_colors(self):
        """重置圆环颜色为默认值"""
        self.ring_bg_color = '#34495e'
        self.ring_fg_color = '#3498db'
        self.progress_ring.update_colors(
            bg_color=self.ring_bg_color,
            fg_color=self.ring_fg_color
        )
        messagebox.showinfo("成功", "已重置圆环颜色为默认值")

    def start_timer(self):
        if self.total_seconds <= 0:
            messagebox.showwarning("警告", "请先设置倒计时时间！")
            return

        if not self.is_running and self.remaining_seconds > 0:
            self.is_running = True
            self.is_paused = False
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)

            # 开始倒计时
            self.countdown_thread = threading.Thread(target=self.run_countdown)
            self.countdown_thread.daemon = True
            self.countdown_thread.start()

    def run_countdown(self):
        start_time = time.time()

        while self.is_running and self.remaining_seconds > 0:
            if not self.is_paused:
                # 计算剩余时间
                elapsed = time.time() - start_time
                self.remaining_seconds = max(0, self.total_seconds - int(elapsed))

                # 更新显示
                self.root.after(0, self.update_display)

                # 每100毫秒更新一次
                time.sleep(0.1)
            else:
                # 如果暂停，更新开始时间以补偿暂停的时间
                start_time += 0.1
                time.sleep(0.1)

        # 倒计时结束
        if self.remaining_seconds <= 0:
            self.is_running = False
            self.root.after(0, self.timer_complete)

    def pause_timer(self):
        if self.is_running:
            self.is_paused = not self.is_paused

            if self.is_paused:
                self.pause_btn.config(text="▶ 继续")
            else:
                self.pause_btn.config(text="⏸ 暂停")

    def reset_timer(self):
        # 重置计时器
        self.is_running = False
        self.is_paused = False
        self.remaining_seconds = self.total_seconds

        # 重置圆环为完整状态
        self.progress_ring.reset_to_full()

        # 更新按钮状态
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="⏸ 暂停")

        # 更新显示
        self.update_display()

    def timer_complete(self):
        # 计时器完成
        self.is_running = False

        # 更新按钮状态
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="⏸ 暂停")

        # 确保圆环完全消失
        self.progress_ring.update_progress(100)

        # 显示完成消息
        self.show_completion_message()

    def show_completion_message(self):
        # 创建完成消息窗口
        message_window = tk.Toplevel(self.root)
        message_window.title("时间到！")
        message_window.geometry("300x150")
        message_window.configure(bg='#2c3e50')

        # 居中显示
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 150) // 2
        message_window.geometry(f"300x150+{x}+{y}")

        # 设置窗口置顶
        message_window.attributes('-topmost', True)

        # 添加消息内容
        message_label = tk.Label(
            message_window,
            text="⏰ 时间到！",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='#e74c3c'
        )
        message_label.pack(expand=True)

        message_text = tk.Label(
            message_window,
            text="倒计时已结束",
            font=('Arial', 12),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        message_text.pack(pady=10)

        # 确认按钮
        ok_btn = tk.Button(
            message_window,
            text="确定",
            command=message_window.destroy,
            bg='#3498db',
            fg='white',
            padx=20,
            pady=5
        )
        ok_btn.pack(pady=10)

        # 播放提示音（可选，需要系统支持）
        try:
            import winsound
            winsound.Beep(1000, 1000)  # 频率1000Hz，持续1秒
            winsound.Beep(1000, 1000)  # 再响一次
        except:
            # 如果winsound不可用，忽略
            pass


def main():
    root = tk.Tk()
    app = DesktopCountdownApp(root)

    # 设置窗口默认透明度
    root.attributes('-alpha', 0.9)

    # 设置窗口图标（如果有图标文件）
    try:
        root.iconbitmap('timer_icon.ico')
    except:
        pass

    # 设置窗口在屏幕中央
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - root.winfo_width()) // 2
    y = (screen_height - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()