# /backend/app/services/email_service.py
"""
Email delivery service with templating and retry logic
"""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import logging
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class EmailService:
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        
        # Template loader
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates/emails')
        )
    
    async def send_email(
        self,
        to: str,
        subject: str,
        template: str,
        context: dict,
        reply_to: str = None,
        cc: list = None,
        bcc: list = None,
        max_retries: int = 3
    ) -> bool:
        """
        Send email with retry logic
        """
        
        for attempt in range(max_retries):
            try:
                # Render template
                template_obj = self.jinja_env.get_template(f"{template}.html")
                html_content = template_obj.render(**context)
                
                # Create message
                message = MIMEMultipart('alternative')
                message['Subject'] = subject
                message['From'] = self.from_email
                message['To'] = to
                
                if reply_to:
                    message['Reply-To'] = reply_to
                
                if cc:
                    message['Cc'] = ', '.join(cc)
                
                # Attach HTML part
                html_part = MIMEText(html_content, 'html')
                message.attach(html_part)
                
                # Send via SMTP
                async with aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    use_tls=True
                ) as smtp:
                    await smtp.login(self.smtp_user, self.smtp_password)
                    
                    recipients = [to]
                    if cc:
                        recipients.extend(cc)
                    if bcc:
                        recipients.extend(bcc)
                    
                    await smtp.sendmail(
                        self.from_email,
                        recipients,
                        message.as_string()
                    )
                
                logger.info(f"Email sent to {to} (subject: {subject})")
                return True
            
            except Exception as e:
                logger.warning(f"Email send failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Email delivery failed after {max_retries} attempts")
                    
                    # Log failure for manual intervention
                    await self._log_email_failure(to, subject, str(e))
                    return False
        
        return False
    
    async def _log_email_failure(self, to: str, subject: str, error: str):
        """Log failed emails for investigation"""
        
        failure = EmailFailure(
            recipient=to,
            subject=subject,
            error=error,
            timestamp=datetime.utcnow()
        )
        
        db.add(failure)
        await db.commit()
        
        # Alert admin
        await self.send_email(
            to=settings.ADMIN_EMAIL,
            subject=f"⚠️ Email delivery failed: {subject}",
            template="admin_alert_email_failure",
            context={
                "recipient": to,
                "subject": subject,
                "error": error
            }
        )

# Email templates
