"""
记录导出管理器
将封禁、威胁、评分等记录导出到文件
"""
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class ExportManager:
    """记录导出管理器"""
    
    def __init__(self, db, config: Dict):
        self.db = db
        self.config = config
        self.export_config = config.get('export', {})
        
        # 导出目录
        self.export_dir = Path(self.export_config.get('directory', 'exports'))
        self.export_dir.mkdir(exist_ok=True)
        
        # 自动导出配置
        self.auto_export_enabled = self.export_config.get('auto_export_enabled', False)
        self.auto_export_interval = self.export_config.get('auto_export_interval_hours', 24)
    
    def export_ban_records(self, output_file: str = None, format: str = 'json',
                          active_only: bool = False, days: int = None) -> str:
        """
        导出封禁记录
        
        Args:
            output_file: 输出文件路径（None则自动生成）
            format: 导出格式 (json, csv, txt)
            active_only: 只导出活跃的封禁
            days: 只导出最近N天的记录
            
        Returns:
            导出的文件路径
        """
        from models.database import BanRecord
        
        session = self.db.get_session()
        try:
            # 构建查询
            query = session.query(BanRecord)
            
            if active_only:
                query = query.filter(BanRecord.is_active == True)
            
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                query = query.filter(BanRecord.banned_at >= cutoff)
            
            records = query.order_by(BanRecord.banned_at.desc()).all()
            
            # 转换为字典列表
            data = [{
                'ip': r.ip,
                'banned_at': r.banned_at.strftime('%Y-%m-%d %H:%M:%S'),
                'ban_until': r.ban_until.strftime('%Y-%m-%d %H:%M:%S') if r.ban_until else '永久',
                'is_active': r.is_active,
                'is_permanent': r.is_permanent,
                'reason': r.reason,
                'ban_count': r.ban_count,
                'unbanned_at': r.unbanned_at.strftime('%Y-%m-%d %H:%M:%S') if r.unbanned_at else None,
                'notes': r.notes
            } for r in records]
            
            # 生成文件名
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                status = 'active' if active_only else 'all'
                output_file = self.export_dir / f'ban_records_{status}_{timestamp}.{format}'
            else:
                output_file = Path(output_file)
            
            # 导出
            if format == 'json':
                self._export_json(data, output_file)
            elif format == 'csv':
                self._export_csv(data, output_file)
            elif format == 'txt':
                self._export_txt_ban_records(data, output_file)
            
            print(f"✓ 封禁记录已导出到: {output_file} (共{len(data)}条)")
            return str(output_file)
            
        finally:
            session.close()
    
    def export_threat_events(self, output_file: str = None, format: str = 'json',
                            days: int = 7, severity: str = None) -> str:
        """
        导出威胁事件
        
        Args:
            output_file: 输出文件路径
            format: 导出格式
            days: 最近N天
            severity: 严重程度筛选
        """
        from models.database import ThreatEvent
        
        session = self.db.get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            query = session.query(ThreatEvent).filter(
                ThreatEvent.timestamp >= cutoff
            )
            
            if severity:
                query = query.filter(ThreatEvent.severity == severity)
            
            records = query.order_by(ThreatEvent.timestamp.desc()).all()
            
            data = [{
                'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'ip': r.ip,
                'base_hash': r.base_hash[:16] + '...',
                'threat_type': r.threat_type,
                'severity': r.severity,
                'description': r.description,
                'handled': r.handled,
                'action_taken': r.action_taken
            } for r in records]
            
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                sev = f'_{severity}' if severity else ''
                output_file = self.export_dir / f'threats{sev}_{timestamp}.{format}'
            else:
                output_file = Path(output_file)
            
            if format == 'json':
                self._export_json(data, output_file)
            elif format == 'csv':
                self._export_csv(data, output_file)
            elif format == 'txt':
                self._export_txt_threats(data, output_file)
            
            print(f"✓ 威胁事件已导出到: {output_file} (共{len(data)}条)")
            return str(output_file)
            
        finally:
            session.close()
    
    def export_score_records(self, output_file: str = None, format: str = 'json',
                            min_score: int = 0, limit: int = 100) -> str:
        """
        导出评分记录
        
        Args:
            output_file: 输出文件路径
            format: 导出格式
            min_score: 最低分数
            limit: 导出数量
        """
        from models.database import Fingerprint
        
        session = self.db.get_session()
        try:
            records = session.query(Fingerprint).filter(
                Fingerprint.threat_score >= min_score
            ).order_by(Fingerprint.threat_score.desc()).limit(limit).all()
            
            data = [{
                'ip': r.ip,
                'base_hash': r.base_hash[:16] + '...',
                'threat_score': r.threat_score,
                'visit_count': r.visit_count,
                'first_seen': r.first_seen.strftime('%Y-%m-%d %H:%M:%S'),
                'last_seen': r.last_seen.strftime('%Y-%m-%d %H:%M:%S'),
                'last_score_update': r.last_score_update.strftime('%Y-%m-%d %H:%M:%S') if r.last_score_update else None,
                'identity_chain_id': r.identity_chain_id
            } for r in records]
            
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = self.export_dir / f'scores_min{min_score}_{timestamp}.{format}'
            else:
                output_file = Path(output_file)
            
            if format == 'json':
                self._export_json(data, output_file)
            elif format == 'csv':
                self._export_csv(data, output_file)
            elif format == 'txt':
                self._export_txt_scores(data, output_file)
            
            print(f"✓ 评分记录已导出到: {output_file} (共{len(data)}条)")
            return str(output_file)
            
        finally:
            session.close()
    
    def export_access_logs(self, output_file: str = None, format: str = 'json',
                          ip: str = None, hours: int = 24, limit: int = 1000) -> str:
        """
        导出访问日志
        
        Args:
            output_file: 输出文件路径
            format: 导出格式
            ip: 筛选特定IP
            hours: 最近N小时
            limit: 导出数量
        """
        from models.database import AccessLog
        
        session = self.db.get_session()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            query = session.query(AccessLog).filter(
                AccessLog.timestamp >= cutoff
            )
            
            if ip:
                query = query.filter(AccessLog.ip == ip)
            
            records = query.order_by(AccessLog.timestamp.desc()).limit(limit).all()
            
            data = [{
                'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'ip': r.ip,
                'request_method': r.request_method,
                'request_path': r.request_path,
                'status_code': r.status_code,
                'response_size': r.response_size,
                'user_agent': r.user_agent[:100]
            } for r in records]
            
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                ip_suffix = f'_{ip.replace(".", "_")}' if ip else ''
                output_file = self.export_dir / f'access_logs{ip_suffix}_{timestamp}.{format}'
            else:
                output_file = Path(output_file)
            
            if format == 'json':
                self._export_json(data, output_file)
            elif format == 'csv':
                self._export_csv(data, output_file)
            elif format == 'txt':
                self._export_txt_access_logs(data, output_file)
            
            print(f"✓ 访问日志已导出到: {output_file} (共{len(data)}条)")
            return str(output_file)
            
        finally:
            session.close()
    
    def export_all_records(self, format: str = 'json') -> Dict[str, str]:
        """
        导出所有记录（生成完整报告）
        
        Returns:
            导出文件路径字典
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = self.export_dir / f'full_report_{timestamp}'
        report_dir.mkdir(exist_ok=True)
        
        results = {}
        
        print("\n开始导出完整报告...")
        print("=" * 60)
        
        # 1. 封禁记录
        print("\n[1/5] 导出封禁记录...")
        results['ban_records'] = self.export_ban_records(
            report_dir / f'ban_records.{format}',
            format=format
        )
        
        # 2. 威胁事件
        print("\n[2/5] 导出威胁事件...")
        results['threat_events'] = self.export_threat_events(
            report_dir / f'threat_events.{format}',
            format=format,
            days=30
        )
        
        # 3. 评分记录
        print("\n[3/5] 导出评分记录...")
        results['score_records'] = self.export_score_records(
            report_dir / f'score_records.{format}',
            format=format,
            limit=500
        )
        
        # 4. 访问日志（最近24小时）
        print("\n[4/5] 导出访问日志...")
        results['access_logs'] = self.export_access_logs(
            report_dir / f'access_logs.{format}',
            format=format,
            hours=24,
            limit=5000
        )
        
        # 5. 统计摘要
        print("\n[5/5] 生成统计摘要...")
        results['summary'] = self._export_summary(report_dir / 'summary.txt')
        
        print("\n" + "=" * 60)
        print(f"✓ 完整报告已导出到: {report_dir}")
        print(f"  包含 {len(results)} 个文件")
        
        return results
    
    def _export_json(self, data: List[Dict], output_file: Path):
        """导出为JSON格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_csv(self, data: List[Dict], output_file: Path):
        """导出为CSV格式"""
        if not data:
            return
        
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _export_txt_ban_records(self, data: List[Dict], output_file: Path):
        """导出封禁记录为TXT格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("封禁记录报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总记录数: {len(data)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, record in enumerate(data, 1):
                f.write(f"[{i}] IP: {record['ip']}\n")
                f.write(f"    封禁时间: {record['banned_at']}\n")
                f.write(f"    解封时间: {record['ban_until']}\n")
                f.write(f"    状态: {'活跃' if record['is_active'] else '已解封'}\n")
                f.write(f"    原因: {record['reason']}\n")
                f.write(f"    封禁次数: {record['ban_count']}\n")
                f.write("-" * 80 + "\n")
    
    def _export_txt_threats(self, data: List[Dict], output_file: Path):
        """导出威胁事件为TXT格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("威胁事件报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总记录数: {len(data)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, record in enumerate(data, 1):
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(record['severity'], '⚪')
                
                f.write(f"[{i}] {severity_emoji} {record['threat_type']}\n")
                f.write(f"    时间: {record['timestamp']}\n")
                f.write(f"    IP: {record['ip']}\n")
                f.write(f"    严重程度: {record['severity']}\n")
                f.write(f"    描述: {record['description']}\n")
                f.write(f"    已处理: {'是' if record['handled'] else '否'}\n")
                f.write("-" * 80 + "\n")
    
    def _export_txt_scores(self, data: List[Dict], output_file: Path):
        """导出评分记录为TXT格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("威胁评分报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总记录数: {len(data)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, record in enumerate(data, 1):
                score = record['threat_score']
                risk_level = '极高' if score >= 150 else '高' if score >= 100 else '中' if score >= 60 else '低'
                
                f.write(f"[{i}] IP: {record['ip']} (风险等级: {risk_level})\n")
                f.write(f"    威胁评分: {score}\n")
                f.write(f"    访问次数: {record['visit_count']}\n")
                f.write(f"    首次访问: {record['first_seen']}\n")
                f.write(f"    最后访问: {record['last_seen']}\n")
                f.write("-" * 80 + "\n")
    
    def _export_txt_access_logs(self, data: List[Dict], output_file: Path):
        """导出访问日志为TXT格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("访问日志报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总记录数: {len(data)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, record in enumerate(data, 1):
                f.write(f"[{i}] {record['timestamp']} - {record['ip']}\n")
                f.write(f"    {record['request_method']} {record['request_path']} -> {record['status_code']}\n")
                f.write(f"    User-Agent: {record['user_agent']}\n")
                f.write("-" * 80 + "\n")
    
    def _export_summary(self, output_file: Path) -> str:
        """生成统计摘要"""
        from models.database import (
            BanRecord, ThreatEvent, Fingerprint, AccessLog, IdentityChain
        )
        from sqlalchemy import func
        
        session = self.db.get_session()
        try:
            cutoff_24h = datetime.now() - timedelta(hours=24)
            cutoff_7d = datetime.now() - timedelta(days=7)
            
            summary = []
            summary.append("=" * 80)
            summary.append("系统统计摘要")
            summary.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary.append("=" * 80)
            summary.append("")
            
            # 封禁统计
            summary.append("【封禁统计】")
            active_bans = session.query(func.count(BanRecord.id)).filter(
                BanRecord.is_active == True
            ).scalar()
            permanent_bans = session.query(func.count(BanRecord.id)).filter(
                BanRecord.is_permanent == True
            ).scalar()
            summary.append(f"  活跃封禁: {active_bans}")
            summary.append(f"  永久封禁: {permanent_bans}")
            summary.append("")
            
            # 威胁统计
            summary.append("【威胁统计】")
            threats_24h = session.query(func.count(ThreatEvent.id)).filter(
                ThreatEvent.timestamp >= cutoff_24h
            ).scalar()
            threats_7d = session.query(func.count(ThreatEvent.id)).filter(
                ThreatEvent.timestamp >= cutoff_7d
            ).scalar()
            summary.append(f"  24小时内威胁: {threats_24h}")
            summary.append(f"  7天内威胁: {threats_7d}")
            summary.append("")
            
            # 访问统计
            summary.append("【访问统计】")
            access_24h = session.query(func.count(AccessLog.id)).filter(
                AccessLog.timestamp >= cutoff_24h
            ).scalar()
            unique_ips_24h = session.query(func.count(func.distinct(AccessLog.ip))).filter(
                AccessLog.timestamp >= cutoff_24h
            ).scalar()
            summary.append(f"  24小时访问: {access_24h}")
            summary.append(f"  唯一IP: {unique_ips_24h}")
            summary.append("")
            
            # 评分统计
            summary.append("【评分统计】")
            high_score_count = session.query(func.count(Fingerprint.id)).filter(
                Fingerprint.threat_score >= 60
            ).scalar()
            avg_score = session.query(func.avg(Fingerprint.threat_score)).scalar()
            summary.append(f"  高分用户(≥60): {high_score_count}")
            summary.append(f"  平均评分: {avg_score:.2f if avg_score else 0}")
            summary.append("")
            
            # 身份链统计
            summary.append("【身份链统计】")
            total_chains = session.query(func.count(IdentityChain.id)).scalar()
            summary.append(f"  总身份链: {total_chains}")
            summary.append("")
            
            summary.append("=" * 80)
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary))
            
            return str(output_file)
            
        finally:
            session.close()
    
    def schedule_auto_export(self):
        """定时自动导出（在主程序中调用）"""
        if not self.auto_export_enabled:
            return
        
        print(f"自动导出已启用，每{self.auto_export_interval}小时导出一次")
        
        # 立即导出一次
        self.export_all_records(format='json')

