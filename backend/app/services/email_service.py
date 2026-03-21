"""
Email Service

Handles sending emails via SMTP (Gmail or other providers).

Features:
- Password reset emails
- Welcome emails
- Invitation emails

Usage:
    email_service = EmailService()
    await email_service.send_password_reset_email(
        to_email="user@example.com",
        reset_token="abc123"
    )
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from functools import partial

from app.config import get_settings
from app.core.logging import auth_logger


class EmailServiceError(Exception):
    """Base exception for email service errors."""
    pass


class EmailNotConfiguredError(EmailServiceError):
    """Raised when email service is not configured."""
    pass


class EmailSendError(EmailServiceError):
    """Raised when email sending fails."""
    pass


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.settings.smtp_host
            and self.settings.smtp_user
            and self.settings.smtp_password
        )

    def _create_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
    ) -> MIMEMultipart:
        """Create password reset email message."""
        message = MIMEMultipart("alternative")
        message["Subject"] = f"[{self.settings.smtp_from_name}] 비밀번호 재설정"
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        message["To"] = to_email

        # Plain text version
        text_content = f"""
비밀번호 재설정

안녕하세요,

비밀번호 재설정을 요청하셨습니다.
아래 링크를 클릭하여 새 비밀번호를 설정하세요.

{reset_url}

이 링크는 1시간 동안 유효합니다.

본인이 요청하지 않았다면 이 이메일을 무시하셔도 됩니다.

감사합니다.
{self.settings.smtp_from_name}
"""

        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">비밀번호 재설정</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <p>안녕하세요,</p>
        <p>비밀번호 재설정을 요청하셨습니다.<br>아래 버튼을 클릭하여 새 비밀번호를 설정하세요.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">비밀번호 재설정</a>
        </div>
        <p style="font-size: 14px; color: #666;">
            버튼이 작동하지 않으면 아래 링크를 복사하여 브라우저에 붙여넣으세요:<br>
            <a href="{reset_url}" style="color: #667eea; word-break: break-all;">{reset_url}</a>
        </p>
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
        <p style="font-size: 13px; color: #888;">
            이 링크는 1시간 동안 유효합니다.<br>
            본인이 요청하지 않았다면 이 이메일을 무시하셔도 됩니다.
        </p>
    </div>
    <div style="text-align: center; padding: 20px; color: #888; font-size: 12px;">
        <p>&copy; {self.settings.smtp_from_name}</p>
    </div>
</body>
</html>
"""

        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        return message

    def _send_email_sync(self, message: MIMEMultipart) -> None:
        """Send email synchronously (for use in thread pool)."""
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.send_message(message)
        except smtplib.SMTPAuthenticationError as e:
            auth_logger.error(f"SMTP authentication failed: {e}")
            raise EmailSendError("이메일 서버 인증에 실패했습니다.")
        except smtplib.SMTPException as e:
            auth_logger.error(f"SMTP error: {e}")
            raise EmailSendError("이메일 발송에 실패했습니다.")
        except Exception as e:
            auth_logger.error(f"Email send error: {e}")
            raise EmailSendError("이메일 발송 중 오류가 발생했습니다.")

    async def _send_email(self, message: MIMEMultipart) -> None:
        """Send email asynchronously."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, partial(self._send_email_sync, message))

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
    ) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token

        Returns:
            True if email was sent successfully

        Raises:
            EmailNotConfiguredError: If email service is not configured
            EmailSendError: If email sending fails
        """
        if not self.is_configured:
            auth_logger.warning(
                f"Email service not configured. Password reset token for {to_email}: {reset_token}"
            )
            raise EmailNotConfiguredError("이메일 서비스가 설정되지 않았습니다.")

        # Build reset URL
        reset_url = f"{self.settings.frontend_base_url}/reset-password?token={reset_token}"

        # Create and send email
        message = self._create_password_reset_email(to_email, reset_url)

        try:
            await self._send_email(message)
            auth_logger.info(f"Password reset email sent to {to_email}")
            return True
        except EmailSendError:
            raise
        except Exception as e:
            auth_logger.error(f"Failed to send password reset email to {to_email}: {e}")
            raise EmailSendError("이메일 발송에 실패했습니다.")

    async def send_welcome_email(
        self,
        to_email: str,
        full_name: str,
    ) -> bool:
        """
        Send welcome email to new user.

        Args:
            to_email: Recipient email address
            full_name: User's full name

        Returns:
            True if email was sent successfully
        """
        if not self.is_configured:
            auth_logger.warning(f"Email service not configured. Skipping welcome email for {to_email}")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = f"[{self.settings.smtp_from_name}] 가입을 환영합니다!"
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        message["To"] = to_email

        login_url = f"{self.settings.frontend_base_url}/login"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">환영합니다!</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <p>안녕하세요, <strong>{full_name}</strong>님!</p>
        <p>{self.settings.smtp_from_name}에 가입해 주셔서 감사합니다.</p>
        <p>계정이 승인되면 로그인하여 서비스를 이용하실 수 있습니다.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{login_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">로그인하기</a>
        </div>
    </div>
    <div style="text-align: center; padding: 20px; color: #888; font-size: 12px;">
        <p>&copy; {self.settings.smtp_from_name}</p>
    </div>
</body>
</html>
"""

        message.attach(MIMEText(html_content, "html"))

        try:
            await self._send_email(message)
            auth_logger.info(f"Welcome email sent to {to_email}")
            return True
        except Exception as e:
            auth_logger.warning(f"Failed to send welcome email to {to_email}: {e}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get email service singleton instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
