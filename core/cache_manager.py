"""
Redis缓存管理器
提供高性能的数据缓存和频率限制
"""
import redis
import json
from typing import Optional, Dict, List
from datetime import datetime, timedelta


class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        redis_config = config.get('redis', {})
        
        self.enabled = redis_config.get('enabled', False)
        
        if self.enabled:
            try:
                self.redis = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    db=redis_config.get('db', 0),
                    password=redis_config.get('password'),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # 测试连接
                self.redis.ping()
                print("✓ Redis缓存已启用")
            except Exception as e:
                print(f"⚠ Redis连接失败，将禁用缓存: {e}")
                self.enabled = False
                self.redis = None
        else:
            self.redis = None
            print("ℹ Redis缓存未启用")
    
    def is_enabled(self) -> bool:
        """检查缓存是否可用"""
        return self.enabled and self.redis is not None
    
    # ==================== IP评分缓存 ====================
    
    def get_score(self, ip: str) -> Optional[int]:
        """获取IP评分（缓存）"""
        if not self.is_enabled():
            return None
        
        try:
            score = self.redis.get(f"score:{ip}")
            return int(score) if score else None
        except:
            return None
    
    def set_score(self, ip: str, score: int, ttl: int = 300):
        """设置IP评分（缓存5分钟）"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.setex(f"score:{ip}", ttl, score)
        except:
            pass
    
    def incr_score(self, ip: str, delta: int) -> Optional[int]:
        """增加IP评分"""
        if not self.is_enabled():
            return None
        
        try:
            new_score = self.redis.incrby(f"score:{ip}", delta)
            self.redis.expire(f"score:{ip}", 300)
            return new_score
        except:
            return None
    
    # ==================== 频率限制 ====================
    
    def check_rate_limit(self, ip: str, window: int = 60, limit: int = 100) -> bool:
        """
        检查频率限制
        
        Args:
            ip: IP地址
            window: 时间窗口（秒）
            limit: 限制次数
            
        Returns:
            True: 超出限制, False: 未超出
        """
        if not self.is_enabled():
            return False
        
        try:
            minute = int(datetime.now().timestamp() / window)
            key = f"rate:{ip}:{minute}"
            
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, window)
            
            return count > limit
        except:
            return False
    
    def get_request_count(self, ip: str, window: int = 60) -> int:
        """获取IP在时间窗口内的请求数"""
        if not self.is_enabled():
            return 0
        
        try:
            minute = int(datetime.now().timestamp() / window)
            key = f"rate:{ip}:{minute}"
            count = self.redis.get(key)
            return int(count) if count else 0
        except:
            return 0
    
    # ==================== 封禁列表缓存 ====================
    
    def is_banned(self, ip: str) -> bool:
        """检查IP是否被封禁（缓存）"""
        if not self.is_enabled():
            return False
        
        try:
            return self.redis.sismember("banned_ips", ip)
        except:
            return False
    
    def add_to_ban_list(self, ip: str, ttl: Optional[int] = None):
        """添加到封禁列表"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.sadd("banned_ips", ip)
            if ttl:
                # 使用有序集合存储带过期时间的封禁
                expire_at = int(datetime.now().timestamp()) + ttl
                self.redis.zadd("banned_ips_ttl", {ip: expire_at})
        except:
            pass
    
    def remove_from_ban_list(self, ip: str):
        """从封禁列表移除"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.srem("banned_ips", ip)
            self.redis.zrem("banned_ips_ttl", ip)
        except:
            pass
    
    def get_expired_bans(self) -> List[str]:
        """获取过期的封禁"""
        if not self.is_enabled():
            return []
        
        try:
            now = int(datetime.now().timestamp())
            # 获取所有过期的IP
            expired = self.redis.zrangebyscore("banned_ips_ttl", 0, now)
            return list(expired) if expired else []
        except:
            return []
    
    # ==================== 白名单/黑名单缓存 ====================
    
    def is_whitelisted(self, ip: str) -> Optional[bool]:
        """检查是否在白名单（缓存）"""
        if not self.is_enabled():
            return None
        
        try:
            return self.redis.sismember("whitelist", ip)
        except:
            return None
    
    def is_blacklisted(self, ip: str) -> Optional[bool]:
        """检查是否在黑名单（缓存）"""
        if not self.is_enabled():
            return None
        
        try:
            return self.redis.sismember("blacklist", ip)
        except:
            return None
    
    def sync_whitelist(self, ip_list: List[str]):
        """同步白名单到Redis"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.delete("whitelist")
            if ip_list:
                self.redis.sadd("whitelist", *ip_list)
        except:
            pass
    
    def sync_blacklist(self, ip_list: List[str]):
        """同步黑名单到Redis"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.delete("blacklist")
            if ip_list:
                self.redis.sadd("blacklist", *ip_list)
        except:
            pass
    
    # ==================== 指纹缓存 ====================
    
    def get_fingerprint(self, base_hash: str) -> Optional[Dict]:
        """获取指纹信息（缓存）"""
        if not self.is_enabled():
            return None
        
        try:
            data = self.redis.get(f"fp:{base_hash}")
            return json.loads(data) if data else None
        except:
            return None
    
    def set_fingerprint(self, base_hash: str, data: Dict, ttl: int = 300):
        """设置指纹信息（缓存5分钟）"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.setex(f"fp:{base_hash}", ttl, json.dumps(data))
        except:
            pass
    
    # ==================== 统计缓存 ====================
    
    def increment_counter(self, key: str, expire: int = 3600):
        """增加计数器"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.incr(key)
            self.redis.expire(key, expire)
        except:
            pass
    
    def get_counter(self, key: str) -> int:
        """获取计数器值"""
        if not self.is_enabled():
            return 0
        
        try:
            val = self.redis.get(key)
            return int(val) if val else 0
        except:
            return 0
    
    # ==================== 地理位置缓存 ====================
    
    def get_location(self, ip: str) -> Optional[Dict]:
        """获取IP地理位置（缓存）"""
        if not self.is_enabled():
            return None
        
        try:
            data = self.redis.get(f"geo:{ip}")
            return json.loads(data) if data else None
        except:
            return None
    
    def set_location(self, ip: str, location: Dict, ttl: int = 86400):
        """设置IP地理位置（缓存24小时）"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.setex(f"geo:{ip}", ttl, json.dumps(location))
        except:
            pass
    
    # ==================== 清理 ====================
    
    def clear_all(self):
        """清空所有缓存"""
        if not self.is_enabled():
            return
        
        try:
            self.redis.flushdb()
            print("✓ Redis缓存已清空")
        except:
            pass
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        if not self.is_enabled():
            return {'enabled': False}
        
        try:
            info = self.redis.info()
            return {
                'enabled': True,
                'connected': True,
                'used_memory': info.get('used_memory_human'),
                'keys': self.redis.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0)
            }
        except:
            return {'enabled': True, 'connected': False}

