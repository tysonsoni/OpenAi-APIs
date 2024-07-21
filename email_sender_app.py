import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(gmail_user, gmail_password):
    try:
        # Set up the server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = gmail_user
        msg['Subject'] = 'Hello from Streamlit!'
        body = 'Hello, World!'
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.sendmail(gmail_user, gmail_user, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False

st.title('Send Email with Gmail')

# Input fields for the user's email and password
gmail_user = st.text_input('Gmail Address')
gmail_password = st.text_input('Gmail Password', type='password')

# Button to send the email
if st.button('Send Email'):
    if gmail_user and gmail_password:
        if send_email(gmail_user, gmail_password):
            st.success('Email sent successfully!')
        else:
            st.error('Failed to send email. Check your credentials and try again.')
    else:
        st.warning('Please enter both your Gmail address and password.')
