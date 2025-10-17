"""
IP地理位置分析模块
检测异常地理位置访问
"""
import geoip2.database
import geoip2.errors
from typing import Dict, Optional, Tuple
from datetime import datetime
import os


class GeoAnalyzer:
    """地理位置分析器"""
    
    def __init__(self, db, cache_manager, config: Dict):
        self.db = db
        self.cache = cache_manager
        self.config = config
        
        geo_config = config.get('geo_location', {})
        self.enabled = geo_config.get('enabled', False)
        
        if self.enabled:
            db_path = geo_config.get('database_path', 'GeoLite2-City.mmdb')
            
            if os.path.exists(db_path):
                try:
                    self.reader = geoip2.database.Reader(db_path)
                    print("✓ 地理位置分析已启用")
                except Exception as e:
                    print(f"⚠ GeoIP数据库加载失败: {e}")
                    self.enabled = False
                    self.reader = None
            else:
                print(f"⚠ GeoIP数据库不存在: {db_path}")
                print("  下载地址: https://dev.maxmind.com/geoip/geoip2/geolite2/")
                self.enabled = False
                self.reader = None
        else:
            self.reader = None
            print("ℹ 地理位置分析未启用")
        
        # 配置
        self.anomaly_threshold = geo_config.get('anomaly_threshold', 1000)  # km
        self.blocked_countries = set(geo_config.get('blocked_countries', []))
    
    def get_location(self, ip: str) -> Optional[Dict]:
        """
        获取IP地理位置
        
        Returns:
            {
                'country': '中国',
                'country_code': 'CN',
                'city': '北京',
                'latitude': 39.9042,
                'longitude': 116.4074,
                'continent': 'Asia'
            }
        """
        if not self.enabled:
            return None
        
        # 先查缓存
        if self.cache.is_enabled():
            cached = self.cache.get_location(ip)
            if cached:
                return cached
        
        try:
            response = self.reader.city(ip)
            
            location = {
                'country': response.country.name or 'Unknown',
                'country_code': response.country.iso_code or '',
                'city': response.city.name or '',
                'latitude': response.location.latitude,
                'longitude': response.location.longitude,
                'continent': response.continent.name or '',
                'timezone': response.location.time_zone or ''
            }
            
            # 缓存结果（24小时）
            if self.cache.is_enabled():
                self.cache.set_location(ip, location, 86400)
            
            return location
            
        except geoip2.errors.AddressNotFoundError:
            return None
        except Exception as e:
            print(f"地理位置查询失败 ({ip}): {e}")
            return None
    
    def check_geo_anomaly(self, ip: str, base_hash: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        检测地理位置异常
        
        Returns:
            (is_anomaly, reason, score)
        """
        if not self.enabled:
            return False, None, None
        
        current_location = self.get_location(ip)
        if not current_location:
            return False, None, None
        
        # 检查国家封禁
        if current_location['country_code'] in self.blocked_countries:
            return True, f"来自被封禁国家: {current_location['country']}", 50
        
        # 获取历史地理位置
        from models.database import Fingerprint
        session = self.db.get_session()
        try:
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if not fingerprint or not fingerprint.extra_data:
                # 首次访问，保存地理位置
                return False, None, None
            
            import json
            extra_data = json.loads(fingerprint.extra_data) if isinstance(fingerprint.extra_data, str) else fingerprint.extra_data
            last_location = extra_data.get('last_location')
            
            if not last_location:
                return False, None, None
            
            # 检查国家变化
            if last_location.get('country_code') != current_location['country_code']:
                reason = f"国家变化: {last_location.get('country')} → {current_location['country']}"
                
                # 计算距离
                distance = self._calculate_distance(
                    last_location.get('latitude'),
                    last_location.get('longitude'),
                    current_location['latitude'],
                    current_location['longitude']
                )
                
                if distance and distance > self.anomaly_threshold:
                    score = min(50, int(distance / 100))  # 每100km加1分，最高50分
                    return True, reason, score
                else:
                    # 国家变化但距离不远（如边境城市）
                    return True, reason, 15
            
            return False, None, None
            
        finally:
            session.close()
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2) -> Optional[float]:
        """计算两点之间的距离（km）"""
        if not all([lat1, lon1, lat2, lon2]):
            return None
        
        from math import radians, sin, cos, sqrt, atan2
        
        # 地球半径（km）
        R = 6371
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def update_location_metadata(self, base_hash: str, location: Dict):
        """更新指纹的地理位置元数据"""
        from models.database import Fingerprint
        import json
        
        session = self.db.get_session()
        try:
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if fingerprint:
                extra_data = json.loads(fingerprint.extra_data) if fingerprint.extra_data else {}
                extra_data['last_location'] = location
                extra_data['location_updated_at'] = datetime.now().isoformat()
                fingerprint.extra_data = json.dumps(extra_data)
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"更新地理位置元数据失败: {e}")
        finally:
            session.close()
    
    def get_country_stats(self, hours: int = 24) -> Dict:
        """获取国家访问统计"""
        from models.database import AccessLog
        from sqlalchemy import func
        from datetime import timedelta
        
        session = self.db.get_session()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            # 获取所有唯一IP
            ips = session.query(AccessLog.ip).filter(
                AccessLog.timestamp >= cutoff
            ).distinct().all()
            
            country_count = {}
            for (ip,) in ips:
                location = self.get_location(ip)
                if location:
                    country = location['country']
                    country_count[country] = country_count.get(country, 0) + 1
            
            return country_count
        finally:
            session.close()
    
    def close(self):
        """关闭GeoIP数据库"""
        if self.reader:
            self.reader.close()

