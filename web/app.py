"""
Web管理后台
提供可视化的管理界面
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os


def create_app(config, db, firewall, threat_detector, identity_chain_mgr, 
               cache_manager=None, geo_analyzer=None, audit_logger=None,
               scoring_system=None, port_manager=None, auth_manager=None):
    """创建Flask应用"""
    
    app = Flask(__name__)
    app.secret_key = config.get('web_dashboard', {}).get('secret_key', 'change-me')
    
    # 启用CORS
    CORS(app)
    
    # 存储模块引用
    app.cache_manager = cache_manager
    app.geo_analyzer = geo_analyzer
    app.audit_logger = audit_logger
    app.scoring_system = scoring_system
    app.port_manager = port_manager
    app.auth_manager = auth_manager
    
    # 会话管理
    from flask import session as flask_session
    
    def require_auth(f):
        """认证装饰器"""
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not auth_manager:
                return f(*args, **kwargs)  # 认证未启用，跳过
            
            if 'user_id' not in flask_session:
                return redirect(url_for('login'))
            
            # 检查是否需要修改密码
            if flask_session.get('require_password_change'):
                if request.endpoint != 'change_password' and request.endpoint != 'do_change_password':
                    return redirect(url_for('change_password'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/login', methods=['GET'])
    def login():
        """登录页面"""
        # 如果已登录，跳转到主页
        if 'user_id' in flask_session:
            return redirect(url_for('index'))
        return render_template('login.html')
    
    @app.route('/api/auth/login', methods=['POST'])
    def do_login():
        """执行登录"""
        if not auth_manager:
            return jsonify({'success': False, 'message': '认证未启用'}), 400
        
        data = request.json
        username = data.get('username')
        password = data.get('password')
        totp_token = data.get('totp_token')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        # 验证密码
        is_valid, user_info = auth_manager.verify_password(username, password)
        
        if not is_valid:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        # 如果需要2FA
        if user_info.get('require_2fa'):
            if not totp_token:
                return jsonify({
                    'success': False,
                    'require_2fa': True,
                    'message': '请输入双因素认证码'
                })
            
            # 验证TOTP
            if not auth_manager.verify_totp(username, totp_token):
                return jsonify({'success': False, 'message': '验证码错误'}), 401
        
        # 创建会话
        flask_session['user_id'] = user_info['user_id']
        flask_session['username'] = user_info['username']
        flask_session['is_admin'] = user_info['is_admin']
        flask_session['require_password_change'] = user_info['require_password_change']
        
        return jsonify({
            'success': True,
            'require_password_change': user_info['require_password_change'],
            'redirect': '/change-password' if user_info['require_password_change'] else '/'
        })
    
    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        """登出"""
        flask_session.clear()
        return jsonify({'success': True})
    
    @app.route('/change-password', methods=['GET'])
    def change_password():
        """修改密码页面"""
        if 'user_id' not in flask_session:
            return redirect(url_for('login'))
        return render_template('change_password.html')
    
    @app.route('/api/auth/change-password', methods=['POST'])
    def do_change_password():
        """执行密码修改"""
        if not auth_manager or 'username' not in flask_session:
            return jsonify({'success': False, 'message': '未登录'}), 401
        
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'message': '密码不能为空'}), 400
        
        success, message = auth_manager.change_password(
            flask_session['username'],
            old_password,
            new_password
        )
        
        if success:
            flask_session['require_password_change'] = False
        
        return jsonify({'success': success, 'message': message})
    
    @app.route('/settings', methods=['GET'])
    @require_auth
    def settings():
        """设置页面"""
        return render_template('settings.html')
    
    @app.route('/api/auth/totp/generate', methods=['POST'])
    @require_auth
    def generate_totp():
        """生成TOTP密钥"""
        if not auth_manager:
            return jsonify({'success': False}), 400
        
        username = flask_session.get('username')
        secret, qr_uri = auth_manager.generate_totp_secret(username)
        
        # 生成QR码
        import qrcode
        import io
        import base64
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'secret': secret,
            'qr_code': f'data:image/png;base64,{img_str}'
        })
    
    @app.route('/api/auth/totp/enable', methods=['POST'])
    @require_auth
    def enable_totp():
        """启用TOTP"""
        if not auth_manager:
            return jsonify({'success': False}), 400
        
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({'success': False, 'message': '请输入验证码'}), 400
        
        username = flask_session.get('username')
        success, message = auth_manager.enable_totp(username, token)
        
        return jsonify({'success': success, 'message': message})
    
    @app.route('/api/auth/totp/disable', methods=['POST'])
    @require_auth
    def disable_totp():
        """禁用TOTP"""
        if not auth_manager:
            return jsonify({'success': False}), 400
        
        data = request.json
        password = data.get('password')
        
        if not password:
            return jsonify({'success': False, 'message': '请输入密码'}), 400
        
        username = flask_session.get('username')
        success, message = auth_manager.disable_totp(username, password)
        
        return jsonify({'success': success, 'message': message})
    
    # 端口扫描API
    @app.route('/api/ports/scan', methods=['GET'])
    @require_auth
    def scan_ports():
        """扫描服务器端口"""
        try:
            from core.port_scanner import PortScanner
            scanner = PortScanner(db, config)
            
            # 扫描监听端口
            ports = scanner.get_listening_ports()
            
            # 分类
            categorized = scanner.categorize_ports(ports)
            
            return jsonify({
                'success': True,
                'total': len(ports),
                'ports': ports,
                'categorized': {
                    'external': categorized['external'],
                    'internal': categorized['internal'],
                    'web': categorized['web'],
                    'database': categorized['database'],
                    'remote': categorized['remote'],
                    'email': categorized['email'],
                    'dns': categorized['dns'],
                    'other': categorized['other']
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/')
    @require_auth
    def index():
        """主页 - 仪表板"""
        return render_template('dashboard.html', username=flask_session.get('username'))
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """静态文件服务"""
        return send_from_directory('static', filename)
    
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
        from sqlalchemy import func
        
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
            
            # 地理位置
            location = None
            if geo_analyzer:
                location = geo_analyzer.get_location(ip)
            
            return jsonify({
                'ip': ip,
                'log_count': log_count,
                'location': location,
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
    
    @app.route('/api/stats/realtime')
    def realtime_stats():
        """实时统计数据"""
        from models.database import AccessLog
        from sqlalchemy import func
        
        session = db.get_session()
        try:
            # 最近1分钟的请求数
            one_min_ago = datetime.now() - timedelta(minutes=1)
            requests_per_min = session.query(func.count(AccessLog.id)).filter(
                AccessLog.timestamp >= one_min_ago
            ).scalar()
            
            # Redis缓存统计
            cache_stats = {}
            if cache_manager and cache_manager.is_enabled():
                cache_stats = cache_manager.get_stats()
            
            return jsonify({
                'requests_per_min': requests_per_min,
                'cache_stats': cache_stats,
                'timestamp': datetime.now().isoformat()
            })
        finally:
            session.close()
    
    @app.route('/api/geo/countries')
    def geo_countries():
        """国家统计"""
        if not geo_analyzer:
            return jsonify({'error': '地理位置功能未启用'}), 400
        
        hours = request.args.get('hours', 24, type=int)
        stats = geo_analyzer.get_country_stats(hours)
        
        return jsonify(stats)
    
    @app.route('/api/audit/logs')
    def audit_logs():
        """审计日志"""
        if not audit_logger:
            return jsonify({'error': '审计日志未启用'}), 400
        
        action = request.args.get('action')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        logs = audit_logger.search_logs(action=action, hours=hours, limit=limit)
        
        return jsonify(logs)
    
    @app.route('/api/scores/top')
    def top_scores():
        """威胁评分最高的IP"""
        if not scoring_system:
            return jsonify([])
        
        limit = request.args.get('limit', 20, type=int)
        results = scoring_system.get_top_threat_scores(limit)
        
        return jsonify(results)
    
    @app.route('/api/system/health')
    def system_health():
        """系统健康检查"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': 'ok',
                'redis': 'not_configured',
                'geo_location': 'not_configured',
                'audit': 'not_configured'
            }
        }
        
        # 检查Redis
        if cache_manager and cache_manager.is_enabled():
            stats = cache_manager.get_stats()
            health['components']['redis'] = 'ok' if stats.get('connected') else 'error'
        
        # 检查地理位置
        if geo_analyzer and geo_analyzer.enabled:
            health['components']['geo_location'] = 'ok'
        
        # 检查审计日志
        if audit_logger and audit_logger.enabled:
            health['components']['audit'] = 'ok'
        
        return jsonify(health)
    
    # ==================== 端口管理 API ====================
    
    @app.route('/api/ports')
    def list_ports():
        """获取端口规则列表"""
        if not port_manager:
            return jsonify({'error': '端口管理器未启用'}), 400
        
        rules = port_manager.list_port_rules()
        return jsonify(rules)
    
    @app.route('/api/ports/common')
    def common_ports():
        """获取常用端口列表"""
        if not port_manager:
            return jsonify([])
        
        ports = port_manager.get_common_ports()
        return jsonify(ports)
    
    @app.route('/api/ports/open', methods=['POST'])
    def open_port():
        """开放端口"""
        if not port_manager:
            return jsonify({'error': '端口管理器未启用'}), 400
        
        data = request.json
        port = data.get('port')
        protocol = data.get('protocol', 'tcp')
        description = data.get('description', '')
        
        if not port:
            return jsonify({'error': '端口号不能为空'}), 400
        
        if not 1 <= port <= 65535:
            return jsonify({'error': '端口号必须在1-65535之间'}), 400
        
        success = port_manager.open_port(port, protocol, description, 'web_admin')
        
        return jsonify({
            'success': success,
            'message': f'端口 {port}/{protocol} 已开放' if success else '操作失败'
        })
    
    @app.route('/api/ports/close', methods=['POST'])
    def close_port():
        """关闭端口"""
        if not port_manager:
            return jsonify({'error': '端口管理器未启用'}), 400
        
        data = request.json
        port = data.get('port')
        protocol = data.get('protocol', 'tcp')
        
        if not port:
            return jsonify({'error': '端口号不能为空'}), 400
        
        success = port_manager.close_port(port, protocol, 'web_admin')
        
        return jsonify({
            'success': success,
            'message': f'端口 {port}/{protocol} 已关闭' if success else '操作失败'
        })
    
    @app.route('/api/ports/block', methods=['POST'])
    def block_port():
        """阻止端口"""
        if not port_manager:
            return jsonify({'error': '端口管理器未启用'}), 400
        
        data = request.json
        port = data.get('port')
        protocol = data.get('protocol', 'tcp')
        description = data.get('description', '')
        
        if not port:
            return jsonify({'error': '端口号不能为空'}), 400
        
        success = port_manager.block_port(port, protocol, description, 'web_admin')
        
        return jsonify({
            'success': success,
            'message': f'端口 {port}/{protocol} 已阻止' if success else '操作失败'
        })
    
    @app.route('/ports')
    def ports_page():
        """端口管理页面"""
        return render_template('ports.html')
    
    # ==================== 规则管理 API ====================
    
    @app.route('/rules')
    @require_auth
    def rules_page():
        """规则管理页面"""
        return render_template('rules.html', username=flask_session.get('username'))
    
    @app.route('/api/rules/threat')
    @require_auth
    def get_threat_rules():
        """获取所有威胁检测规则"""
        from models.database import ThreatDetectionRule
        
        session = db.get_session()
        try:
            rules = session.query(ThreatDetectionRule).order_by(ThreatDetectionRule.category).all()
            return jsonify({
                'success': True,
                'rules': [{
                    'id': r.id,
                    'category': r.category,
                    'name': r.name,
                    'description': r.description,
                    'enabled': r.enabled,
                    'patterns': r.patterns,
                    'parameters': r.parameters,
                    'threat_score': r.threat_score,
                    'created_at': r.created_at.isoformat() if r.created_at else None,
                    'updated_at': r.updated_at.isoformat() if r.updated_at else None
                } for r in rules]
            })
        finally:
            session.close()
    
    @app.route('/api/rules/threat/<int:rule_id>')
    @require_auth
    def get_threat_rule(rule_id):
        """获取单个威胁检测规则"""
        from models.database import ThreatDetectionRule
        
        session = db.get_session()
        try:
            rule = session.query(ThreatDetectionRule).filter(ThreatDetectionRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            return jsonify({
                'id': rule.id,
                'category': rule.category,
                'name': rule.name,
                'description': rule.description,
                'enabled': rule.enabled,
                'patterns': rule.patterns,
                'parameters': rule.parameters,
                'threat_score': rule.threat_score
            })
        finally:
            session.close()
    
    @app.route('/api/rules/threat', methods=['POST'])
    @require_auth
    def create_threat_rule():
        """创建威胁检测规则"""
        from models.database import ThreatDetectionRule
        
        data = request.json
        session = db.get_session()
        try:
            rule = ThreatDetectionRule(
                category=data.get('category'),
                name=data.get('name'),
                description=data.get('description'),
                enabled=data.get('enabled', True),
                patterns=data.get('patterns'),
                parameters=data.get('parameters'),
                threat_score=data.get('threat_score', 0)
            )
            session.add(rule)
            session.commit()
            
            return jsonify({'success': True, 'id': rule.id})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    @app.route('/api/rules/threat/<int:rule_id>', methods=['PUT'])
    @require_auth
    def update_threat_rule(rule_id):
        """更新威胁检测规则"""
        from models.database import ThreatDetectionRule
        
        data = request.json
        session = db.get_session()
        try:
            rule = session.query(ThreatDetectionRule).filter(ThreatDetectionRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            rule.category = data.get('category', rule.category)
            rule.name = data.get('name', rule.name)
            rule.description = data.get('description', rule.description)
            rule.enabled = data.get('enabled', rule.enabled)
            rule.patterns = data.get('patterns', rule.patterns)
            rule.parameters = data.get('parameters', rule.parameters)
            rule.threat_score = data.get('threat_score', rule.threat_score)
            rule.updated_at = datetime.now()
            
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    @app.route('/api/rules/threat/<int:rule_id>', methods=['DELETE'])
    @require_auth
    def delete_threat_rule(rule_id):
        """删除威胁检测规则"""
        from models.database import ThreatDetectionRule
        
        session = db.get_session()
        try:
            rule = session.query(ThreatDetectionRule).filter(ThreatDetectionRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            session.delete(rule)
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    @app.route('/api/rules/threat/<int:rule_id>/toggle', methods=['POST'])
    @require_auth
    def toggle_threat_rule(rule_id):
        """切换威胁检测规则启用状态"""
        from models.database import ThreatDetectionRule
        
        data = request.json
        session = db.get_session()
        try:
            rule = session.query(ThreatDetectionRule).filter(ThreatDetectionRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            rule.enabled = data.get('enabled', not rule.enabled)
            rule.updated_at = datetime.now()
            session.commit()
            return jsonify({'success': True, 'enabled': rule.enabled})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    # 自定义规则API
    @app.route('/api/rules/custom')
    @require_auth
    def get_custom_rules():
        """获取所有自定义规则"""
        from models.database import ScoringRule
        
        session = db.get_session()
        try:
            rules = session.query(ScoringRule).order_by(ScoringRule.priority.desc()).all()
            return jsonify({
                'success': True,
                'rules': [{
                    'id': r.id,
                    'name': r.name,
                    'description': r.description,
                    'enabled': r.enabled,
                    'rule_type': r.rule_type,
                    'conditions': r.conditions,
                    'score': r.score,
                    'action': r.action,
                    'priority': r.priority,
                    'created_at': r.created_at.isoformat() if r.created_at else None,
                    'updated_at': r.updated_at.isoformat() if r.updated_at else None
                } for r in rules]
            })
        finally:
            session.close()
    
    @app.route('/api/rules/custom/<int:rule_id>')
    @require_auth
    def get_custom_rule(rule_id):
        """获取单个自定义规则"""
        from models.database import ScoringRule
        
        session = db.get_session()
        try:
            rule = session.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            return jsonify({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'enabled': rule.enabled,
                'rule_type': rule.rule_type,
                'conditions': rule.conditions,
                'score': rule.score,
                'action': rule.action,
                'priority': rule.priority
            })
        finally:
            session.close()
    
    @app.route('/api/rules/custom', methods=['POST'])
    @require_auth
    def create_custom_rule():
        """创建自定义规则"""
        from models.database import ScoringRule
        
        data = request.json
        session = db.get_session()
        try:
            rule = ScoringRule(
                name=data.get('name'),
                description=data.get('description'),
                enabled=data.get('enabled', True),
                rule_type=data.get('rule_type'),
                conditions=data.get('conditions'),
                score=data.get('score', 0),
                action=data.get('action', 'score'),
                priority=data.get('priority', 100)
            )
            session.add(rule)
            session.commit()
            return jsonify({'success': True, 'id': rule.id})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    @app.route('/api/rules/custom/<int:rule_id>', methods=['PUT'])
    @require_auth
    def update_custom_rule(rule_id):
        """更新自定义规则"""
        from models.database import ScoringRule
        
        data = request.json
        session = db.get_session()
        try:
            rule = session.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            rule.name = data.get('name', rule.name)
            rule.description = data.get('description', rule.description)
            rule.enabled = data.get('enabled', rule.enabled)
            rule.rule_type = data.get('rule_type', rule.rule_type)
            rule.conditions = data.get('conditions', rule.conditions)
            rule.score = data.get('score', rule.score)
            rule.action = data.get('action', rule.action)
            rule.priority = data.get('priority', rule.priority)
            rule.updated_at = datetime.now()
            
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    @app.route('/api/rules/custom/<int:rule_id>', methods=['DELETE'])
    @require_auth
    def delete_custom_rule(rule_id):
        """删除自定义规则"""
        from models.database import ScoringRule
        
        session = db.get_session()
        try:
            rule = session.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            session.delete(rule)
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    @app.route('/api/rules/custom/<int:rule_id>/toggle', methods=['POST'])
    @require_auth
    def toggle_custom_rule(rule_id):
        """切换自定义规则启用状态"""
        from models.database import ScoringRule
        
        data = request.json
        session = db.get_session()
        try:
            rule = session.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
            if not rule:
                return jsonify({'error': '规则不存在'}), 404
            
            rule.enabled = data.get('enabled', not rule.enabled)
            rule.updated_at = datetime.now()
            session.commit()
            return jsonify({'success': True, 'enabled': rule.enabled})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()
    
    # ==================== 防火墙管理 ====================
    
    @app.route('/firewall')
    @require_auth
    def firewall_page():
        """防火墙管理页面"""
        return render_template('firewall.html', username=flask_session.get('username'))
    
    @app.route('/api/firewall/ban', methods=['POST'])
    @require_auth
    def api_ban_ip():
        """手动封禁IP"""
        if not firewall:
            return jsonify({'success': False, 'message': '防火墙未初始化'}), 500
        
        data = request.json
        ip = data.get('ip')
        reason = data.get('reason', 'Manual ban')
        duration = data.get('duration')
        
        success = firewall.ban_ip(ip, reason, duration)
        return jsonify({'success': success, 'message': f'IP {ip} 已封禁' if success else '封禁失败'})
    
    @app.route('/api/firewall/unban', methods=['POST'])
    @require_auth
    def api_unban_ip():
        """手动解封IP"""
        if not firewall:
            return jsonify({'success': False, 'message': '防火墙未初始化'}), 500
        
        data = request.json
        ip = data.get('ip')
        
        success = firewall.unban_ip(ip)
        return jsonify({'success': success, 'message': f'IP {ip} 已解封' if success else '解封失败'})
    
    @app.route('/api/firewall/unban-batch', methods=['POST'])
    @require_auth
    def api_unban_batch():
        """批量解封IP"""
        if not firewall:
            return jsonify({'success': False, 'message': '防火墙未初始化'}), 500
        
        data = request.json
        ips = data.get('ips', [])
        
        count = 0
        for ip in ips:
            if firewall.unban_ip(ip):
                count += 1
        
        return jsonify({'success': True, 'count': count, 'total': len(ips)})
    
    @app.route('/api/firewall/stats')
    @require_auth
    def api_firewall_stats():
        """获取防火墙统计"""
        if not firewall or not hasattr(firewall, 'get_firewall_stats'):
            return jsonify({'total_bans': 0, 'total_packets_blocked': 0, 'total_bytes_blocked': 0})
        
        stats = firewall.get_firewall_stats()
        return jsonify(stats)
    
    @app.route('/api/firewall/chains')
    @require_auth
    def api_firewall_chains():
        """获取iptables链信息"""
        import subprocess
        
        try:
            chains = {}
            for chain_name in ['FIREWALL_BANS', 'FIREWALL_RATE_LIMIT', 'FIREWALL_PORT_RULES']:
                result = subprocess.run(
                    ['iptables', '-L', chain_name, '-n', '-v', '--line-numbers'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    chains[chain_name.lower() + '_chain'] = result.stdout
                else:
                    chains[chain_name.lower() + '_chain'] = f'链 {chain_name} 不存在或无法访问'
            
            return jsonify(chains)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

