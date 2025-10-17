"""
Web管理后台
提供可视化的管理界面
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta
import json


def create_app(config, db, firewall, threat_detector, identity_chain_mgr):
    """创建Flask应用"""
    
    app = Flask(__name__)
    app.secret_key = config.get('web_dashboard', {}).get('secret_key', 'change-me')
    
    @app.route('/')
    def index():
        """主页 - 仪表板"""
        return render_template('dashboard.html')
    
    @app.route('/api/stats/overview')
    def stats_overview():
        """获取总览统计"""
        from models.database import AccessLog, BanRecord, ThreatEvent, Fingerprint, IdentityChain
        from sqlalchemy import func
        
        session = db.get_session()
        try:
            # 24小时内的统计
            cutoff = datetime.now() - timedelta(hours=24)
            
            total_requests = session.query(func.count(AccessLog.id)).filter(
                AccessLog.timestamp >= cutoff
            ).scalar()
            
            unique_ips = session.query(func.count(func.distinct(AccessLog.ip))).filter(
                AccessLog.timestamp >= cutoff
            ).scalar()
            
            active_bans = session.query(func.count(BanRecord.id)).filter(
                BanRecord.is_active == True
            ).scalar()
            
            threats_detected = session.query(func.count(ThreatEvent.id)).filter(
                ThreatEvent.timestamp >= cutoff
            ).scalar()
            
            total_fingerprints = session.query(func.count(Fingerprint.id)).scalar()
            total_chains = session.query(func.count(IdentityChain.id)).scalar()
            
            return jsonify({
                'total_requests': total_requests or 0,
                'unique_ips': unique_ips or 0,
                'active_bans': active_bans or 0,
                'threats_detected': threats_detected or 0,
                'total_fingerprints': total_fingerprints or 0,
                'total_chains': total_chains or 0
            })
        finally:
            session.close()
    
    @app.route('/api/stats/threats')
    def stats_threats():
        """威胁统计"""
        hours = request.args.get('hours', 24, type=int)
        stats = threat_detector.get_threat_statistics(hours)
        return jsonify(stats)
    
    @app.route('/api/bans')
    def list_bans():
        """获取封禁列表"""
        bans = firewall.list_banned_ips()
        return jsonify(bans)
    
    @app.route('/api/bans/<ip>', methods=['DELETE'])
    def unban_ip(ip):
        """解封IP"""
        success = firewall.unban_ip(ip)
        return jsonify({'success': success})
    
    @app.route('/api/bans', methods=['POST'])
    def ban_ip():
        """手动封禁IP"""
        data = request.json
        ip = data.get('ip')
        reason = data.get('reason', '手动封禁')
        duration = data.get('duration', 3600)
        
        if not ip:
            return jsonify({'success': False, 'error': 'IP地址不能为空'}), 400
        
        success = firewall.ban_ip(ip, reason, duration)
        return jsonify({'success': success})
    
    @app.route('/api/threats/recent')
    def recent_threats():
        """最近的威胁事件"""
        from models.database import ThreatEvent
        
        limit = request.args.get('limit', 50, type=int)
        hours = request.args.get('hours', 24, type=int)
        
        session = db.get_session()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            threats = session.query(ThreatEvent).filter(
                ThreatEvent.timestamp >= cutoff
            ).order_by(ThreatEvent.timestamp.desc()).limit(limit).all()
            
            return jsonify([{
                'id': t.id,
                'timestamp': t.timestamp.isoformat(),
                'ip': t.ip,
                'threat_type': t.threat_type,
                'severity': t.severity,
                'description': t.description,
                'handled': t.handled
            } for t in threats])
        finally:
            session.close()
    
    @app.route('/api/fingerprints')
    def list_fingerprints():
        """指纹列表"""
        from models.database import Fingerprint
        
        limit = request.args.get('limit', 100, type=int)
        sort_by = request.args.get('sort', 'threat_score')
        
        session = db.get_session()
        try:
            query = session.query(Fingerprint)
            
            if sort_by == 'threat_score':
                query = query.order_by(Fingerprint.threat_score.desc())
            elif sort_by == 'visit_count':
                query = query.order_by(Fingerprint.visit_count.desc())
            else:
                query = query.order_by(Fingerprint.last_seen.desc())
            
            fingerprints = query.limit(limit).all()
            
            return jsonify([{
                'id': fp.id,
                'base_hash': fp.base_hash,
                'ip': fp.ip,
                'visit_count': fp.visit_count,
                'unique_behaviors': fp.unique_behaviors,
                'threat_score': fp.threat_score,
                'first_seen': fp.first_seen.isoformat(),
                'last_seen': fp.last_seen.isoformat(),
                'identity_chain_id': fp.identity_chain_id
            } for fp in fingerprints])
        finally:
            session.close()
    
    @app.route('/api/chains')
    def list_chains():
        """身份链列表"""
        limit = request.args.get('limit', 100, type=int)
        chains = identity_chain_mgr.list_all_chains(limit)
        return jsonify(chains)
    
    @app.route('/api/chains/<int:chain_id>')
    def chain_detail(chain_id):
        """身份链详情"""
        info = identity_chain_mgr.get_chain_info(chain_id)
        if info:
            return jsonify(info)
        else:
            return jsonify({'error': '未找到身份链'}), 404
    
    @app.route('/api/logs/recent')
    def recent_logs():
        """最近的访问日志"""
        from models.database import AccessLog
        
        limit = request.args.get('limit', 100, type=int)
        ip = request.args.get('ip')
        
        session = db.get_session()
        try:
            query = session.query(AccessLog).order_by(AccessLog.timestamp.desc())
            
            if ip:
                query = query.filter(AccessLog.ip == ip)
            
            logs = query.limit(limit).all()
            
            return jsonify([{
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'ip': log.ip,
                'request_method': log.request_method,
                'request_path': log.request_path,
                'status_code': log.status_code,
                'user_agent': log.user_agent[:100]
            } for log in logs])
        finally:
            session.close()
    
    @app.route('/api/search/ip/<ip>')
    def search_ip(ip):
        """搜索IP相关信息"""
        from models.database import AccessLog, Fingerprint, ThreatEvent, BanRecord
        
        session = db.get_session()
        try:
            # 基本信息
            log_count = session.query(func.count(AccessLog.id)).filter(
                AccessLog.ip == ip
            ).scalar()
            
            # 指纹
            fingerprints = session.query(Fingerprint).filter(
                Fingerprint.ip == ip
            ).all()
            
            # 威胁
            threats = session.query(ThreatEvent).filter(
                ThreatEvent.ip == ip
            ).order_by(ThreatEvent.timestamp.desc()).limit(10).all()
            
            # 封禁状态
            ban = session.query(BanRecord).filter(
                BanRecord.ip == ip,
                BanRecord.is_active == True
            ).first()
            
            return jsonify({
                'ip': ip,
                'log_count': log_count,
                'fingerprints': [{
                    'base_hash': fp.base_hash,
                    'visit_count': fp.visit_count,
                    'threat_score': fp.threat_score
                } for fp in fingerprints],
                'threats': [{
                    'timestamp': t.timestamp.isoformat(),
                    'threat_type': t.threat_type,
                    'severity': t.severity,
                    'description': t.description
                } for t in threats],
                'is_banned': ban is not None,
                'ban_info': {
                    'banned_at': ban.banned_at.isoformat(),
                    'ban_until': ban.ban_until.isoformat() if ban.ban_until else '永久',
                    'reason': ban.reason
                } if ban else None
            })
        finally:
            session.close()
    
    return app

