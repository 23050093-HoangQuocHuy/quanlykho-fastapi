import smtplib, ssl

port = 587
smtp_server = "smtp.gmail.com"
sender_email = "huy1995303@gmail.com"
password = "bamclyajqqsujanf"

message = """\
Subject: Test SMTP

This is a direct SMTP test."""

context = ssl.create_default_context()

with smtplib.SMTP(smtp_server, port) as server:
    server.starttls(context=context)
    server.login(sender_email, password)
    server.sendmail(sender_email, "huy1995303@gmail.com", message)

print("SMTP OK — email should be received")
