from fastapi_mail import FastMail, MessageSchema
from app.email_config import mail_config


async def send_email_alert(to_email: str, subject: str, message: str):
    fm = FastMail(mail_config)

    msg = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=message,
        subtype="plain"
    )

    await fm.send_message(msg)
    return {"status": "sent"}
