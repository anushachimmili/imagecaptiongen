
import os
import smtplib
import secrets
from PIL import Image
from flask import url_for, current_app
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def send_reset_email(user):
    token = user.get_reset_token()
    message = MIMEMultipart()
    message['From'] = current_app.config['MAIL_USERNAME']
    message['To'] = user.email
    message['Subject'] = 'Password Reset Request'
    mail_content = f'''To reset your password, visit the following link:
    {url_for('users.reset_token', token=token, _external=True)}

    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    message.attach(MIMEText(mail_content, 'plain'))
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
    
    session.sendmail(from_addr=current_app.config['MAIL_USERNAME'], 
                        to_addrs=user.email, msg=message.as_string())
