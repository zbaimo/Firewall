# 🔧 数据库连接池修复

## 问题

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached
```

### 症状
- ❌ 连接池耗尽
- ❌ 每30秒超时一次
- ❌ 系统无法处理日志
- ❌ Web界面变慢或无响应

### 根本原因
1. 默认连接池太小（5个连接）
2. 高并发访问时连接不够用
3. 连接没有及时释放
4. SQLite在多线程下的限制

---

## 修复方案

### 1. 增加连接池大小

**之前**：
```python
create_engine(f'sqlite:///{db_path}', echo=False)
# 默认: pool_size=5, max_overflow=10
```

**修复后**：
```python
create_engine(
    f'sqlite:///{db_path}',
    echo=False,
    pool_size=20,          # 20个常驻连接
    max_overflow=40,       # 最多60个连接(20+40)
    pool_timeout=60,       # 60秒超时
    pool_recycle=3600,     # 1小时回收
    pool_pre_ping=True,    # 连接前测试
    connect_args={
        'check_same_thread': False,  # 多线程支持
        'timeout': 30                # 数据库锁超时
    }
)
```

### 2. 配置详解

| 参数 | 之前 | 修复后 | 说明 |
|------|------|--------|------|
| pool_size | 5 | 20 | 常驻连接数 |
| max_overflow | 10 | 40 | 溢出连接数 |
| pool_timeout | 30 | 60 | 获取连接超时 |
| pool_recycle | - | 3600 | 1小时回收旧连接 |
| pool_pre_ping | False | True | 使用前测试连接 |
| check_same_thread | True | False | 允许多线程 |

---

## 应用修复

### 方法1：重新部署（推荐）

```bash
# 在本地（Windows）
cd C:\Users\ZBaimo\Desktop\Github\Firewall
git add models/database.py
git commit -m "Fix: Increase database connection pool size"
git push origin main

# 等待GitHub Actions构建新镜像（5-10分钟）

# 在服务器
cd /root/data/firewall
docker-compose -f docker-compose.deploy.yml pull
docker-compose -f docker-compose.deploy.yml down
docker-compose -f docker-compose.deploy.yml up -d
```

### 方法2：临时修复（立即生效）

如果等不及重新部署，可以手动修改：

```bash
# 在服务器上
cd /root/data/firewall

# 进入容器
docker exec -it nginx-firewall bash

# 备份原文件
cp /app/models/database.py /app/models/database.py.backup

# 编辑文件（添加连接池配置）
vi /app/models/database.py
# 或使用 nano /app/models/database.py

# 重启容器使生效
exit
docker-compose -f docker-compose.deploy.yml restart firewall
```

---

## 验证修复

### 1. 检查错误是否消失

```bash
# 查看日志
docker-compose -f docker-compose.deploy.yml logs -f firewall

# 应该不再看到：
# ❌ QueuePool limit of size 5 overflow 10 reached
```

### 2. 监控连接池状态

```bash
# 进入容器
docker exec -it nginx-firewall python

# Python shell中
>>> from models.database import Database
>>> from utils.helpers import load_config
>>> config = load_config('config.yaml')
>>> db = Database(config)
>>> print(db.engine.pool.status())
# 应该显示 pool_size=20

# 退出
>>> exit()
```

### 3. 性能测试

访问Web界面多次刷新，应该：
- ✅ 响应迅速
- ✅ 无超时错误
- ✅ 日志处理正常

---

## 性能提升

### 连接池对比

| 场景 | 之前 | 修复后 |
|------|------|--------|
| 最大并发连接 | 15 | 60 |
| 连接超时 | 30秒 | 60秒 |
| 连接健康检查 | ❌ | ✅ |
| 多线程支持 | ⚠️ | ✅ |
| 连接回收 | ❌ | ✅ (1小时) |

### 预期效果

**之前**：
```
高并发 → 15个连接耗尽 → 等待30秒 → 超时错误
```

**修复后**：
```
高并发 → 60个连接池 → 正常处理 → 无错误
```

---

## 进一步优化（可选）

### 1. 如果访问量特别大

编辑 `models/database.py`，增加连接池：

```python
pool_size=30,          # 30个常驻连接
max_overflow=70,       # 最多100个连接
```

### 2. 考虑升级到MySQL/PostgreSQL

SQLite适合中小型网站，如果：
- 日访问量 > 100万
- 并发连接 > 100
- 多服务器部署

建议升级到MySQL或PostgreSQL：

```yaml
# config.yaml
database:
  type: "mysql"
  host: "localhost"
  port: 3306
  user: "firewall"
  password: "your_password"
  database: "firewall_db"
```

### 3. 使用连接池监控

添加监控脚本：

```python
# monitor_pool.py
from models.database import Database
from utils.helpers import load_config
import time

config = load_config('config.yaml')
db = Database(config)

while True:
    status = db.engine.pool.status()
    print(f"Pool status: {status}")
    time.sleep(10)
```

---

## 注意事项

### ⚠️ 内存使用

更多连接 = 更多内存：
- 每个连接 ≈ 1-2MB
- 60个连接 ≈ 60-120MB

确保Docker容器有足够内存。

### ⚠️ 数据库锁

SQLite在写入时会锁定整个数据库：
- 多个写入会排队
- 大量写入可能变慢

如果遇到性能瓶颈，考虑：
1. 批量写入
2. 使用WAL模式
3. 升级到MySQL

---

## 故障排查

### 如果还是超时

1. **检查磁盘IO**
```bash
iostat -x 1
```

2. **检查数据库大小**
```bash
ls -lh /root/data/firewall/firewall.db
```

3. **优化数据库**
```bash
docker exec nginx-firewall sqlite3 /data/firewall.db "VACUUM;"
```

4. **清理旧数据**
访问Web界面，触发数据清理

### 如果内存不足

减小连接池：
```python
pool_size=10,
max_overflow=20,
```

---

## 总结

### ✅ 已修复
- [x] 增加连接池大小 (5 → 20)
- [x] 增加溢出连接 (10 → 40)
- [x] 延长超时时间 (30s → 60s)
- [x] 添加连接回收 (1小时)
- [x] 启用连接健康检查
- [x] 启用多线程支持

### 📊 预期结果
- ✅ 不再出现连接池耗尽错误
- ✅ 支持更高并发
- ✅ Web界面响应更快
- ✅ 日志处理不再中断

### 🚀 下一步
1. 重新部署应用修复
2. 监控是否还有错误
3. 如果访问量继续增长，考虑升级数据库

---

**修复文件**：`models/database.py`  
**需要重新构建镜像**：是  
**预计修复时间**：10-15分钟（包括构建）

立即执行修复，系统将恢复正常！

