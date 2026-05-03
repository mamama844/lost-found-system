import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string


class EmailService:
    def __init__(self):
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.smtp_password = None
        self.sender_email = None
        self.enabled = False
    
    def init_app(self, app):
        self.smtp_server = app.config.get('SMTP_SERVER', 'smtp.qq.com')
        self.smtp_port = app.config.get('SMTP_PORT', 587)
        self.smtp_username = app.config.get('SMTP_USERNAME')
        self.smtp_password = app.config.get('SMTP_PASSWORD')
        self.sender_email = app.config.get('SENDER_EMAIL')
        self.enabled = app.config.get('MAIL_ENABLED', False)
    
    def send_email(self, to_email, subject, body_html, body_text=None):
        if not self.enabled:
            return False, "邮件服务未启用"
        
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.sender_email]):
            return False, "邮件服务配置不完整"
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email
            
            if body_text:
                msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
            
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            return True, "邮件发送成功"
        except Exception as e:
            return False, str(e)
    
    def send_match_notification(self, user_email, username, lost_item, found_item, match_score):
        subject = f"【校园失物招领】找到可能的匹配物品 - {lost_item.title}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: 'Microsoft YaHei', sans-serif; background: #f5f5f5; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; }
                .match-info { background: #f8f9fa; border-radius: 10px; padding: 20px; margin: 20px 0; }
                .score { font-size: 2rem; font-weight: bold; color: #4facfe; }
                .btn { display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 25px; }
                .footer { text-align: center; padding: 20px; color: #999; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 校园失物招领系统</h1>
                    <p>智能匹配通知</p>
                </div>
                <div class="content">
                    <p>亲爱的 {{ username }}，您好！</p>
                    <p>系统为您找到了一个可能匹配的物品，请查看详情：</p>
                    
                    <div class="match-info">
                        <h3>您丢失的物品</h3>
                        <p><strong>名称：</strong>{{ lost_title }}</p>
                        <p><strong>地点：</strong>{{ lost_location }}</p>
                    </div>
                    
                    <div class="match-info">
                        <h3>匹配的拾获物品</h3>
                        <p><strong>名称：</strong>{{ found_title }}</p>
                        <p><strong>地点：</strong>{{ found_location }}</p>
                        <p><strong>匹配度：</strong><span class="score">{{ match_score }}%</span></p>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{{ site_url }}" class="btn">立即查看详情</a>
                    </p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2026 校园失物招领智能匹配系统</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_content = render_template_string(html_template,
            username=username,
            lost_title=lost_item.title,
            lost_location=lost_item.location or '未知',
            found_title=found_item.title,
            found_location=found_item.location or '未知',
            match_score=round(match_score * 100, 1),
            site_url=current_app.config.get('SITE_URL', 'http://localhost:5000')
        )
        
        return self.send_email(user_email, subject, html_content)
    
    def send_status_notification(self, user_email, username, item_title, status):
        status_text = "已找回" if status == "found" else "已归还"
        subject = f"【校园失物招领】物品状态更新 - {item_title}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: 'Microsoft YaHei', sans-serif; background: #f5f5f5; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; }
                .header { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; text-align: center; }
                .status { font-size: 1.5rem; color: #28a745; margin: 20px 0; }
                .footer { text-align: center; padding: 20px; color: #999; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 物品状态更新</h1>
                </div>
                <div class="content">
                    <p>亲爱的 {{ username }}，您好！</p>
                    <p>您发布的物品有了新的状态更新：</p>
                    <p class="status">{{ item_title }} - {{ status_text }}</p>
                    <p>感谢您使用校园失物招领系统！</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2026 校园失物招领智能匹配系统</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_content = render_template_string(html_template,
            username=username,
            item_title=item_title,
            status_text=status_text
        )
        
        return self.send_email(user_email, subject, html_content)


email_service = EmailService()
