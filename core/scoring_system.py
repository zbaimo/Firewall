"""
用户威胁评分系统
对每个用户的行为进行评分，累计分数达到阈值时采取行动
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


class ThreatScoringSystem:
    """威胁评分系统"""
    
    # 默认配置（如果配置文件中没有）
    DEFAULT_THREAT_SCORES = {
        'sql_injection': 50,
        'xss_attack': 40,
        'path_scan': 30,
        'rate_limit_exceeded': 25,
        'sensitive_path_access': 15,
        'bad_user_agent': 20,
        'multiple_404': 10,
        'suspicious_query': 15,
    }
    
    DEFAULT_SEVERITY_MULTIPLIERS = {
        'critical': 2.0,
        'high': 1.5,
        'medium': 1.0,
        'low': 0.5
    }
    
    DEFAULT_BEHAVIOR_PATTERNS = {
        'tool_switching': 30,
        'time_pattern_anomaly': 15,
        'geographic_anomaly': 20,
        'rapid_behavior_change': 25,
    }
    
    def __init__(self, db, config: Dict):
        self.db = db
        self.config = config
        self.scoring_config = config.get('scoring_system', {})
        
        # 是否启用评分系统
        self.enabled = self.scoring_config.get('enabled', True)
        
        # 评分策略配置（从config.yaml读取，可以自定义）
        self.score_decay_hours = self.scoring_config.get('score_decay_hours', 24)
        self.score_decay_rate = self.scoring_config.get('score_decay_rate', 0.5)
        
        # 威胁分数配置（用户可以在config.yaml中自定义）
        self.threat_scores = self.scoring_config.get('threat_scores', self.DEFAULT_THREAT_SCORES)
        self.severity_multipliers = self.scoring_config.get('severity_multipliers', self.DEFAULT_SEVERITY_MULTIPLIERS)
        self.behavior_patterns = self.scoring_config.get('behavior_patterns', self.DEFAULT_BEHAVIOR_PATTERNS)
        self.score_rewards = self.scoring_config.get('score_rewards', {})
        
        # 封禁阈值（用户可以在config.yaml中自定义）
        default_thresholds = {
            'temporary_ban': 60,
            'extended_ban': 100,
            'permanent_ban': 150
        }
        self.thresholds = self.scoring_config.get('ban_thresholds', default_thresholds)
        
        # 封禁时长（秒）（用户可以在config.yaml中自定义）
        default_durations = {
            'temporary_ban': 3600,
            'extended_ban': 86400,
            'permanent_ban': None
        }
        self.ban_durations = self.scoring_config.get('ban_durations', default_durations)
    
    def calculate_threat_score(self, threat: Dict) -> float:
        """
        计算单次威胁的分数
        
        Args:
            threat: 威胁信息字典
            
        Returns:
            威胁分数
        """
        threat_type = threat.get('threat_type')
        severity = threat.get('severity', 'medium')
        
        # 基础分数（从配置读取）
        base_score = self.threat_scores.get(threat_type, 10)
        
        # 严重程度乘数（从配置读取）
        multiplier = self.severity_multipliers.get(severity, 1.0)
        
        # 计算最终分数
        final_score = base_score * multiplier
        
        return final_score
    
    def add_score_to_fingerprint(self, base_hash: str, score: float, 
                                 reason: str, threat_id: Optional[int] = None):
        """
        为指纹添加分数
        
        Args:
            base_hash: 基础指纹哈希
            score: 要添加的分数
            reason: 评分原因
            threat_id: 关联的威胁事件ID
        """
        from models.database import Fingerprint, ScoreHistory
        
        session = self.db.get_session()
        try:
            # 获取或创建指纹
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if not fingerprint:
                return
            
            # 应用分数衰减
            current_score = self._apply_score_decay(fingerprint)
            
            # 添加新分数
            new_score = current_score + score
            fingerprint.threat_score = min(200, int(new_score))  # 最高200分
            fingerprint.last_score_update = datetime.now()
            
            # 记录评分历史
            score_history = ScoreHistory(
                fingerprint_id=fingerprint.id,
                base_hash=base_hash,
                score_change=score,
                total_score=fingerprint.threat_score,
                reason=reason,
                threat_event_id=threat_id
            )
            session.add(score_history)
            
            session.commit()
            
            return fingerprint.threat_score
        except Exception as e:
            session.rollback()
            print(f"添加评分失败: {e}")
            return None
        finally:
            session.close()
    
    def _apply_score_decay(self, fingerprint) -> float:
        """
        应用分数衰减
        分数会随时间自然降低（表示威胁减弱）
        
        Args:
            fingerprint: 指纹对象
            
        Returns:
            衰减后的分数
        """
        if not fingerprint.last_score_update:
            return fingerprint.threat_score
        
        # 计算时间差（小时）
        time_diff = datetime.now() - fingerprint.last_score_update
        hours_passed = time_diff.total_seconds() / 3600
        
        # 如果超过衰减周期，应用衰减
        if hours_passed >= self.score_decay_hours:
            decay_cycles = int(hours_passed / self.score_decay_hours)
            decayed_score = fingerprint.threat_score * (self.score_decay_rate ** decay_cycles)
            return max(0, decayed_score)
        
        return fingerprint.threat_score
    
    def get_fingerprint_score(self, base_hash: str) -> Tuple[float, str]:
        """
        获取指纹的当前分数和风险等级
        
        Returns:
            (score, risk_level)
        """
        from models.database import Fingerprint
        
        session = self.db.get_session()
        try:
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if not fingerprint:
                return 0.0, 'safe'
            
            # 应用衰减
            current_score = self._apply_score_decay(fingerprint)
            
            # 确定风险等级
            risk_level = self._determine_risk_level(current_score)
            
            return current_score, risk_level
        finally:
            session.close()
    
    def _determine_risk_level(self, score: float) -> str:
        """确定风险等级"""
        if score >= self.thresholds['permanent_ban']:
            return 'critical'  # 极高危险
        elif score >= self.thresholds['extended_ban']:
            return 'high'      # 高危险
        elif score >= self.thresholds['temporary_ban']:
            return 'medium'    # 中等危险
        elif score >= 30:
            return 'low'       # 低危险
        else:
            return 'safe'      # 安全
    
    def should_ban(self, base_hash: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        判断是否应该封禁该指纹
        
        Returns:
            (should_ban, ban_type, duration_seconds)
        """
        score, risk_level = self.get_fingerprint_score(base_hash)
        
        # 判断封禁级别
        if score >= self.thresholds['permanent_ban']:
            return True, 'permanent_ban', self.ban_durations['permanent_ban']
        elif score >= self.thresholds['extended_ban']:
            return True, 'extended_ban', self.ban_durations['extended_ban']
        elif score >= self.thresholds['temporary_ban']:
            return True, 'temporary_ban', self.ban_durations['temporary_ban']
        
        return False, None, None
    
    def add_behavior_pattern_score(self, base_hash: str, pattern_type: str):
        """
        为行为模式添加分数
        
        Args:
            base_hash: 基础指纹哈希
            pattern_type: 行为模式类型
        """
        score = self.behavior_patterns.get(pattern_type, 0)
        if score > 0:
            self.add_score_to_fingerprint(
                base_hash, 
                score, 
                f"行为模式: {pattern_type}"
            )
    
    def add_reward_score(self, base_hash: str, reward_type: str):
        """
        为良好行为添加奖励分数（负分，降低威胁评分）
        
        Args:
            base_hash: 基础指纹哈希
            reward_type: 奖励类型
        """
        score = self.score_rewards.get(reward_type, 0)
        if score != 0:
            self.add_score_to_fingerprint(
                base_hash,
                score,
                f"良好行为: {reward_type}",
                None
            )
    
    def get_score_history(self, base_hash: str, limit: int = 20) -> List[Dict]:
        """获取评分历史"""
        from models.database import ScoreHistory
        
        session = self.db.get_session()
        try:
            history = session.query(ScoreHistory).filter(
                ScoreHistory.base_hash == base_hash
            ).order_by(ScoreHistory.timestamp.desc()).limit(limit).all()
            
            return [{
                'timestamp': h.timestamp.isoformat(),
                'score_change': h.score_change,
                'total_score': h.total_score,
                'reason': h.reason
            } for h in history]
        finally:
            session.close()
    
    def reset_score(self, base_hash: str, reason: str = "手动重置"):
        """重置指纹分数"""
        from models.database import Fingerprint, ScoreHistory
        
        session = self.db.get_session()
        try:
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if fingerprint:
                old_score = fingerprint.threat_score
                fingerprint.threat_score = 0
                fingerprint.last_score_update = datetime.now()
                
                # 记录重置
                score_history = ScoreHistory(
                    fingerprint_id=fingerprint.id,
                    base_hash=base_hash,
                    score_change=-old_score,
                    total_score=0,
                    reason=reason
                )
                session.add(score_history)
                
                session.commit()
                return True
        except Exception as e:
            session.rollback()
            print(f"重置分数失败: {e}")
            return False
        finally:
            session.close()
    
    def get_top_threat_scores(self, limit: int = 50) -> List[Dict]:
        """获取威胁分数最高的指纹"""
        from models.database import Fingerprint
        
        session = self.db.get_session()
        try:
            fingerprints = session.query(Fingerprint).order_by(
                Fingerprint.threat_score.desc()
            ).limit(limit).all()
            
            results = []
            for fp in fingerprints:
                current_score = self._apply_score_decay(fp)
                risk_level = self._determine_risk_level(current_score)
                
                results.append({
                    'base_hash': fp.base_hash,
                    'ip': fp.ip,
                    'score': current_score,
                    'risk_level': risk_level,
                    'visit_count': fp.visit_count,
                    'last_seen': fp.last_seen.isoformat() if fp.last_seen else None
                })
            
            return results
        finally:
            session.close()
    
    def generate_score_report(self, base_hash: str) -> Dict:
        """生成详细的评分报告"""
        from models.database import Fingerprint
        
        session = self.db.get_session()
        try:
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if not fingerprint:
                return {'error': '指纹不存在'}
            
            current_score = self._apply_score_decay(fingerprint)
            risk_level = self._determine_risk_level(current_score)
            should_ban, ban_type, duration = self.should_ban(base_hash)
            
            # 获取评分历史
            history = self.get_score_history(base_hash, 10)
            
            # 计算分数来源分布
            score_sources = {}
            for h in history:
                reason = h['reason']
                score_sources[reason] = score_sources.get(reason, 0) + h['score_change']
            
            return {
                'base_hash': base_hash,
                'ip': fingerprint.ip,
                'current_score': current_score,
                'original_score': fingerprint.threat_score,
                'risk_level': risk_level,
                'should_ban': should_ban,
                'ban_type': ban_type,
                'ban_duration': duration,
                'last_score_update': fingerprint.last_score_update.isoformat() if fingerprint.last_score_update else None,
                'score_sources': score_sources,
                'recent_history': history,
                'thresholds': {
                    'temporary_ban': self.thresholds['temporary_ban'],
                    'extended_ban': self.thresholds['extended_ban'],
                    'permanent_ban': self.thresholds['permanent_ban']
                }
            }
        finally:
            session.close()

