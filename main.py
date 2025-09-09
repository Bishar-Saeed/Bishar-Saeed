

import smtplib
sender_email = input("Enter sender email: ")
receiver_email = input("Enter receiver email: ")

subject = input("Enter subject: ")
message = input("Enter message: ")
text = f"Subject: {subject}\n\n{message}"

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls() 
    app_password = input("Enter your app password: ")  
    server.login(sender_email, app_password)
    server.sendmail(sender_email, receiver_email, text)
    print(f"Email  sent to {receiver_email}")
except Exception as e:
    print(f"Failed to send email: {e}")

finally:
    server.quit()
