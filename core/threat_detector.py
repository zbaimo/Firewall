"""
威胁检测引擎
检测各种安全威胁和异常行为
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import time


class ThreatDetector:
    """威胁检测引擎"""
    
    def __init__(self, db, config: Dict):
        self.db = db
        self.config = config
        self.detection_config = config.get('threat_detection', {})
        
        # 内存缓存（用于实时检测）
        self.ip_request_history = defaultdict(lambda: deque(maxlen=1000))
        self.ip_404_history = defaultdict(lambda: deque(maxlen=100))
        
        # 编译正则表达式模式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译威胁检测的正则表达式"""
        sql_patterns = self.detection_config.get('sql_injection', {}).get('patterns', [])
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in sql_patterns]
        
        xss_patterns = self.detection_config.get('xss_detection', {}).get('patterns', [])
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in xss_patterns]
        
        ua_patterns = self.detection_config.get('bad_user_agents', {}).get('patterns', [])
        self.bad_ua_patterns = [re.compile(p, re.IGNORECASE) for p in ua_patterns]
        
        self.sensitive_paths = self.detection_config.get('sensitive_paths', {}).get('paths', [])
    
    def detect(self, log_data: Dict) -> List[Dict]:
        """
        检测威胁
        
        Returns:
            威胁列表，每个威胁包含：
            - threat_type: 威胁类型
            - severity: 严重程度
            - description: 描述
            - details: 详细信息
        """
        threats = []
        ip = log_data.get('ip')
        
        # 1. 频率限制检测
        if self.detection_config.get('rate_limit', {}).get('enabled', True):
            threat = self._check_rate_limit(log_data)
            if threat:
                threats.append(threat)
        
        # 2. 404扫描检测
        if self.detection_config.get('scan_detection', {}).get('enabled', True):
            threat = self._check_scan_behavior(log_data)
            if threat:
                threats.append(threat)
        
        # 3. SQL注入检测
        if self.detection_config.get('sql_injection', {}).get('enabled', True):
            threat = self._check_sql_injection(log_data)
            if threat:
                threats.append(threat)
        
        # 4. XSS检测
        if self.detection_config.get('xss_detection', {}).get('enabled', True):
            threat = self._check_xss(log_data)
            if threat:
                threats.append(threat)
        
        # 5. 敏感路径访问
        if self.detection_config.get('sensitive_paths', {}).get('enabled', True):
            threat = self._check_sensitive_path(log_data)
            if threat:
                threats.append(threat)
        
        # 6. User-Agent检测
        if self.detection_config.get('bad_user_agents', {}).get('enabled', True):
            threat = self._check_bad_user_agent(log_data)
            if threat:
                threats.append(threat)
        
        return threats
    
    def _check_rate_limit(self, log_data: Dict) -> Optional[Dict]:
        """检测请求频率限制"""
        config = self.detection_config.get('rate_limit', {})
        window_seconds = config.get('window_seconds', 60)
        max_requests = config.get('max_requests', 100)
        
        ip = log_data.get('ip')
        current_time = time.time()
        
        # 添加到历史记录
        self.ip_request_history[ip].append(current_time)
        
        # 计算时间窗口内的请求数
        cutoff_time = current_time - window_seconds
        recent_requests = [t for t in self.ip_request_history[ip] if t >= cutoff_time]
        
        if len(recent_requests) > max_requests:
            return {
                'threat_type': 'rate_limit_exceeded',
                'severity': 'high',
                'description': f'请求频率过高: {len(recent_requests)}次/{window_seconds}秒',
                'details': {
                    'request_count': len(recent_requests),
                    'window_seconds': window_seconds,
                    'max_allowed': max_requests
                }
            }
        
        return None
    
    def _check_scan_behavior(self, log_data: Dict) -> Optional[Dict]:
        """检测路径扫描行为"""
        config = self.detection_config.get('scan_detection', {})
        window_seconds = config.get('window_seconds', 300)
        max_404_count = config.get('max_404_count', 20)
        
        ip = log_data.get('ip')
        status_code = log_data.get('status_code')
        
        if status_code == 404:
            current_time = time.time()
            self.ip_404_history[ip].append(current_time)
            
            # 计算时间窗口内的404数量
            cutoff_time = current_time - window_seconds
            recent_404s = [t for t in self.ip_404_history[ip] if t >= cutoff_time]
            
            if len(recent_404s) > max_404_count:
                return {
                    'threat_type': 'path_scan',
                    'severity': 'high',
                    'description': f'疑似路径扫描: {len(recent_404s)}个404错误',
                    'details': {
                        '404_count': len(recent_404s),
                        'window_seconds': window_seconds,
                        'max_allowed': max_404_count
                    }
                }
        
        return None
    
    def _check_sql_injection(self, log_data: Dict) -> Optional[Dict]:
        """检测SQL注入攻击"""
        request_path = log_data.get('request_path', '')
        query_params = log_data.get('query_params', '')
        
        # 检查路径和参数
        test_strings = [request_path, query_params]
        
        for test_str in test_strings:
            for pattern in self.sql_patterns:
                if pattern.search(test_str):
                    return {
                        'threat_type': 'sql_injection',
                        'severity': 'critical',
                        'description': 'SQL注入攻击特征',
                        'details': {
                            'matched_pattern': pattern.pattern,
                            'request_path': request_path,
                            'matched_in': test_str[:200]
                        }
                    }
        
        return None
    
    def _check_xss(self, log_data: Dict) -> Optional[Dict]:
        """检测XSS攻击"""
        request_path = log_data.get('request_path', '')
        query_params = log_data.get('query_params', '')
        
        test_strings = [request_path, query_params]
        
        for test_str in test_strings:
            for pattern in self.xss_patterns:
                if pattern.search(test_str):
                    return {
                        'threat_type': 'xss_attack',
                        'severity': 'high',
                        'description': 'XSS攻击特征',
                        'details': {
                            'matched_pattern': pattern.pattern,
                            'request_path': request_path,
                            'matched_in': test_str[:200]
                        }
                    }
        
        return None
    
    def _check_sensitive_path(self, log_data: Dict) -> Optional[Dict]:
        """检测敏感路径访问"""
        request_path = log_data.get('request_path', '')
        
        for sensitive_path in self.sensitive_paths:
            if sensitive_path in request_path:
                return {
                    'threat_type': 'sensitive_path_access',
                    'severity': 'medium',
                    'description': f'访问敏感路径: {sensitive_path}',
                    'details': {
                        'sensitive_path': sensitive_path,
                        'full_path': request_path
                    }
                }
        
        return None
    
    def _check_bad_user_agent(self, log_data: Dict) -> Optional[Dict]:
        """检测恶意User-Agent"""
        user_agent = log_data.get('user_agent', '').lower()
        
        for pattern in self.bad_ua_patterns:
            if pattern.search(user_agent):
                return {
                    'threat_type': 'bad_user_agent',
                    'severity': 'medium',
                    'description': '检测到恶意工具User-Agent',
                    'details': {
                        'matched_pattern': pattern.pattern,
                        'user_agent': user_agent[:200]
                    }
                }
        
        return None
    
    def save_threat_event(self, ip: str, base_hash: str, threat: Dict, 
                         identity_chain_id: Optional[int] = None):
        """保存威胁事件到数据库"""
        from models.database import ThreatEvent
        import json
        
        session = self.db.get_session()
        try:
            event = ThreatEvent(
                ip=ip,
                base_hash=base_hash,
                identity_chain_id=identity_chain_id,
                threat_type=threat['threat_type'],
                severity=threat['severity'],
                description=threat['description'],
                details=json.dumps(threat.get('details', {})),
                handled=False
            )
            session.add(event)
            session.commit()
            return event.id
        except Exception as e:
            session.rollback()
            print(f"保存威胁事件失败: {e}")
            return None
        finally:
            session.close()
    
    def get_ip_threat_history(self, ip: str, hours: int = 24) -> List[Dict]:
        """获取IP的威胁历史"""
        from models.database import ThreatEvent
        
        session = self.db.get_session()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            events = session.query(ThreatEvent).filter(
                ThreatEvent.ip == ip,
                ThreatEvent.timestamp >= cutoff_time
            ).order_by(ThreatEvent.timestamp.desc()).all()
            
            return [{
                'id': event.id,
                'timestamp': event.timestamp.isoformat(),
                'threat_type': event.threat_type,
                'severity': event.severity,
                'description': event.description
            } for event in events]
        finally:
            session.close()
    
    def get_threat_statistics(self, hours: int = 24) -> Dict:
        """获取威胁统计信息"""
        from models.database import ThreatEvent
        from sqlalchemy import func
        
        session = self.db.get_session()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 按类型统计
            type_stats = session.query(
                ThreatEvent.threat_type,
                func.count(ThreatEvent.id).label('count')
            ).filter(
                ThreatEvent.timestamp >= cutoff_time
            ).group_by(ThreatEvent.threat_type).all()
            
            # 按严重程度统计
            severity_stats = session.query(
                ThreatEvent.severity,
                func.count(ThreatEvent.id).label('count')
            ).filter(
                ThreatEvent.timestamp >= cutoff_time
            ).group_by(ThreatEvent.severity).all()
            
            # 总数
            total = session.query(func.count(ThreatEvent.id)).filter(
                ThreatEvent.timestamp >= cutoff_time
            ).scalar()
            
            return {
                'total': total,
                'by_type': {t: c for t, c in type_stats},
                'by_severity': {s: c for s, c in severity_stats},
                'time_range_hours': hours
            }
        finally:
            session.close()

