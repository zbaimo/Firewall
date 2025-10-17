"""
用户认证管理器
提供用户登录、密码管理、2FA等功能
"""
import hashlib
import secrets
import pyotp
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta


class AuthManager:
    """认证管理器"""
    
    def __init__(self, db, config: Dict):
        self.db = db
        self.config = config
        self.auth_config = config.get('authentication', {})
        
        # 确保默认管理员账户存在
        self._ensure_default_admin()
        
        print("✓ 认证系统已初始化")
    
    def _ensure_default_admin(self):
        """确保默认管理员账户存在"""
        from models.database import User
        
        session = self.db.get_session()
        try:
            # 检查是否有admin用户
            admin = session.query(User).filter(User.username == 'admin').first()
            
            if not admin:
                # 创建默认admin账户
                default_password = 'admin'
                admin = User(
                    username='admin',
                    password_hash=self.hash_password(default_password),
                    is_active=True,
                    is_admin=True,
                    require_password_change=True,  # 强制首次修改密码
                    created_at=datetime.now()
                )
                session.add(admin)
                session.commit()
                print("⚠️  已创建默认管理员账户: admin/admin （首次登录需要修改密码）")
        except Exception as e:
            session.rollback()
            print(f"创建默认管理员失败: {e}")
        finally:
            session.close()
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        # 使用SHA256 + 盐值
        salt = self.auth_config.get('password_salt', 'firewall-salt-2025')
        combined = f"{password}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        验证密码
        
        Returns:
            (is_valid, user_info)
        """
        from models.database import User
        
        session = self.db.get_session()
        try:
            user = session.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if not user:
                return False, None
            
            # 验证密码
            password_hash = self.hash_password(password)
            if user.password_hash != password_hash:
                # 记录失败尝试
                user.failed_login_attempts += 1
                user.last_login_attempt = datetime.now()
                session.commit()
                return False, None
            
            # 检查是否需要2FA
            if user.totp_secret and not user.require_password_change:
                # 需要2FA验证
                return True, {
                    'user_id': user.id,
                    'username': user.username,
                    'require_2fa': True,
                    'require_password_change': user.require_password_change,
                    'is_admin': user.is_admin
                }
            
            # 更新登录信息
            user.last_login = datetime.now()
            user.failed_login_attempts = 0
            session.commit()
            
            return True, {
                'user_id': user.id,
                'username': user.username,
                'require_2fa': False,
                'require_password_change': user.require_password_change,
                'is_admin': user.is_admin
            }
            
        finally:
            session.close()
    
    def verify_totp(self, username: str, token: str) -> bool:
        """验证TOTP令牌"""
        from models.database import User
        
        session = self.db.get_session()
        try:
            user = session.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if not user or not user.totp_secret:
                return False
            
            # 验证TOTP
            totp = pyotp.TOTP(user.totp_secret)
            is_valid = totp.verify(token, valid_window=1)
            
            if is_valid:
                # 更新登录信息
                user.last_login = datetime.now()
                user.failed_login_attempts = 0
                session.commit()
            
            return is_valid
            
        finally:
            session.close()
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        修改密码
        
        Returns:
            (success, message)
        """
        from models.database import User
        
        # 验证旧密码
        is_valid, _ = self.verify_password(username, old_password)
        if not is_valid:
            return False, "旧密码错误"
        
        # 密码强度检查
        if len(new_password) < 8:
            return False, "密码长度至少8位"
        
        session = self.db.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            
            if not user:
                return False, "用户不存在"
            
            # 更新密码
            user.password_hash = self.hash_password(new_password)
            user.require_password_change = False
            user.password_changed_at = datetime.now()
            
            session.commit()
            
            return True, "密码修改成功"
            
        except Exception as e:
            session.rollback()
            return False, f"修改失败: {str(e)}"
        finally:
            session.close()
    
    def generate_totp_secret(self, username: str) -> Tuple[str, str]:
        """
        生成TOTP密钥
        
        Returns:
            (secret, qr_code_url)
        """
        from models.database import User
        
        # 生成密钥
        secret = pyotp.random_base32()
        
        # 生成QR码URL
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(
            name=username,
            issuer_name='Nginx Firewall'
        )
        
        # 保存到数据库（但不启用，需要验证后启用）
        session = self.db.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if user:
                user.totp_secret_pending = secret
                session.commit()
        finally:
            session.close()
        
        return secret, qr_uri
    
    def enable_totp(self, username: str, token: str) -> Tuple[bool, str]:
        """
        启用TOTP（需要验证令牌）
        
        Returns:
            (success, message)
        """
        from models.database import User
        
        session = self.db.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            
            if not user or not user.totp_secret_pending:
                return False, "没有待启用的密钥"
            
            # 验证令牌
            totp = pyotp.TOTP(user.totp_secret_pending)
            if not totp.verify(token, valid_window=1):
                return False, "验证码错误"
            
            # 启用TOTP
            user.totp_secret = user.totp_secret_pending
            user.totp_secret_pending = None
            user.totp_enabled_at = datetime.now()
            
            session.commit()
            
            return True, "双因素认证已启用"
            
        except Exception as e:
            session.rollback()
            return False, f"启用失败: {str(e)}"
        finally:
            session.close()
    
    def disable_totp(self, username: str, password: str) -> Tuple[bool, str]:
        """
        禁用TOTP（需要密码验证）
        
        Returns:
            (success, message)
        """
        # 验证密码
        is_valid, _ = self.verify_password(username, password)
        if not is_valid:
            return False, "密码错误"
        
        from models.database import User
        
        session = self.db.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            
            if not user:
                return False, "用户不存在"
            
            user.totp_secret = None
            user.totp_secret_pending = None
            
            session.commit()
            
            return True, "双因素认证已禁用"
            
        except Exception as e:
            session.rollback()
            return False, f"禁用失败: {str(e)}"
        finally:
            session.close()
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> Tuple[bool, str]:
        """
        创建用户
        
        Returns:
            (success, message)
        """
        from models.database import User
        
        if len(username) < 3:
            return False, "用户名至少3个字符"
        
        if len(password) < 8:
            return False, "密码至少8个字符"
        
        session = self.db.get_session()
        try:
            # 检查用户名是否已存在
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                return False, "用户名已存在"
            
            # 创建用户
            user = User(
                username=username,
                password_hash=self.hash_password(password),
                is_active=True,
                is_admin=is_admin,
                require_password_change=True
            )
            
            session.add(user)
            session.commit()
            
            return True, "用户创建成功"
            
        except Exception as e:
            session.rollback()
            return False, f"创建失败: {str(e)}"
        finally:
            session.close()
    
    def generate_session_token(self) -> str:
        """生成会话令牌"""
        return secrets.token_urlsafe(32)

