import socket #用于网络通信
import ssl #用于SSL/TLS加密通信
import json
import threading
import hashlib  #用于密码哈希处理

# 哈希密码函数
def hash_password(salt, password):
    return hashlib.sha256((salt+password).encode('utf-8')).hexdigest() #注意，密码编码为字符串才能哈希

# VPN客户端
def vpn_client(host, port, name, password, target_host="www.example.com", target_port=80, auth_successed = None, auth_failed=None): #可选参数，用于GUI.py
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH) # 创建SSL上下文，配置用于服务器认证
    context.load_verify_locations("server.crt") #服务器证书

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #创建套接字
    client_socket.connect((host, port)) #连接到VPN服务器
    conn = context.wrap_socket(client_socket, server_hostname=host) #将套接字包装为SSL/TLS连接

    try:
        #使用哈希的认证机制
        conn.send(json.dumps({'type': 'login', 'name': name}).encode('utf-8')) #仅发送用户名，使用JSON格式编码
        salt = json.loads(conn.recv(1024).decode('utf-8')) #接收盐值
        if salt.get('status') == 'error':
            print("用户名或密码错误，无法建立VPN连接")
            if(auth_failed): #回调函数，错误弹窗
                auth_failed()
            return False
        salt = salt.get('salt') #获取盐值
        auth_data = {'name': name, 'h_password': hash_password(salt, password)}
        conn.send(json.dumps(auth_data).encode('utf-8')) #发送完整认证数据
        
        #接收认证响应
        auth_response = json.loads(conn.recv(1024).decode('utf-8'))
        print(f"认证结果：{auth_response['message']}")
        
        if auth_response['status'] == 'success':
            if auth_successed: #回调函数，已连接弹窗
                auth_successed()
            # 发送目标服务器信息
            target_info = {
                'host': target_host,
                'port': target_port
            }
            conn.send(json.dumps(target_info).encode('utf-8'))
            print(f"VPN隧道已建立，正在转发流量到 {target_host}:{target_port}")
            
            # 创建本地监听端口
            local_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 为避免端口冲突，自动分配监听端口
            local_server.bind(('127.0.0.1', 0))
            local_server.listen(1)
            local_host, local_port = local_server.getsockname()
            print(f"本地代理服务器启动于{local_host}:{local_port}")
            
            while True:
                local_conn, addr = local_server.accept()
                print(f"本地连接：{addr}")
                try:
                    while True:
                        data = local_conn.recv(4096) #接收8888端口应用数据，最大4096字节
                        if not data:
                            break
                        conn.send(data)#发送数据给VPN服务器，最大4096字节
                        response = conn.recv(4096)
                        if not response:
                            break
                        local_conn.send(response)
                finally:
                    local_conn.close()
        else:
            print("用户名或密码错误，无法建立VPN连接")
            if(auth_failed): #回调函数，错误弹窗
                auth_failed()
            return False
    finally:
        conn.close()

def new_user(nn,npwd):
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations("server.crt")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 8443))
    conn = context.wrap_socket(client_socket, server_hostname='127.0.0.1') #将套接字包装为SSL/TLS连接
    try:
        reg_data={'type':'register', 'name':nn, 'password':npwd} #向服务器发送注册信息
        conn.send(json.dumps(reg_data).encode('utf-8'))
        reg_response=json.loads(conn.recv(1024).decode('utf-8')) #接收注册响应
        print(f"注册响应：{reg_response}")
        return reg_response.get('status') #返回状态信息
    except Exception as e:
        print(f"注册异常：{e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__": #当脚本作为主程序运行时，启动VPN客户端
    name = input("请输入用户名：")
    password = input("请输入密码：")
    target = input("请输入目标服务器地址（格式：host:port）：")
    host, port = target.split(':')
    vpn_client('127.0.0.1', 8443, name, password, host, int(port)) #连接到本地服务器