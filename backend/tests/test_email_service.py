from unittest.mock import MagicMock, patch

from backend.src.core.email_service import send_email


def test_send_email_smtp_success(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "testuser")
    monkeypatch.setenv("SMTP_PASSWORD", "testpass")
    monkeypatch.setenv("NOTIFICATION_FROM_EMAIL", "test@pottershouse.org.uk")

    with patch("smtplib.SMTP") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = instance

        res = send_email(
            to_email="trustee@pottershouse.org.uk",
            subject="Test Subject",
            body_html="<p>Test Body</p>",
        )

        assert res["success"] is True
        assert res["provider"] == "smtp"
        instance.starttls.assert_called_once()
        instance.login.assert_called_once_with("testuser", "testpass")
        instance.sendmail.assert_called_once()


def test_send_email_no_smtp_host_configured(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)

    res = send_email(
        to_email="trustee@pottershouse.org.uk",
        subject="Test",
        body_html="<p>Test</p>",
    )

    assert res["success"] is False
    assert "No SMTP_HOST configured" in res["error"]


def test_send_email_port_465_ssl(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.ssl.test.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USERNAME", "ssluser")
    monkeypatch.setenv("SMTP_PASSWORD", "sslpass")

    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl:
        instance = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = instance

        res = send_email(
            to_email="trustee@pottershouse.org.uk",
            subject="SSL Test",
            body_html="<p>SSL Body</p>",
            body_text="Plain text SSL body",
        )

        assert res["success"] is True
        assert res["provider"] == "smtp"
        instance.login.assert_called_once_with("ssluser", "sslpass")
        instance.sendmail.assert_called_once()


def test_send_email_smtp_exception_handling(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fail.test.com")

    with patch("smtplib.SMTP", side_effect=RuntimeError("SMTP connection refused")):
        res = send_email(
            to_email="trustee@pottershouse.org.uk",
            subject="Fail Test",
            body_html="<p>Fail</p>",
        )

        assert res["success"] is False
        assert res["provider"] == "smtp"
        assert "SMTP connection refused" in res["error"]


def test_send_email_plain_text_attachment_and_no_tls(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.notls.com")
    monkeypatch.setenv("SMTP_PORT", "25")
    monkeypatch.setenv("SMTP_USE_TLS", "false")
    monkeypatch.delenv("SMTP_USERNAME", raising=False)

    with patch("smtplib.SMTP") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = instance

        res = send_email(
            to_email="trustee@pottershouse.org.uk",
            subject="No TLS Test",
            body_html="<p>HTML Body</p>",
            body_text="Plain text body attachment",
        )

        assert res["success"] is True
        instance.starttls.assert_not_called()
        instance.login.assert_not_called()
        instance.sendmail.assert_called_once()
