"""
数据库模型定义
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import json

Base = declarative_base()


class AccessLog(Base):
    """访问日志记录"""
    __tablename__ = 'access_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    ip = Column(String(45), index=True)  # 支持IPv6
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(Text)
    query_params = Column(Text)  # JSON格式
    status_code = Column(Integer, index=True)
    referer = Column(Text)
    response_size = Column(Integer)
    request_time = Column(Float)
    
    # 基础指纹（IP + User-Agent的哈希）
    base_hash = Column(String(64), index=True)
    
    # 行为指纹（包含请求特征的哈希）
    behavior_hash = Column(String(64), index=True)
    
    # 所属身份链ID（如果有）
    identity_chain_id = Column(Integer, ForeignKey('identity_chains.id'), nullable=True, index=True)
    
    # 原始日志行
    raw_log = Column(Text)
    
    __table_args__ = (
        Index('idx_base_behavior', 'base_hash', 'behavior_hash'),
        Index('idx_ip_timestamp', 'ip', 'timestamp'),
    )


class Fingerprint(Base):
    """指纹记录"""
    __tablename__ = 'fingerprints'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    base_hash = Column(String(64), unique=True, index=True)
    ip = Column(String(45), index=True)
    user_agent = Column(Text)
    
    # 首次和最后访问时间
    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 统计信息
    visit_count = Column(Integer, default=1)
    unique_behaviors = Column(Integer, default=1)  # 不同行为指纹数量
    
    # 所属身份链ID（如果已归档到父指纹）
    identity_chain_id = Column(Integer, ForeignKey('identity_chains.id'), nullable=True, index=True)
    
    # 是否为身份链的根节点
    is_identity_root = Column(Boolean, default=False)
    
    # 威胁评分（0-200）
    threat_score = Column(Integer, default=0, index=True)
    
    # 最后评分更新时间（用于分数衰减）
    last_score_update = Column(DateTime, default=datetime.now)
    
    # 额外信息（JSON格式）- 使用extra_data避免与SQLAlchemy的metadata冲突
    extra_data = Column(Text)  # 存储地理位置、设备类型等


class IdentityChain(Base):
    """身份链 - 关联演变的指纹"""
    __tablename__ = 'identity_chains'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 身份链的根哈希（最新的父指纹）
    root_hash = Column(String(64), unique=True, index=True)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 统计信息
    fingerprint_count = Column(Integer, default=0)  # 包含的指纹数量
    total_visits = Column(Integer, default=0)
    
    # 威胁评分
    threat_score = Column(Integer, default=0)
    
    # 关联的所有指纹（关系）
    fingerprints = relationship("Fingerprint", backref="identity_chain", foreign_keys=[Fingerprint.identity_chain_id])
    access_logs = relationship("AccessLog", backref="identity_chain", foreign_keys=[AccessLog.identity_chain_id])
    
    # 身份链历史（JSON格式，记录演变过程）
    evolution_history = Column(Text)  # [{"hash": "xxx", "timestamp": "xxx", "reason": "xxx"}]
    
    # 描述
    description = Column(Text)


class ThreatEvent(Base):
    """威胁事件记录"""
    __tablename__ = 'threat_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    ip = Column(String(45), index=True)
    base_hash = Column(String(64), index=True)
    identity_chain_id = Column(Integer, ForeignKey('identity_chains.id'), nullable=True)
    
    # 威胁类型
    threat_type = Column(String(50), index=True)  # rate_limit, scan, sql_injection, xss, etc.
    severity = Column(String(20))  # low, medium, high, critical
    
    # 详细信息
    description = Column(Text)
    details = Column(Text)  # JSON格式
    
    # 是否已处理
    handled = Column(Boolean, default=False)
    action_taken = Column(String(50))  # banned, alerted, ignored


class BanRecord(Base):
    """封禁记录"""
    __tablename__ = 'ban_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(45), unique=True, index=True)
    
    # 封禁时间
    banned_at = Column(DateTime, default=datetime.now)
    ban_until = Column(DateTime, nullable=True)  # None表示永久封禁
    
    # 封禁原因
    reason = Column(String(200))
    threat_event_id = Column(Integer, ForeignKey('threat_events.id'), nullable=True)
    
    # 是否永久封禁
    is_permanent = Column(Boolean, default=False)
    
    # 是否已解封
    is_active = Column(Boolean, default=True, index=True)
    unbanned_at = Column(DateTime, nullable=True)
    
    # 封禁次数
    ban_count = Column(Integer, default=1)
    
    # 额外信息
    notes = Column(Text)
    
    __table_args__ = (
        Index('idx_active_until', 'is_active', 'ban_until'),
    )


class Whitelist(Base):
    """白名单"""
    __tablename__ = 'whitelist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(45), unique=True, index=True)
    cidr = Column(String(50))  # CIDR格式，如果适用
    description = Column(String(200))
    added_at = Column(DateTime, default=datetime.now)


class Blacklist(Base):
    """黑名单"""
    __tablename__ = 'blacklist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(45), unique=True, index=True)
    cidr = Column(String(50))
    reason = Column(String(200))
    added_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)


class Statistics(Base):
    """统计数据（按小时汇总）"""
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)  # 小时的起始时间
    
    total_requests = Column(Integer, default=0)
    unique_ips = Column(Integer, default=0)
    unique_fingerprints = Column(Integer, default=0)
    
    threats_detected = Column(Integer, default=0)
    ips_banned = Column(Integer, default=0)
    
    # 状态码统计（JSON）
    status_codes = Column(Text)  # {"200": 100, "404": 20, ...}
    
    # 热门路径（JSON）
    top_paths = Column(Text)  # [{"path": "/api/users", "count": 50}, ...]


class ScoreHistory(Base):
    """评分历史记录"""
    __tablename__ = 'score_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    fingerprint_id = Column(Integer, ForeignKey('fingerprints.id'))
    base_hash = Column(String(64), index=True)
    
    # 分数变化
    score_change = Column(Float)  # 正数表示增加，负数表示减少
    total_score = Column(Integer)  # 变化后的总分
    
    # 原因
    reason = Column(String(200))
    threat_event_id = Column(Integer, ForeignKey('threat_events.id'), nullable=True)
    
    # 操作者（system 或 admin）
    operator = Column(String(50), default='system')


class ScoringRule(Base):
    """自定义评分规则"""
    __tablename__ = 'scoring_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 规则名称和描述
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    
    # 规则类型
    rule_type = Column(String(50))  # threat_type, pattern, custom
    
    # 匹配条件（JSON）
    conditions = Column(Text)  # {"threat_type": "sql_injection", "severity": "high"}
    
    # 分数
    score = Column(Integer)
    
    # 是否启用
    enabled = Column(Boolean, default=True)
    
    # 优先级（数字越大优先级越高）
    priority = Column(Integer, default=0)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PortRule(Base):
    """端口规则"""
    __tablename__ = 'port_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 端口信息
    port = Column(Integer, index=True)
    protocol = Column(String(10))  # tcp, udp
    
    # 动作
    action = Column(String(20))  # allow, deny
    
    # 描述
    description = Column(String(200))
    
    # 创建信息
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String(50), default='admin')
    
    # 是否活跃
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_port_protocol', 'port', 'protocol'),
    )


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户名和密码
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(64))
    
    # 2FA/TOTP
    totp_secret = Column(String(32), nullable=True)  # 已启用的密钥
    totp_secret_pending = Column(String(32), nullable=True)  # 待验证的密钥
    totp_enabled_at = Column(DateTime, nullable=True)
    
    # 用户状态
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    require_password_change = Column(Boolean, default=True)
    
    # 登录信息
    last_login = Column(DateTime, nullable=True)
    last_login_attempt = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    
    # 密码修改
    password_changed_at = Column(DateTime, nullable=True)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now)
    
    # API密钥
    api_key = Column(String(64), nullable=True, unique=True)
    api_key_created_at = Column(DateTime, nullable=True)


class Session(Base):
    """会话表"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    session_token = Column(String(64), unique=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    
    # 会话信息
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # 是否活跃
    is_active = Column(Boolean, default=True)


