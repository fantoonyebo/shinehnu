import socket #用于网络通信
import ssl #用于SSL/TLS加密通信
import threading
import os,hashlib,json  # 用于密码哈希处理

# 哈希密码函数
def hash_password(password):
    salt = os.urandom(16).hex() #生成随机盐
    h_password = hashlib.sha256((salt+password).encode('utf-8')).hexdigest() #注意，密码编码为字符串才能哈希
    return {'salt':salt, 'h_password':h_password} 

# 用户数据
FILE="users.json" #存储在json文件中
def read_users():
    if os.path.exists(FILE):
        f=open(FILE, 'r', encoding='utf-8') #导入用户数据，读模式
        return json.load(f)
    else:
        return {}
def write_users(data):
    f=open(FILE, 'w', encoding='utf-8') #新增用户数据，写模式
    json.dump(data, f, ensure_ascii=False)

Identity_data = read_users() #读取用户数据

# 验证身份函数
def verify_identity(name, h_password):
    if name not in Identity_data or Identity_data[name]['h_password'] != h_password:
        return False
    return True

# 认证 + 数据转发处理
def handle_connection(client_socket, context):
    conn = context.wrap_socket(client_socket, server_side=True)
    try:
        #接收操作类型，判断是注册还是登录（直接连接）
        data = conn.recv(1024).decode('utf-8')
        try:
            info = json.loads(data)
            type = info.get('type')
        except Exception:
            conn.close()
            return #发生错误，进入下一次while循环
        # 注册
        if type == 'register':
            new_name = info.get('name')
            new_pwd = info.get('password')
            if new_name in Identity_data: #已存在
                conn.sendall(json.dumps({'status': 'error', 'message': '用户名已存在'}).encode('utf-8')) #返回响应
                conn.close()
                return
            Identity_data[new_name] = hash_password(new_pwd) #新用户信息加入字典
            write_users(Identity_data) #保存用户数据到json文件
            print(f"新用户注册：{new_name}")
            conn.sendall(json.dumps({'status': 'success', 'message': '注册成功'}).encode('utf-8'))
            conn.close()
            return

        # 使用哈希的认证机制
        # 1.接收用户名，返回盐
        name_data = data
        try:
            name_info = json.loads(name_data) #格式转换
            name = name_info.get('name') #获取用户名
            if name in Identity_data:
                conn.sendall(json.dumps({'salt': Identity_data[name]['salt']}).encode('utf-8')) #向客户端发送盐
            else:
                conn.sendall(json.dumps({'status': 'error', 'message': '用户不存在，认证失败'}).encode('utf-8'))
                conn.close()
                return
        except json.JSONDecodeError:
            conn.sendall(json.dumps({'status':'error', 'message': '无效用户名数据'}).encode('utf-8'))
            conn.close()
            return

        # 2.接收完整认证数据
        auth_data = conn.recv(1024).decode('utf-8')
        try:
            auth_info = json.loads(auth_data)
            result = verify_identity(auth_info.get('name'), auth_info.get('h_password')) #调用身份验证函数
            if result:                                                                    #认证成功
                conn.sendall(json.dumps({'status': 'success','message': '认证成功'}).encode('utf-8'))
                # 接收目标服务器信息
                target_data = conn.recv(1024)
                target_info = json.loads(target_data.decode('utf-8'))
                print(f"代理请求：{target_info['host']}:{target_info['port']}")
                handle_client_proxy(conn, target_info['host'], target_info['port']) #处理客户端代理请求
            else:
                conn.sendall(json.dumps({'status': 'error','message': '认证失败'}).encode('utf-8'))
                conn.close()
                return
        except json.JSONDecodeError:
            conn.sendall(json.dumps({'status': 'error','message': '无效的认证数据'}).encode('utf-8'))
            conn.close()
            return

    except Exception as e:
        print(f"错误：{e}")
    finally:
        try:
            conn.close()
        except OSError as e:
            print(f"关闭连接时产生错误：{e}")


# 双向转发数据
def handle_forward(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                print("连接断开！！") #客户端连接正常关闭
                break
            destination.sendall(data)
    except:
        pass

# 建立目标连接并转发
def handle_client_proxy(client_conn, target_host, target_port):
    try:
        #套接字，连接目标服务器
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect((target_host, target_port))
        print(f"已连接目标服务器 {target_host}:{target_port}")

        t1 = threading.Thread(target=handle_forward, args=(client_conn, target), daemon=True)
        t2 = threading.Thread(target=handle_forward, args=(target, client_conn), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except Exception as e:
        print(f"目标连接失败: {e}")
    finally:
        target.close()

# 启动服务器监听
def start_vpn_server(host, port):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"VPN服务器正在监听 {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"收到客户端连接：{addr}")
        threading.Thread(target=handle_connection, args=(client_socket, context), daemon=True).start()

if __name__ == "__main__":
    start_vpn_server('127.0.0.1', 8443)
