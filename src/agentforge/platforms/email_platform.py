import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.vault import CredentialVault

class EmailPlatform(BasePlatform):
    name = "email"
    description = "Send emails using SMTP server configurations."
    supports_read = False
    supports_write = True
    supports_search = False
    requires_auth = True
    auth_type = "credentials"

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Email platform does not support read operations. Use write/send.")

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Sends an email using SMTP configurations."""
        vault = CredentialVault()
        smtp_host = kwargs.get("smtp_host") or vault.get("email", "smtp_host")
        smtp_port = kwargs.get("smtp_port") or vault.get("email", "smtp_port") or 587
        smtp_user = kwargs.get("smtp_user") or vault.get("email", "smtp_user")
        smtp_pass = kwargs.get("smtp_pass") or vault.get("email", "smtp_pass")
        sender = kwargs.get("sender") or vault.get("email", "sender") or smtp_user
        
        to = kwargs.get("to")
        subject = kwargs.get("subject", "AgentForge Automated Notification")
        cc = kwargs.get("cc")
        is_html = kwargs.get("html", False)

        if not to:
            return {
                "platform": self.name,
                "action": "send",
                "success": False,
                "error": "Recipient email ('to') argument is missing."
            }

        if not smtp_host or not smtp_user or not smtp_pass:
            return {
                "platform": self.name,
                "action": "send",
                "success": False,
                "error": "SMTP server configurations (smtp_host, smtp_user, smtp_pass) are missing. Configure in Vault."
            }

        try:
            # Construct message
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = cc
            
            body_type = "html" if is_html else "plain"
            msg.attach(MIMEText(content, body_type))

            # Connect and send
            port = int(smtp_port)
            server = smtplib.SMTP(smtp_host, port)
            server.ehlo()
            if port == 587:
                server.starttls()
                server.ehlo()
            
            server.login(smtp_user, smtp_pass)
            
            recipients = [to]
            if cc:
                recipients.extend([c.strip() for c in cc.split(",")])
                
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()
            
            return {
                "platform": self.name,
                "action": "send",
                "success": True,
                "notes": f"Email successfully sent to {to}."
            }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "send",
                "success": False,
                "error": str(e)
            }

    def doctor(self) -> Dict[str, Any]:
        vault = CredentialVault()
        smtp_host = vault.get("email", "smtp_host")
        smtp_user = vault.get("email", "smtp_user")
        
        if smtp_host and smtp_user:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": f"SMTP ({smtp_host})",
                "auth": "Configured",
                "notes": f"SMTP host configured for user {smtp_user}."
            }
        else:
            return {
                "platform": self.name,
                "status": "Not Configured",
                "tool": "smtplib",
                "auth": "Missing",
                "notes": "SMTP credentials are missing. Configure using: 'agentforge vault set email smtp_host ...'"
            }
