"""
SendGrid email service with templates and delivery tracking
"""

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

logger = logging.getLogger(__name__)

class SendGridService:
    # Email templates (SendGrid template IDs)
    TEMPLATES = {
        'welcome': 'd-abc123def456',
        'verify_email': 'd-xyz789uvw012',
        'password_reset': 'd-ghi345jkl678',
        'payment_confirmation': 'd-mno901pqr234',
        'payment_receipt': 'd-stu567vwx890',
        'ban_notice': 'd-yza234bcd567',
        'support_response': 'd-efg890hij123',
    }

    def __init__(self, api_key: str):
        self.sg = sendgrid.SendGridAPIClient(api_key)
        self.from_email = Email("noreply@cgraph.org", "CGRAPH")

    async def send_transactional_email(
        self,
        to_email: str,
        template_id: str,
        dynamic_template_data: dict = None
    ) -> bool:
        """
        Send templated email via SendGrid
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email)
            )
            message.template_id = template_id
            message.dynamic_template_data = dynamic_template_data or {}

            # Add tracking
            message.tracking_settings.click_tracking.enable = True
            message.tracking_settings.open_tracking.enable = True

            # Send
            response = self.sg.send(message)

            logger.info(
                f"Email sent to {to_email} using template {template_id}",
                extra={"status_code": response.status_code}
            )

            return response.status_code == 202

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    async def send_welcome_email(self, email: str, name: str, verification_link: str) -> bool:
        """Send welcome email to new user"""
        return await self.send_transactional_email(
            to_email=email,
            template_id=self.TEMPLATES['welcome'],
            dynamic_template_data={
                'name': name,
                'verification_link': verification_link,
                'year': datetime.now().year
            }
        )

    async def send_password_reset_email(self, email: str, reset_link: str) -> bool:
        """Send password reset email"""
        return await self.send_transactional_email(
            to_email=email,
            template_id=self.TEMPLATES['password_reset'],
            dynamic_template_data={
                'reset_link': reset_link,
                'expiry_hours': 24
            }
        )

    async def send_payment_receipt(
        self,
        email: str,
        receipt_data: dict
    ) -> bool:
        """Send payment receipt"""
        return await self.send_transactional_email(
            to_email=email,
            template_id=self.TEMPLATES['payment_receipt'],
            dynamic_template_data=receipt_data
        )
