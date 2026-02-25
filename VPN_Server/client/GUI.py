import tkinter as tk
from tkinter import ttk, messagebox
import threading
import vpn_client # 导入vpn_client模块

class VPNClient:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN客户端")
        self.root.geometry("300x400")
        
        #框架，更好地组织布局
        frm = ttk.Frame(root, padding="10")
        frm.pack(fill="both", expand=True)
         
        # VPN服务器配置
        tk.Label(frm, text="VPN服务器配置", fg='blue', font=('Arial', 10, 'bold')).pack(pady=5)
        
        # VPN服务器
        ttk.Label(frm, text="VPN服务器地址和端口： 127.0.0.1 : 8443").pack(anchor='w', pady=2)  

        # 用户名
        ttk.Label(frm, text="请输入用户名：").pack(anchor='w')
        self.name = ttk.Entry(frm)
        self.name.pack(fill="x", pady=2)

        # 用户密码
        ttk.Label(frm, text="请输入密码：").pack(anchor='w')
        self.password = ttk.Entry(frm, show="*")
        self.password.pack(fill="x", pady=2)
        
        # 分隔线
        ttk.Separator(frm, orient='horizontal').pack(fill='x', pady=10)
        
        # 目标服务器配置
        tk.Label(frm, text="目标服务器配置", fg='orange', font=('Arial', 10, 'bold')).pack(pady=5)
        
        # 目标服务器地址
        ttk.Label(frm, text="请输入目标服务器：").pack(anchor='w')
        self.target_host = ttk.Entry(frm)
        self.target_host.insert(0, "127.0.0.1") # 默认值
        self.target_host.pack(fill="x", pady=2)
        
        # 目标服务器端口
        ttk.Label(frm, text="请输入目标端口：").pack(anchor='w')
        self.target_port = ttk.Entry(frm)
        self.target_port.insert(0, "8000") # 默认值
        self.target_port.pack(fill="x", pady=2)
        
        # 按钮横向布局
        btn_frame = ttk.Frame(frm)
        btn_frame.pack(pady=10, fill="x")

        # 连接按钮
        self.cnect_btn = ttk.Button(btn_frame, text="点击连接", command=self.connection)
        self.cnect_btn.pack(side="left", expand=True, padx=(0, 5))

        # 注册按钮
        self.signup_btn = ttk.Button(btn_frame, text="点击注册", command=self.signup)
        self.signup_btn.pack(side="left", expand=True, padx=(5, 0))

        # 初始化状态
        self.connected = False
    
    # 连接函数
    def connection(self):
        if not self.connected:
            try:
                vpn_host = "127.0.0.1"
                vpn_port = 8443
                name = self.name.get()
                password = self.password.get()
                target_host = self.target_host.get()
                target_port = int(self.target_port.get())

                if not name or not password or not target_host or not target_port:
                    messagebox.showwarning("提示", "用户名、密码和目标服务器信息不能为空！")
                    return

                def show_auth_failed(): #错误弹窗
                    messagebox.showerror("错误", "用户名或密码错误，请重新输入！")
                    #for widget in [self.password, self.btn, self.target_host, self.target_port]:
                    #    widget.configure(state='normal')
                    self.connected = False

                def show_connected(): #已连接弹窗
                    messagebox.showinfo("登录成功", "状态：已连接")
                    for widget in [self.name, self.password, self.cnect_btn, self.signup_btn, self.target_host, self.target_port]: #禁用输入框和按钮
                        widget.configure(state='disabled')
                    self.connected = True

                self.thread = threading.Thread(target=vpn_client.vpn_client, 
                args=(vpn_host, vpn_port, name, password, target_host, target_port,),  #传入用户输入的数据作为参数
                kwargs={'auth_failed': show_auth_failed, 'auth_successed': show_connected}) #传入回调函数作为参数

                self.thread.daemon = True
                self.thread.start()

            except Exception as e:
                messagebox.showerror("错误", f"连接失败: {str(e)}")

    #注册界面
    def signup(self):
        window = tk.Toplevel(self.root)
        window.title("用户注册")
        window.geometry("300x220")

        ttk.Label(window, text="用户名：").pack(anchor='w', padx=20)
        entry_name = ttk.Entry(window)
        entry_name.pack(fill="x", padx=20, pady=2)
        ttk.Label(window, text="(提示：用户名不超过6位，必须包含中文或字母)").pack(anchor='w', padx=20, pady=2)

        ttk.Label(window, text="密码：").pack(anchor='w', padx=20)
        entry_pwd = ttk.Entry(window, show="*")
        entry_pwd.pack(fill="x", padx=20, pady=2)
        ttk.Label(window, text="(提示：密码为8~14位，必须包含字母和数字)").pack(anchor='w', padx=20, pady=2)

        def submit():
            new_name=entry_name.get()
            new_pwd=entry_pwd.get()
            #密码不能为空
            if not new_name or not new_pwd:
                messagebox.showwarning("提示", "用户名和密码不能为空！")
                return
            #用户名和密码强度检查
            if len(new_name) > 6 or not any('\u4e00' <= c <= '\u9fff' or  c.isalpha() for c in new_name):
                messagebox.showwarning("提示", "用户名不超过6位，且必须包含中文或字母！")
                return
            if len(new_pwd) < 8 or len(new_pwd) > 14 or not any(c.isdigit() for c in new_pwd) or not any(c.isalpha() for c in new_pwd):
                messagebox.showwarning("提示", "密码应为8~14位，且包含字母和数字！")
                return
            
            result = vpn_client.new_user(new_name, new_pwd) #调用vpn_client模块的new_user函数，发送新用户名和密码，并接收状态信息
            if result == 'success':
                messagebox.showinfo("注册成功", "用户注册成功！")
                window.destroy()
                return
            if result == 'error':
                messagebox.showerror("错误", "用户名已存在，注册失败。")
                return

            messagebox.showerror("错误", "发生异常，注册失败。")
        
        ttk.Button(window, text="提交", command=submit).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = VPNClient(root)
    root.mainloop()