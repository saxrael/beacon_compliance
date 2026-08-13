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
