"""
实时告警通知管理器
支持邮件、Webhook、Telegram等多种告警方式
"""
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime, timedelta
import json


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.alert_config = config.get('alerts', {})
        self.enabled = self.alert_config.get('enabled', False)
        
        if self.enabled:
            print("✓ 告警系统已启用")
        else:
            print("ℹ 告警系统未启用")
        
        # 告警阈值
        self.alert_on_events = set(self.alert_config.get('alert_on_events', [
            'sql_injection', 'xss_attack', 'rate_limit_exceeded', 'path_scan'
        ]))
        
        # 防止告警风暴
        self._alert_history = {}  # {ip: last_alert_time}
        self.min_alert_interval = self.alert_config.get('min_alert_interval_seconds', 300)  # 5分钟
    
    def should_alert(self, ip: str, threat_type: str, severity: str) -> bool:
        """判断是否应该发送告警"""
        if not self.enabled:
            return False
        
        # 检查威胁类型
        if threat_type not in self.alert_on_events and severity not in ['critical', 'high']:
            return False
        
        # 防止告警风暴
        last_alert = self._alert_history.get(ip)
        if last_alert:
            elapsed = (datetime.now() - last_alert).total_seconds()
            if elapsed < self.min_alert_interval:
                return False
        
        return True
    
    def send_threat_alert(self, ip: str, threat_type: str, severity: str, 
                         description: str, details: Dict = None):
        """
        发送威胁告警
        
        Args:
            ip: IP地址
            threat_type: 威胁类型
            severity: 严重程度
            description: 描述
            details: 详细信息
        """
        if not self.should_alert(ip, threat_type, severity):
            return
        
        # 记录告警时间
        self._alert_history[ip] = datetime.now()
        
        # 构建告警消息
        message = self._build_alert_message(ip, threat_type, severity, description, details)
        
        # 发送邮件
        if self.alert_config.get('email', {}).get('enabled'):
            self._send_email_alert(message)
        
        # 发送Webhook
        if self.alert_config.get('webhook', {}).get('enabled'):
            self._send_webhook_alert(message)
        
        # 发送Telegram
        if self.alert_config.get('telegram', {}).get('enabled'):
            self._send_telegram_alert(message)
    
    def send_ban_alert(self, ip: str, reason: str, duration: int = None):
        """发送封禁告警"""
        if not self.enabled:
            return
        
        message = {
            'type': 'ban',
            'ip': ip,
            'reason': reason,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        # 只发送Webhook和Telegram（邮件不发封禁通知，太频繁）
        if self.alert_config.get('webhook', {}).get('enabled'):
            self._send_webhook_alert(message)
        
        if self.alert_config.get('telegram', {}).get('enabled'):
            text = f"🚫 IP封禁\n\nIP: {ip}\n原因: {reason}\n时长: {duration}秒" if duration else "永久"
            self._send_telegram_message(text)
    
    def send_system_alert(self, message: str, level: str = 'warning'):
        """发送系统告警"""
        if not self.enabled:
            return
        
        alert = {
            'type': 'system',
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # 发送到所有渠道
        if level in ['error', 'critical']:
            if self.alert_config.get('email', {}).get('enabled'):
                self._send_email_alert(alert)
        
        if self.alert_config.get('webhook', {}).get('enabled'):
            self._send_webhook_alert(alert)
    
    def _build_alert_message(self, ip: str, threat_type: str, severity: str,
                            description: str, details: Dict = None) -> Dict:
        """构建告警消息"""
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        return {
            'type': 'threat',
            'ip': ip,
            'threat_type': threat_type,
            'severity': severity,
            'severity_emoji': severity_emoji.get(severity, '⚪'),
            'description': description,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_email_alert(self, alert: Dict):
        """发送邮件告警"""
        email_config = self.alert_config.get('email', {})
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 防火墙告警 - {alert.get('severity', 'ALERT').upper()}"
            msg['From'] = email_config.get('from_addr')
            msg['To'] = ', '.join(email_config.get('to_addrs', []))
            
            # 纯文本版本
            text_content = self._format_email_text(alert)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML版本
            html_content = self._format_email_html(alert)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
            
            print(f"✓ 邮件告警已发送: {alert.get('ip')}")
            
        except Exception as e:
            print(f"✗ 邮件告警发送失败: {e}")
    
    def _format_email_text(self, alert: Dict) -> str:
        """格式化邮件文本内容"""
        if alert['type'] == 'threat':
            return f"""
防火墙威胁告警

时间: {alert['timestamp']}
严重程度: {alert['severity'].upper()}
IP地址: {alert['ip']}
威胁类型: {alert['threat_type']}
描述: {alert['description']}

详细信息:
{json.dumps(alert.get('details', {}), indent=2, ensure_ascii=False)}

---
此邮件由防火墙系统自动发送
            """.strip()
        elif alert['type'] == 'system':
            return f"""
系统告警

时间: {alert['timestamp']}
级别: {alert['level'].upper()}
消息: {alert['message']}

---
此邮件由防火墙系统自动发送
            """.strip()
        else:
            return json.dumps(alert, indent=2, ensure_ascii=False)
    
    def _format_email_html(self, alert: Dict) -> str:
        """格式化邮件HTML内容"""
        severity_colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#f59e0b',
            'low': '#10b981'
        }
        
        if alert['type'] == 'threat':
            color = severity_colors.get(alert['severity'], '#6b7280')
            
            return f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background: {color}; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; background: #f9fafb; border-radius: 5px; margin-top: 10px; }}
        .field {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #374151; }}
        .value {{ color: #111827; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{alert['severity_emoji']} 防火墙威胁告警</h2>
    </div>
    <div class="content">
        <div class="field">
            <span class="label">时间:</span> 
            <span class="value">{alert['timestamp']}</span>
        </div>
        <div class="field">
            <span class="label">严重程度:</span> 
            <span class="value" style="color: {color};">{alert['severity'].upper()}</span>
        </div>
        <div class="field">
            <span class="label">IP地址:</span> 
            <span class="value">{alert['ip']}</span>
        </div>
        <div class="field">
            <span class="label">威胁类型:</span> 
            <span class="value">{alert['threat_type']}</span>
        </div>
        <div class="field">
            <span class="label">描述:</span> 
            <span class="value">{alert['description']}</span>
        </div>
    </div>
    <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
        此邮件由防火墙系统自动发送
    </p>
</body>
</html>
            """.strip()
        else:
            return f"<pre>{json.dumps(alert, indent=2, ensure_ascii=False)}</pre>"
    
    def _send_webhook_alert(self, alert: Dict):
        """发送Webhook告警（企业微信、钉钉、Slack等）"""
        webhook_config = self.alert_config.get('webhook', {})
        url = webhook_config.get('url')
        
        if not url:
            return
        
        try:
            # 格式化消息（适配企业微信/钉钉）
            if alert['type'] == 'threat':
                text = f"{alert['severity_emoji']} 威胁告警\n\n" \
                       f"IP: {alert['ip']}\n" \
                       f"类型: {alert['threat_type']}\n" \
                       f"严重程度: {alert['severity']}\n" \
                       f"描述: {alert['description']}\n" \
                       f"时间: {alert['timestamp']}"
            else:
                text = f"系统告警: {alert.get('message', str(alert))}"
            
            # 企业微信格式
            payload = {
                "msgtype": "text",
                "text": {
                    "content": text
                }
            }
            
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"✓ Webhook告警已发送: {alert.get('ip', 'system')}")
            else:
                print(f"✗ Webhook告警发送失败: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Webhook告警发送失败: {e}")
    
    def _send_telegram_alert(self, alert: Dict):
        """发送Telegram告警"""
        telegram_config = self.alert_config.get('telegram', {})
        bot_token = telegram_config.get('bot_token')
        chat_id = telegram_config.get('chat_id')
        
        if not bot_token or not chat_id:
            return
        
        try:
            if alert['type'] == 'threat':
                text = f"{alert['severity_emoji']} *威胁告警*\n\n" \
                       f"IP: `{alert['ip']}`\n" \
                       f"类型: {alert['threat_type']}\n" \
                       f"严重程度: *{alert['severity']}*\n" \
                       f"描述: {alert['description']}\n" \
                       f"时间: {alert['timestamp']}"
            else:
                text = f"🔔 系统告警\n\n{alert.get('message', str(alert))}"
            
            self._send_telegram_message(text)
            
        except Exception as e:
            print(f"✗ Telegram告警发送失败: {e}")
    
    def _send_telegram_message(self, text: str):
        """发送Telegram消息"""
        telegram_config = self.alert_config.get('telegram', {})
        bot_token = telegram_config.get('bot_token')
        chat_id = telegram_config.get('chat_id')
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("✓ Telegram告警已发送")
        else:
            print(f"✗ Telegram告警发送失败: {response.status_code}")
    
    def test_alerts(self):
        """测试所有告警渠道"""
        print("\n测试告警系统...")
        print("=" * 60)
        
        test_alert = {
            'type': 'threat',
            'ip': '192.168.1.100',
            'threat_type': 'test',
            'severity': 'medium',
            'severity_emoji': '🟡',
            'description': '这是一条测试告警',
            'details': {'test': True},
            'timestamp': datetime.now().isoformat()
        }
        
        if self.alert_config.get('email', {}).get('enabled'):
            print("\n[1] 测试邮件告警...")
            self._send_email_alert(test_alert)
        
        if self.alert_config.get('webhook', {}).get('enabled'):
            print("\n[2] 测试Webhook告警...")
            self._send_webhook_alert(test_alert)
        
        if self.alert_config.get('telegram', {}).get('enabled'):
            print("\n[3] 测试Telegram告警...")
            self._send_telegram_alert(test_alert)
        
        print("\n" + "=" * 60)
        print("告警测试完成")

