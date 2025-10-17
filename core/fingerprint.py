"""
指纹生成和管理模块
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse


class FingerprintGenerator:
    """指纹生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_fields = config.get('fingerprint', {}).get('base_fields', ['ip', 'user_agent'])
        self.behavior_fields = config.get('fingerprint', {}).get('behavior_fields', [
            'request_path', 'request_method', 'status_code'
        ])
    
    def generate_base_hash(self, data: Dict) -> str:
        """
        生成基础指纹哈希（基于IP和User-Agent）
        这个哈希用于识别相同的"设备/客户端"
        """
        values = []
        for field in self.base_fields:
            value = data.get(field, '')
            if isinstance(value, str):
                values.append(value.lower().strip())
            else:
                values.append(str(value))
        
        # 生成SHA256哈希
        content = '|'.join(values)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def generate_behavior_hash(self, data: Dict) -> str:
        """
        生成行为指纹哈希（基于请求特征）
        这个哈希用于识别访问行为模式
        """
        values = []
        for field in self.behavior_fields:
            value = data.get(field, '')
            
            # 对路径进行标准化处理
            if field == 'request_path':
                value = self._normalize_path(value)
            
            if isinstance(value, str):
                values.append(value.lower().strip())
            else:
                values.append(str(value))
        
        content = '|'.join(values)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def generate_identity_hash(self, fingerprints: List[str]) -> str:
        """
        生成身份链哈希（基于多个基础指纹）
        当检测到行为演变时，创建一个新的"父哈希"来关联所有相关指纹
        """
        # 对指纹列表排序，确保相同的指纹集合生成相同的哈希
        sorted_fps = sorted(fingerprints)
        content = '||'.join(sorted_fps)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _normalize_path(self, path: str) -> str:
        """
        标准化URL路径，用于更好的模式识别
        例如：/user/123 和 /user/456 应该被识别为相似的路径模式
        """
        # 移除查询参数
        if '?' in path:
            path = path.split('?')[0]
        
        # 移除末尾的斜杠
        path = path.rstrip('/')
        
        # 可选：将数字ID替换为通配符（用于模式识别）
        # 这里保留原始路径，在行为分析时再做聚合
        
        return path
    
    def extract_features(self, data: Dict) -> Dict:
        """
        从请求数据中提取特征
        用于行为分析和威胁检测
        """
        features = {
            'has_query_params': bool(data.get('query_params')),
            'path_depth': len(data.get('request_path', '/').strip('/').split('/')),
            'is_api_request': '/api/' in data.get('request_path', ''),
            'has_file_extension': '.' in data.get('request_path', '').split('/')[-1],
            'referer_exists': bool(data.get('referer')),
            'is_error': data.get('status_code', 200) >= 400,
        }
        
        # User-Agent分析
        ua = data.get('user_agent', '').lower()
        features['is_bot'] = any(bot in ua for bot in ['bot', 'spider', 'crawler', 'scraper'])
        features['is_browser'] = any(browser in ua for browser in ['chrome', 'firefox', 'safari', 'edge'])
        features['is_mobile'] = any(mobile in ua for mobile in ['mobile', 'android', 'iphone', 'ipad'])
        
        return features


class BehaviorAnalyzer:
    """行为分析器 - 检测行为模式变化"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.threshold_config = config.get('fingerprint', {}).get('identity_chain_threshold', {})
        self.same_base_count = self.threshold_config.get('same_base_count', 10)
        self.behavior_change_rate = self.threshold_config.get('behavior_change_rate', 0.3)
    
    def analyze_behavior_change(self, base_hash: str, db_session) -> Dict:
        """
        分析指定基础指纹的行为变化
        返回是否需要创建身份链以及相关信息
        """
        from models.database import AccessLog, Fingerprint
        from sqlalchemy import func
        
        # 获取该基础指纹的所有访问记录
        logs = db_session.query(AccessLog).filter(
            AccessLog.base_hash == base_hash
        ).order_by(AccessLog.timestamp.desc()).limit(1000).all()
        
        if len(logs) < self.same_base_count:
            return {
                'should_create_chain': False,
                'reason': 'insufficient_data',
                'log_count': len(logs)
            }
        
        # 统计不同的行为指纹
        behavior_hashes = set()
        path_patterns = set()
        status_codes = set()
        
        for log in logs:
            behavior_hashes.add(log.behavior_hash)
            path_patterns.add(self._extract_path_pattern(log.request_path))
            status_codes.add(log.status_code)
        
        # 计算行为多样性
        behavior_diversity = len(behavior_hashes) / len(logs) if logs else 0
        
        # 判断是否需要创建身份链
        should_create = (
            len(logs) >= self.same_base_count and
            behavior_diversity >= self.behavior_change_rate
        )
        
        return {
            'should_create_chain': should_create,
            'reason': 'behavior_evolution_detected' if should_create else 'normal_behavior',
            'log_count': len(logs),
            'unique_behaviors': len(behavior_hashes),
            'behavior_diversity': behavior_diversity,
            'path_patterns': list(path_patterns),
            'status_codes': list(status_codes)
        }
    
    def _extract_path_pattern(self, path: str) -> str:
        """
        提取路径模式（将数字、UUID等替换为占位符）
        """
        import re
        
        # 移除查询参数
        if '?' in path:
            path = path.split('?')[0]
        
        # 替换数字ID
        path = re.sub(r'/\d+', '/{id}', path)
        
        # 替换UUID
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path, flags=re.IGNORECASE)
        
        # 替换哈希值
        path = re.sub(r'/[0-9a-f]{32,}', '/{hash}', path, flags=re.IGNORECASE)
        
        return path
    
    def calculate_threat_score(self, base_hash: str, db_session) -> int:
        """
        计算威胁评分（0-100）
        基于访问模式、错误率、扫描行为等
        """
        from models.database import AccessLog, ThreatEvent
        from sqlalchemy import func
        from datetime import timedelta
        
        score = 0
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # 获取24小时内的访问记录
        logs = db_session.query(AccessLog).filter(
            AccessLog.base_hash == base_hash,
            AccessLog.timestamp >= cutoff_time
        ).all()
        
        if not logs:
            return 0
        
        # 1. 错误率 (最高30分)
        error_count = sum(1 for log in logs if log.status_code >= 400)
        error_rate = error_count / len(logs)
        score += min(30, int(error_rate * 100))
        
        # 2. 请求频率 (最高20分)
        time_span = (logs[0].timestamp - logs[-1].timestamp).total_seconds()
        if time_span > 0:
            requests_per_minute = len(logs) / (time_span / 60)
            if requests_per_minute > 10:
                score += min(20, int((requests_per_minute - 10) * 2))
        
        # 3. 扫描行为 (最高25分)
        unique_paths = len(set(log.request_path for log in logs))
        if unique_paths > 20:
            score += min(25, int((unique_paths - 20) / 2))
        
        # 4. 历史威胁事件 (最高25分)
        threat_count = db_session.query(func.count(ThreatEvent.id)).filter(
            ThreatEvent.base_hash == base_hash,
            ThreatEvent.timestamp >= cutoff_time
        ).scalar()
        score += min(25, threat_count * 5)
        
        return min(100, score)