class Database:
    """数据库管理类"""
    
    def __init__(self, config):
        self.config = config
        db_config = config.get('database', {})
        
        if db_config.get('type') == 'sqlite':
            db_path = db_config.get('path', 'firewall.db')
            self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        elif db_config.get('type') == 'mysql':
            conn_str = (f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
                       f"@{db_config['host']}:{db_config['port']}/{db_config['database']}")
            self.engine = create_engine(conn_str, echo=False)
        elif db_config.get('type') == 'postgresql':
            conn_str = (f"postgresql://{db_config['user']}:{db_config['password']}"
                       f"@{db_config['host']}:{db_config['port']}/{db_config['database']}")
            self.engine = create_engine(conn_str, echo=False)
        else:
            raise ValueError(f"Unsupported database type: {db_config.get('type')}")
        
        # 创建所有表
        Base.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def cleanup_old_data(self, retention_days=3):
        """
        清理过期数据（智能清理策略）
        
        策略：
        - 如果某个指纹超过retention_days天没有新访问，删除该指纹的所有记录
        - 如果持续有访问（last_seen不断更新），则持续保存
        
        Args:
            retention_days: 数据保留天数（默认3天）
        
        Returns:
            (deleted_logs, deleted_fps, deleted_chains): 删除的记录数量
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # 1. 找出所有过期的指纹（last_seen超过retention_days天）
            expired_fingerprints = session.query(Fingerprint).filter(
                Fingerprint.last_seen < cutoff_date
            ).all()
            
            deleted_logs = 0
            deleted_chains = 0
            
            # 2. 对每个过期的指纹，删除其所有相关数据
            expired_base_hashes = []
            expired_chain_ids = set()
            
            for fp in expired_fingerprints:
                expired_base_hashes.append(fp.base_hash)
                if fp.identity_chain_id:
                    expired_chain_ids.add(fp.identity_chain_id)
            
            if expired_base_hashes:
                # 删除这些指纹的所有访问日志
                deleted_logs = session.query(AccessLog).filter(
                    AccessLog.base_hash.in_(expired_base_hashes)
                ).delete(synchronize_session=False)
                
                # 删除这些指纹的威胁事件
                session.query(ThreatEvent).filter(
                    ThreatEvent.base_hash.in_(expired_base_hashes)
                ).delete(synchronize_session=False)
            
            # 3. 删除过期的指纹记录
            deleted_fps = session.query(Fingerprint).filter(
                Fingerprint.last_seen < cutoff_date
            ).delete(synchronize_session=False)
            
            # 4. 检查并清理空的身份链（所有指纹都已过期）
            if expired_chain_ids:
                for chain_id in expired_chain_ids:
                    # 检查该身份链是否还有活跃的指纹
                    active_fp_count = session.query(func.count(Fingerprint.id)).filter(
                        Fingerprint.identity_chain_id == chain_id
                    ).scalar()
                    
                    if active_fp_count == 0:
                        # 没有活跃指纹，删除身份链
                        session.query(IdentityChain).filter(
                            IdentityChain.id == chain_id
                        ).delete()
                        deleted_chains += 1
            
            session.commit()
            
            if deleted_logs > 0 or deleted_fps > 0:
                print(f"数据清理完成: 删除 {deleted_logs} 条日志, {deleted_fps} 个指纹, {deleted_chains} 个身份链")
            
            return deleted_logs, deleted_fps, deleted_chains
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

