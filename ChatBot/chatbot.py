import gradio as gr
import openai
import os
import subprocess

openai.api_key = input('Type in your OpenAI password and press enter.')


messages = [{"role": "system", "content": 'You are a therapist. Respond to all input in 25 words or less.'}]

def transcribe(audio):
    global messages

    os.rename(audio, audio + '.wav')
    audio_file = open(audio + '.wav', "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    messages.append({"role": "user", "content": transcript["text"]})
    print(transcript["text"])

    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    system_message = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": system_message})
    print(system_message)
    subprocess.call(
        'PowerShell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{}\')"'.format(
            system_message), shell=True)

    chat_transcript = ""
    for message in messages:
        if message['role'] != 'system':
            chat_transcript += message['role'] + ": " + message['content'] + "\n\n"

    return chat_transcript

ui = gr.Interface(fn=transcribe, inputs=gr.Audio(source="microphone", type="filepath"), outputs="text").launch()
ui.launch()