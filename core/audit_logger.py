"""
审计日志系统
记录所有关键操作，用于合规审计和问题追溯
"""
import json
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path


class AuditLogger:
    """审计日志记录器"""
    
    # 操作类型常量
    ACTION_BAN = 'ban'
    ACTION_UNBAN = 'unban'
    ACTION_CONFIG_CHANGE = 'config_change'
    ACTION_RULE_ADD = 'rule_add'
    ACTION_RULE_UPDATE = 'rule_update'
    ACTION_RULE_DELETE = 'rule_delete'
    ACTION_EXPORT = 'export'
    ACTION_SCORE_ADJUST = 'score_adjust'
    ACTION_WHITELIST_ADD = 'whitelist_add'
    ACTION_BLACKLIST_ADD = 'blacklist_add'
    ACTION_SYSTEM_START = 'system_start'
    ACTION_SYSTEM_STOP = 'system_stop'
    
    def __init__(self, config: Dict):
        self.config = config
        audit_config = config.get('audit', {})
        
        self.enabled = audit_config.get('enabled', True)
        self.log_file = Path(audit_config.get('file', 'audit.log'))
        self.max_size_mb = audit_config.get('max_size_mb', 100)
        
        # 创建审计日志文件
        self.log_file.parent.mkdir(exist_ok=True, parents=True)
        
        if self.enabled:
            print(f"✓ 审计日志已启用: {self.log_file}")
        else:
            print("ℹ 审计日志未启用")
    
    def log(self, action: str, operator: str, target: str, 
            details: Dict = None, result: str = 'success'):
        """
        记录审计日志
        
        Args:
            action: 操作类型
            operator: 操作者（system/admin/用户名）
            target: 操作目标（IP/配置项/规则名等）
            details: 详细信息
            result: 操作结果（success/failure）
        """
        if not self.enabled:
            return
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'operator': operator,
            'target': target,
            'details': details or {},
            'result': result
        }
        
        try:
            # 检查文件大小，超过限制则轮转
            if self.log_file.exists():
                size_mb = self.log_file.stat().st_size / (1024 * 1024)
                if size_mb >= self.max_size_mb:
                    self._rotate_log()
            
            # 追加日志
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"✗ 审计日志记录失败: {e}")
    
    def log_ban(self, ip: str, reason: str, duration: int, operator: str = 'system'):
        """记录封禁操作"""
        self.log(
            action=self.ACTION_BAN,
            operator=operator,
            target=ip,
            details={
                'reason': reason,
                'duration_seconds': duration,
                'duration_human': self._format_duration(duration)
            }
        )
    
    def log_unban(self, ip: str, operator: str = 'system'):
        """记录解封操作"""
        self.log(
            action=self.ACTION_UNBAN,
            operator=operator,
            target=ip,
            details={}
        )
    
    def log_config_change(self, config_key: str, old_value, new_value, operator: str = 'admin'):
        """记录配置修改"""
        self.log(
            action=self.ACTION_CONFIG_CHANGE,
            operator=operator,
            target=config_key,
            details={
                'old_value': str(old_value),
                'new_value': str(new_value)
            }
        )
    
    def log_rule_change(self, action: str, rule_name: str, rule_data: Dict, operator: str = 'admin'):
        """记录规则变更"""
        self.log(
            action=action,
            operator=operator,
            target=rule_name,
            details={'rule_data': rule_data}
        )
    
    def log_export(self, export_type: str, format: str, count: int, operator: str = 'admin'):
        """记录数据导出"""
        self.log(
            action=self.ACTION_EXPORT,
            operator=operator,
            target=export_type,
            details={
                'format': format,
                'count': count,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_score_adjust(self, ip: str, old_score: int, new_score: int, 
                        reason: str, operator: str = 'system'):
        """记录评分调整"""
        self.log(
            action=self.ACTION_SCORE_ADJUST,
            operator=operator,
            target=ip,
            details={
                'old_score': old_score,
                'new_score': new_score,
                'delta': new_score - old_score,
                'reason': reason
            }
        )
    
    def log_whitelist_add(self, ip: str, description: str, operator: str = 'admin'):
        """记录白名单添加"""
        self.log(
            action=self.ACTION_WHITELIST_ADD,
            operator=operator,
            target=ip,
            details={'description': description}
        )
    
    def log_blacklist_add(self, ip: str, reason: str, operator: str = 'admin'):
        """记录黑名单添加"""
        self.log(
            action=self.ACTION_BLACKLIST_ADD,
            operator=operator,
            target=ip,
            details={'reason': reason}
        )
    
    def log_system_event(self, event: str, details: Dict = None):
        """记录系统事件"""
        self.log(
            action=event,
            operator='system',
            target='system',
            details=details or {}
        )
    
    def _rotate_log(self):
        """轮转日志文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.log_file.parent / f"{self.log_file.stem}_{timestamp}.log"
            self.log_file.rename(backup_file)
            print(f"✓ 审计日志已轮转: {backup_file}")
        except Exception as e:
            print(f"✗ 审计日志轮转失败: {e}")
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分钟"
        elif seconds < 86400:
            return f"{seconds // 3600}小时"
        else:
            return f"{seconds // 86400}天"
    
    def search_logs(self, action: str = None, operator: str = None, 
                   target: str = None, hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        搜索审计日志
        
        Args:
            action: 操作类型筛选
            operator: 操作者筛选
            target: 目标筛选
            hours: 时间范围（小时）
            limit: 返回数量限制
            
        Returns:
            审计日志列表
        """
        if not self.log_file.exists():
            return []
        
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        results = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # 时间筛选
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time < cutoff:
                            continue
                        
                        # 条件筛选
                        if action and entry['action'] != action:
                            continue
                        if operator and entry['operator'] != operator:
                            continue
                        if target and entry['target'] != target:
                            continue
                        
                        results.append(entry)
                        
                        if len(results) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            return results[::-1]  # 最新的在前
            
        except Exception as e:
            print(f"✗ 审计日志搜索失败: {e}")
            return []
    
    def get_statistics(self, hours: int = 24) -> Dict:
        """获取审计统计信息"""
        logs = self.search_logs(hours=hours, limit=10000)
        
        if not logs:
            return {
                'total': 0,
                'by_action': {},
                'by_operator': {},
                'success_rate': 0
            }
        
        # 统计
        by_action = {}
        by_operator = {}
        success_count = 0
        
        for log in logs:
            action = log['action']
            operator = log['operator']
            
            by_action[action] = by_action.get(action, 0) + 1
            by_operator[operator] = by_operator.get(operator, 0) + 1
            
            if log.get('result') == 'success':
                success_count += 1
        
        return {
            'total': len(logs),
            'by_action': by_action,
            'by_operator': by_operator,
            'success_rate': (success_count / len(logs) * 100) if logs else 0,
            'time_range_hours': hours
        }
    
    def export_audit_logs(self, output_file: str, hours: int = 24):
        """导出审计日志"""
        logs = self.search_logs(hours=hours, limit=100000)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 审计日志已导出: {output_file} (共{len(logs)}条)")
            
            # 记录导出操作
            self.log_export('audit_logs', 'json', len(logs), 'admin')
            
        except Exception as e:
            print(f"✗ 审计日志导出失败: {e}")
    
    def generate_audit_report(self, hours: int = 24) -> str:
        """生成审计报告（文本格式）"""
        stats = self.get_statistics(hours)
        logs = self.search_logs(hours=hours, limit=50)
        
        report = []
        report.append("=" * 80)
        report.append("审计日志报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"时间范围: 最近{hours}小时")
        report.append("=" * 80)
        report.append("")
        
        # 统计摘要
        report.append("【统计摘要】")
        report.append(f"  总操作数: {stats['total']}")
        report.append(f"  成功率: {stats['success_rate']:.1f}%")
        report.append("")
        
        # 按操作类型统计
        report.append("【操作类型分布】")
        for action, count in sorted(stats['by_action'].items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {action}: {count}")
        report.append("")
        
        # 按操作者统计
        report.append("【操作者分布】")
        for operator, count in sorted(stats['by_operator'].items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {operator}: {count}")
        report.append("")
        
        # 最近操作
        report.append("【最近操作记录】(最多50条)")
        report.append("-" * 80)
        for i, log in enumerate(logs[:50], 1):
            report.append(f"\n[{i}] {log['timestamp']}")
            report.append(f"    操作: {log['action']}")
            report.append(f"    操作者: {log['operator']}")
            report.append(f"    目标: {log['target']}")
            if log.get('details'):
                report.append(f"    详情: {json.dumps(log['details'], ensure_ascii=False)}")
            report.append(f"    结果: {log.get('result', 'success')}")
        
        report.append("\n" + "=" * 80)
        
        return '\n'.join(report)

