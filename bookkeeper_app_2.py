import streamlit as st
from PIL import Image
import json
import io
import base64
import requests
import pandas as pd
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def process_images(image_list, app_password_input, bar):
    app_password = st.secrets["app_password"]
    log_string = ""
    if app_password_input == app_password:
        counter = 1
        with open('output_columns.json') as f:
            output_columns = json.load(f)
        out_df = pd.DataFrame(columns=output_columns)
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
        email = st.secrets["email"]
        email_password = st.secrets["email_password"]

        for image in image_list:
            try:
                bar.progress(counter / len(image_list))
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                }
                payload = {
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """
                        Wie lautet der Unternehmensname, der Gesamtbetrag, der Rechnungstyp und das Datum in der folgenden Rechnung? 
                        Das Datum soll das Format TTMM haben.
                        Der Gesamtbetrag soll ein Komma zur Abtrennung von Euro und Cent haben.
                        Der Rechnungstyp wird durch einen Begriff codiert und bestimmt sich durch folgende Regeln:
                        - Wenn die Rechnung von einer Tankstelle kommt oder Benzin oder Diesel enthält, verwende den Begriff "Tankstelle" als Rechnungstyp.
                        - Wenn der Unternehmensname das Wort 'Floristenbedarf' enthält, verwende den Begriff "Floristenbedarf" als Rechnungstyp.
                        - Verwende in allen anderen Fällen den Begriff "Rest" als Rechnungstyp.
                        Gebe mir die Antwort in folgender Struktur:
                        {
                            "Unternehmensname" : 'String',
                            "Gesamtbetrag" : 'String',
                            "Datum" : 'String',
                            "Rechnungstyp" : 'String'
                        }
                        """
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                        # "url": image_base64
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 300
                }
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                resp = json.loads(response.json()['choices'][0]['message']['content'])
                log_string = log_string + str(response.json()) + "\n\n"

                booking = {
                    "Umsatz (ohne Soll/Haben-Kz)": resp["Gesamtbetrag"],
                    "Soll/Haben-Kennzeichen": "H",
                    "Konto": 1371,
                    "Belegdatum": resp["Datum"],
                    "Belegfeld 1": counter,
                    "Buchungstext": resp["Unternehmensname"],
                    "Festschreibung": 0
                }
                if resp["Rechnungstyp"] == "Tankstelle":
                    booking["BU-Schlüssel"] = 90
                    booking["Gegenkonto (ohne BU-Schlüssel)"] = 4530
                elif resp["Rechnungstyp"] == "Floristenbedarf":
                    booking["BU-Schlüssel"] = 90
                    booking["Gegenkonto (ohne BU-Schlüssel)"] = 4980
                else:
                    booking["Gegenkonto (ohne BU-Schlüssel)"] = 3300


            except Exception as error:
                log_string = log_string + str(error) + "\n\n"
                booking = {
                    "Umsatz (ohne Soll/Haben-Kz)": "1,00",
                    "Soll/Haben-Kennzeichen": "H",
                    "Konto": 1371,
                    "Gegenkonto (ohne BU-Schlüssel)": 3300,
                    "Belegdatum": 101,
                    "Belegfeld 1": counter,
                    "Buchungstext": "???",
                    "Festschreibung": 0
                }
            booking_df = pd.DataFrame(booking, index=[0])
            out_df = pd.concat([out_df, booking_df])
            counter = counter + 1

        subject = "Sending Datev ASCII file"
        body = "Sending Datev ASCII file"
        sender_email = email
        receiver_email = email

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Attach CSV file
        buffer = io.StringIO()
        out_df.to_csv(buffer, encoding='ISO-8859-1', sep=";", index=None)
        buffer.seek(0)
        part = MIMEBase("application", "octet-stream")
        part.set_payload(buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment; filename=Datev_ASCII_file.csv",
        )
        message.attach(part)

        # Attach log file
        log_part = MIMEBase("application", "octet-stream")
        log_part.set_payload(log_string)
        encoders.encode_base64(log_part)
        log_part.add_header(
            "Content-Disposition",
            "attachment; filename=log.txt",
        )
        message.attach(log_part)

        text = message.as_string()
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, email_password)
            server.sendmail(sender_email, receiver_email, text)
        return out_df

    return "wrong password"


st.title("Bookkeeper App 2")
app_password = st.text_input("Enter app password", type="password")
if 'images' not in st.session_state:
    st.session_state['images'] = []

uploaded_file = st.file_uploader("Upload Images", type=['jpg', 'jpeg'], accept_multiple_files=True)
if uploaded_file is not None:
    st.session_state['images'] = [Image.open(img) for img in uploaded_file]
st.number_input("Number images", value=len(st.session_state['images']), disabled=True)

if st.button("Send to OpenAI and email"):
    if app_password:
        bar = st.progress(0)
        output = process_images(st.session_state['images'], app_password, bar)
        st.session_state['images'] = []
        st.write(output)
    else:
        st.warning("Please enter the app password")
