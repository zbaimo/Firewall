# 安装指南

## 系统要求

- Python 3.8+
- 管理员权限（用于修改防火墙规则）
- Nginx服务器及其日志文件访问权限

### Windows系统
- Windows 10/11 或 Windows Server 2016+
- PowerShell

### Linux系统
- 支持iptables或firewalld
- 建议使用Ubuntu 20.04+, CentOS 7+, Debian 10+

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <repository_url>
cd Firewall
```

### 2. 安装Python依赖

#### Windows
```cmd
# 使用启动脚本（推荐）
run.bat

# 或手动安装
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Linux/macOS
```bash
# 使用启动脚本（推荐）
chmod +x run.sh
./run.sh

# 或手动安装
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置系统

编辑 `config.yaml` 配置文件：

```yaml
# 最重要的配置项
nginx:
  access_log: "/var/log/nginx/access.log"  # 修改为你的nginx日志路径
  
database:
  path: "firewall.db"  # SQLite数据库路径
  
firewall:
  enabled: true  # 是否启用实际防火墙操作
  os: "auto"     # auto, windows, linux
  
  whitelist:
    - "127.0.0.1"
    - "::1"
    # 添加你的内网IP段
```

### 4. 权限配置

#### Windows
需要以管理员身份运行：

```powershell
# 右键 PowerShell -> 以管理员身份运行
cd path\to\Firewall
python main.py
```

#### Linux
需要root权限来操作iptables：

```bash
# 方法1: 使用sudo运行
sudo python main.py

# 方法2: 添加sudo权限（推荐生产环境）
sudo visudo
# 添加以下行（替换yourusername）
yourusername ALL=(ALL) NOPASSWD: /sbin/iptables, /usr/bin/firewall-cmd
```

### 5. 测试运行

```bash
# 测试配置
python main.py --help

# 批量处理历史日志（测试）
python main.py --batch /path/to/nginx/access.log --max-lines 1000

# 正式运行
python main.py
```

## 可选配置

### Redis（推荐用于高性能）

安装Redis：

**Windows:**
1. 下载Redis for Windows
2. 解压并运行 `redis-server.exe`

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# CentOS/RHEL
sudo yum install redis
```

配置文件启用Redis：
```yaml
redis:
  enabled: true
  host: "localhost"
  port: 6379
```

### 数据库（可选：MySQL/PostgreSQL）

对于大规模部署，可以使用MySQL或PostgreSQL：

```yaml
database:
  type: "mysql"  # 或 postgresql
  host: "localhost"
  port: 3306
  user: "firewall"
  password: "your_password"
  database: "firewall_db"
```

然后安装对应的Python驱动：
```bash
# MySQL
pip install pymysql

# PostgreSQL
pip install psycopg2-binary
```

## 设置为系统服务

### Linux (systemd)

创建服务文件 `/etc/systemd/system/nginx-firewall.service`：

```ini
[Unit]
Description=Nginx Log Firewall System
After=network.target nginx.service

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/Firewall
Environment="PATH=/path/to/Firewall/venv/bin"
ExecStart=/path/to/Firewall/venv/bin/python /path/to/Firewall/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable nginx-firewall
sudo systemctl start nginx-firewall
sudo systemctl status nginx-firewall
```

### Windows (Task Scheduler)

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：系统启动时
4. 操作：启动程序
   - 程序：`C:\path\to\Firewall\venv\Scripts\python.exe`
   - 参数：`C:\path\to\Firewall\main.py`
   - 起始于：`C:\path\to\Firewall`
5. 勾选"使用最高权限运行"

## 故障排查

### 日志文件权限问题
```bash
# Linux: 给予读取权限
sudo chmod +r /var/log/nginx/access.log
# 或将用户添加到nginx组
sudo usermod -a -G adm yourusername
```

### 防火墙规则不生效
```bash
# Linux: 检查iptables
sudo iptables -L -n

# Windows: 检查防火墙规则
netsh advfirewall firewall show rule name=all
```

### 数据库锁定问题
如果使用SQLite，确保只有一个进程在运行

### Web管理后台无法访问
检查端口是否被占用：
```bash
# Linux
netstat -tulpn | grep 8080

# Windows
netstat -ano | findstr 8080
```

## 下一步

- 阅读 [README.md](README.md) 了解系统功能
- 查看 [config.yaml](config.yaml) 的详细配置说明
- 访问Web管理后台 http://localhost:8080

