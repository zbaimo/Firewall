"""
自定义规则引擎
允许用户定义灵活的检测规则
"""
import re
from typing import Dict, List, Any
from datetime import datetime, time


class RuleEngine:
    """自定义规则引擎"""
    
    def __init__(self, db, config: Dict):
        self.db = db
        self.config = config
        self.rules = []
        
        # 从配置加载规则
        custom_rules = config.get('custom_rules', [])
        for rule_data in custom_rules:
            self.add_rule(CustomRule(rule_data))
        
        # 从数据库加载规则
        self.load_rules_from_db()
        
        print(f"✓ 自定义规则引擎已加载 ({len(self.rules)} 条规则)")
    
    def add_rule(self, rule):
        """添加规则"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def evaluate(self, log_data: Dict) -> List[Dict]:
        """
        评估所有规则
        
        Returns:
            匹配的规则列表
        """
        matches = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if rule.matches(log_data):
                matches.append({
                    'rule_name': rule.name,
                    'score': rule.score,
                    'action': rule.action,
                    'priority': rule.priority
                })
        
        return matches
    
    def load_rules_from_db(self):
        """从数据库加载规则"""
        from models.database import ScoringRule
        
        session = self.db.get_session()
        try:
            db_rules = session.query(ScoringRule).filter(
                ScoringRule.enabled == True
            ).order_by(ScoringRule.priority.desc()).all()
            
            for db_rule in db_rules:
                import json
                rule_data = {
                    'name': db_rule.name,
                    'description': db_rule.description,
                    'conditions': json.loads(db_rule.conditions) if db_rule.conditions else {},
                    'score': db_rule.score,
                    'priority': db_rule.priority,
                    'enabled': db_rule.enabled
                }
                self.add_rule(CustomRule(rule_data))
        finally:
            session.close()
    
    def save_rule_to_db(self, rule_data: Dict) -> int:
        """保存规则到数据库"""
        from models.database import ScoringRule
        import json
        
        session = self.db.get_session()
        try:
            rule = ScoringRule(
                name=rule_data['name'],
                description=rule_data.get('description', ''),
                rule_type=rule_data.get('rule_type', 'custom'),
                conditions=json.dumps(rule_data.get('conditions', {})),
                score=rule_data.get('score', 0),
                enabled=rule_data.get('enabled', True),
                priority=rule_data.get('priority', 0)
            )
            session.add(rule)
            session.commit()
            return rule.id
        except Exception as e:
            session.rollback()
            print(f"保存规则失败: {e}")
            return None
        finally:
            session.close()


class CustomRule:
    """自定义规则"""
    
    def __init__(self, rule_data: Dict):
        self.name = rule_data['name']
        self.description = rule_data.get('description', '')
        self.conditions = rule_data.get('conditions', {})
        self.score = rule_data.get('score', 0)
        self.action = rule_data.get('action', 'score')
        self.priority = rule_data.get('priority', 0)
        self.enabled = rule_data.get('enabled', True)
        
        # 编译正则表达式（如果有）
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.path_pattern = None
        self.ua_pattern = None
        
        if 'path_pattern' in self.conditions:
            try:
                self.path_pattern = re.compile(self.conditions['path_pattern'])
            except:
                pass
        
        if 'user_agent_pattern' in self.conditions:
            try:
                self.ua_pattern = re.compile(self.conditions['user_agent_pattern'])
            except:
                pass
    
    def matches(self, log_data: Dict) -> bool:
        """检查日志是否匹配规则"""
        # 检查所有条件（AND关系）
        for key, value in self.conditions.items():
            if not self._check_condition(key, value, log_data):
                return False
        
        return True
    
    def _check_condition(self, key: str, value: Any, log_data: Dict) -> bool:
        """检查单个条件"""
        
        # 时间范围检查
        if key == 'time_range':
            return self._check_time_range(value, log_data)
        
        # 路径包含
        if key == 'path_contains':
            request_path = log_data.get('request_path', '')
            return value in request_path
        
        # 路径正则匹配
        if key == 'path_pattern' and self.path_pattern:
            request_path = log_data.get('request_path', '')
            return self.path_pattern.search(request_path) is not None
        
        # User-Agent匹配
        if key == 'user_agent_contains':
            user_agent = log_data.get('user_agent', '').lower()
            return value.lower() in user_agent
        
        if key == 'user_agent_pattern' and self.ua_pattern:
            user_agent = log_data.get('user_agent', '')
            return self.ua_pattern.search(user_agent) is not None
        
        # 状态码
        if key == 'status_code':
            if isinstance(value, list):
                return log_data.get('status_code') in value
            else:
                return log_data.get('status_code') == value
        
        if key == 'status_code_range':
            status = log_data.get('status_code', 0)
            return value[0] <= status <= value[1]
        
        # 请求方法
        if key == 'request_method':
            if isinstance(value, list):
                return log_data.get('request_method') in value
            else:
                return log_data.get('request_method') == value
        
        # 查询参数包含
        if key == 'query_contains':
            query_params = log_data.get('query_params', '')
            return value in query_params
        
        # Referer检查
        if key == 'has_referer':
            has_referer = bool(log_data.get('referer'))
            return has_referer == value
        
        # 响应大小
        if key == 'response_size_gt':
            return log_data.get('response_size', 0) > value
        
        if key == 'response_size_lt':
            return log_data.get('response_size', 0) < value
        
        # 默认：精确匹配
        return log_data.get(key) == value
    
    def _check_time_range(self, time_range: str, log_data: Dict) -> bool:
        """检查时间范围"""
        try:
            # 格式: "02:00-05:00"
            start_str, end_str = time_range.split('-')
            start_time = time.fromisoformat(start_str.strip())
            end_time = time.fromisoformat(end_str.strip())
            
            current_time = datetime.now().time()
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                # 跨越午夜
                return current_time >= start_time or current_time <= end_time
        except:
            return False

