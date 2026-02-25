本软件是一个基于 TLS 加密通信的简易 VPN 客户端与服务器系统，在用户注册、登录后实现本地应用通过加密隧道访问远程目标服务器的功能。出于安全性，该系统支持用户身份认证和加密通道建立。通过图形用户界面，用户可以便捷地配置和使用 VPN 连接。该软件用于Windows系统。

下载项目文件后，需要做的工作：
一、安装依赖。
系统环境：Python 
用户可以在终端输入命令安装OpenSSL和Tkinter：
pip install pyOpenSSL
pip install tkinter
一般地，Python自带tkinter，无需另外安装。

二、在项目文件目录下，生成证书。以下为示例命令，虚拟地址信息可修改：
1. 运行命令，生成私钥文件"server.key"：
openssl genpkey -algorithm RSA -out server.key -pkeyopt rsa_keygen_bits:4096

2. 新建名为"server.csr.cnf"的配置文件，内容如下：
[req]
distinguished_name = req_distinguished_name
req_extensions = req_ext
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Example Company
OU = IT
CN = 127.0.0.1

[req_ext]
subjectAltName = @alt_names

[alt_names]
IP.1 = 127.0.0.1

3. 运行命令，根据配置文件生成请求证书文件"server.csr"：
openssl req -new -key server.key -out server.csr -config server.csr.cnf

4. 新建名为"server.crt.cnf"的配置文件，内容如下：
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Example Company
OU = IT
CN = 127.0.0.1

[v3_req]
subjectAltName = @alt_names

[alt_names]
IP.1 = 127.0.0.1

5. 运行命令，根据配置文件生成证书文件"server.crt"
openssl x509 -req -in server.csr -signkey server.key -out server.crt -days 365 -extfile server.crt.cnf -extensions v3_req

三、测试。
1. 使用命令启动一个HTTP服务，在本机模拟目标服务器（运行在8000端口）：
python -m http.server 8000
2. 在项目文件目录下，在两个cmd界面分别运行vpn_server.py（服务器），vpn_client.py（客户端）。
python vpn_server.py
python vpn_client.py
如图"images/client1.png"，输入测试用户信息（信息以哈希值存于"users.example.json"文件，请自行新建"users.json")
3. 再用curl模拟本地应用，向本地代理服务器监听端口（在"images/client1.png"中为46810）发送请求：
curl -v 127.0.0.1:46810
返回目标服务器的响应信息，表明VPN服务器成功转发流量，如图"images/client2.png"。此时，目标服务器端收到请求信息，验证了流量的转发，如图"images/client3.png"

四、使用GUI界面，则在两个cmd界面分别运行vpn_server.py（服务器），GUI.py（客户端）。
点击注册按钮，注册新用户，用户信息哈希加密存于"users.json"，如图"images/GUI1.png"。登陆后可以使用VPN服务，输入公网目标服务器（如www.baidu.com）和目标端口（如80），点击连接按钮。
注册时，如用户名或密码不符合规定（"images/GUI2.png"）或输入已有用户名（"images/GUI3.png"），出现错误弹窗；登陆时，如用户名或密码错误（"images/GUI4.png"），出现错误弹窗。
再用curl模拟本地应用，向本地代理服务器监听端口（在"images/GUI5.png"中为47450）发送请求，返回目标服务器的响应信息，表明VPN服务器成功转发流量，如图"images/GUI6.png"。
