from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import speech_recognition as sr
import json
import time
from pydantic import BaseModel

id_preguntas = 0
preguntas = [
    "¿Cuales son tus hábitos de consumo de luz? (relacionados a su vida cotidiana/laboral)",
    "¿Cuáles son tus principales preocupaciones con respecto al consumo de energía en tu hogar?",
    "¿Cómo han sido tus experiencias previas con otras eléctricas?",
    "¿Miras tu factura de la luz? ¿Estás familiarizado con los términos, tu compañía, etc.?"
] 
ids = {}

class Item(BaseModel):
    id_pregunta: int

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
links = ["s3://miasistente/pregunta1.mp4",
         "s3://miasistente/pregunta2.mp4",
         "s3://miasistente/pregunta3.mp4",
         "s3://miasistente/pregunta4.mp4"]

initialTalks = "s3://miasistente/initialtalk.mp4"
finalTalks = "s3://miasistente/finaltalk.mp4"

def create_talk(api_key, url_photo,text):
    if text in ids.keys():
        return ids[text]
    
    url = "https://api.d-id.com/talks"
    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "es-CU-ManuelNeural"
            },
            "input": text
        },
        "config": {
            "fluent": "true",
            "pad_audio": "0.0"
        },
        "source_url": url_photo
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {api_key}"
    }

    response = requests.post(url, json=payload, headers=headers).json()

    if "id" not in response.keys():
        print("Error in the request")
        return "Error in the request"
    ids[text] = response["id"]
    return response["id"]

def get_talk(api_key,id):
    import requests

    url = f"https://api.d-id.com/talks/{id}"

    headers = {"accept": "application/json", "authorization": f"Basic {api_key}"}

    response = requests.get(url, headers=headers).json()
    while "result_url" not in response.keys():
        time.sleep(5)
        response = requests.get(url, headers=headers).json()

    with open(f"{id.lower()}.json", "w") as file:
        json.dump(response,file,indent=4)

    return response["result_url"]

@app.get("/speech_to_text")
async def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio_data = r.listen(source)
        try:
            text = r.recognize_google(audio_data, language="es-ES")
            #respuestas.append(text)
            return JSONResponse(content={"text": text})
            #return text
        except sr.UnknownValueError:
            return "Lo siento, no pude entender lo que dijiste."
        except sr.RequestError:
            return "Lo siento, hubo un problema con el servicio de reconocimiento de voz."


@app.post("/generate_talk")
async def generate_talk(item:Item):
    #api_key = "am9zanVsbWFycGVyQGdtYWlsLmNvbQ:mayxCQouZ5S0_o9nLkFqr"
    #url_photo = "https://databuckeet.s3.us-east-1.amazonaws.com/photo_2024-06-18_22-09-24.jpg?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEHsaCXVzLWVhc3QtMSJHMEUCIQCKx%2BZuiLjsBR7X8%2FWlRNNUZnepDaizRojltNCTtFat%2FwIgeXrhDCy2OXVwvkvn2P%2BJdwa4M5jvRuu%2Br2jFPaEp%2Bu0q5AIIIxAAGgw4NTE3MjUxNjg1MzIiDH%2BPP60y7kFAKE7z5CrBAisBjxu3uX9g9uU1bUgkRKwO9Spnvi%2FB22CtCTHDfyt%2B0bPkGXImsjywlxPvihuOVCiLIdbuTU%2F8AIUj2odJdOyX6np1QokCT1PUBWHTP33TwRA%2FlWunZWuFZaLpnVQcKQORwawvbDSNPQvQryoRWrXjSok4jeDQ%2F8ufkjdrh28MnVzJb55a4ws8a%2FsMKWeaKGlTFr4mciDtcu4MFvovrtQIIkPPz3YyJMyB6wH25BAZxVJ150rLz13oWq5MNFd4jji%2FBo7hKG0bcqVrjfYX%2BCPN6UkvGunNQc1opVlcw86r1wig%2BezgLVam5bTZ%2FPxnxpuaCu3NhRTHgUdm0aFKCNTzqrY29UD3pux3vs3GI0%2Bxg%2FomjjbgXlrBhqXE1VL63cRDXPcOs1dFHLgrchgBo5cApRgC2NoF4XKGyAHFMZX8ozDQ%2FMizBjqzAlh3A1F37yzBxGmO%2Bp2PbxQ9lgcG1btjg4i%2Fc2MkdScLOb%2BXr9fR16lvPPdG5dCYxRs67IGQUbrRmtcBy3gHBtaSPiTGTjZgsFo9cbCgKNbM6G2ftZHr4qOnOBB1b1pICwGRF%2BdNTDtr%2Fms%2F7d%2Fyp7Ux7YyAdqAjPxkw8ZcdA6iTzQ%2BjMma6yY7MBcuKLsYywUhUBj2gVyQGt0gEfFUTphReusBSIdfB84fnJ660i5RDKvv%2Fz2kN7rACdJ2Tb2aoTqmSqKGotM2ahgpK8gTWldAtUhboFQCPO2lH79l615fApPoLm6MKpTOsJxeXjU5NfouFCb4yNwCJcZB52N0cIXnqOV%2BzDOaHEXrq2PoWNXGOLgD67uIuEMbHPEhAqwd38WTsubBqgP4h2PmlpUqvr6k8vWk%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240619T023902Z&X-Amz-SignedHeaders=host&X-Amz-Expires=43200&X-Amz-Credential=ASIA4MTWGV6KC74ONFMP%2F20240619%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=8502e15a8b7e24c83efbbbc262c53940788d9469294f6a220264bbb14cf3c4f2"
    id_pregunta = item.id_pregunta
    #text = preguntas[id_pregunta]
    #print(text)
    #id = create_talk(api_key, url_photo, text)
    #time.sleep(5)
    #video_url = get_talk(api_key,id)
    video_url = links[id_pregunta]
    #print(video_url)
    return JSONResponse(content={"video_url": video_url})

@app.get("/final_talk")
async def final():
    #api_key = "am9zanVsbWFycGVyQGdtYWlsLmNvbQ:mayxCQouZ5S0_o9nLkFqr"
    #url_photo = "https://databuckeet.s3.us-east-1.amazonaws.com/photo_2024-06-18_22-09-24.jpg?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEHsaCXVzLWVhc3QtMSJHMEUCIQCKx%2BZuiLjsBR7X8%2FWlRNNUZnepDaizRojltNCTtFat%2FwIgeXrhDCy2OXVwvkvn2P%2BJdwa4M5jvRuu%2Br2jFPaEp%2Bu0q5AIIIxAAGgw4NTE3MjUxNjg1MzIiDH%2BPP60y7kFAKE7z5CrBAisBjxu3uX9g9uU1bUgkRKwO9Spnvi%2FB22CtCTHDfyt%2B0bPkGXImsjywlxPvihuOVCiLIdbuTU%2F8AIUj2odJdOyX6np1QokCT1PUBWHTP33TwRA%2FlWunZWuFZaLpnVQcKQORwawvbDSNPQvQryoRWrXjSok4jeDQ%2F8ufkjdrh28MnVzJb55a4ws8a%2FsMKWeaKGlTFr4mciDtcu4MFvovrtQIIkPPz3YyJMyB6wH25BAZxVJ150rLz13oWq5MNFd4jji%2FBo7hKG0bcqVrjfYX%2BCPN6UkvGunNQc1opVlcw86r1wig%2BezgLVam5bTZ%2FPxnxpuaCu3NhRTHgUdm0aFKCNTzqrY29UD3pux3vs3GI0%2Bxg%2FomjjbgXlrBhqXE1VL63cRDXPcOs1dFHLgrchgBo5cApRgC2NoF4XKGyAHFMZX8ozDQ%2FMizBjqzAlh3A1F37yzBxGmO%2Bp2PbxQ9lgcG1btjg4i%2Fc2MkdScLOb%2BXr9fR16lvPPdG5dCYxRs67IGQUbrRmtcBy3gHBtaSPiTGTjZgsFo9cbCgKNbM6G2ftZHr4qOnOBB1b1pICwGRF%2BdNTDtr%2Fms%2F7d%2Fyp7Ux7YyAdqAjPxkw8ZcdA6iTzQ%2BjMma6yY7MBcuKLsYywUhUBj2gVyQGt0gEfFUTphReusBSIdfB84fnJ660i5RDKvv%2Fz2kN7rACdJ2Tb2aoTqmSqKGotM2ahgpK8gTWldAtUhboFQCPO2lH79l615fApPoLm6MKpTOsJxeXjU5NfouFCb4yNwCJcZB52N0cIXnqOV%2BzDOaHEXrq2PoWNXGOLgD67uIuEMbHPEhAqwd38WTsubBqgP4h2PmlpUqvr6k8vWk%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240619T023902Z&X-Amz-SignedHeaders=host&X-Amz-Expires=43200&X-Amz-Credential=ASIA4MTWGV6KC74ONFMP%2F20240619%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=8502e15a8b7e24c83efbbbc262c53940788d9469294f6a220264bbb14cf3c4f2"
    ## Saludo inicial o mensaje del chatbot
    #text = "Gracias por comunicarte con nosotros, un gusto poder atenderle"
    #id = create_talk(api_key, url_photo, text)
    #time.sleep(5)
    #video_url = get_talk(api_key,id)
    video_url = finalTalks
    #print(video_url)
    #video_url = "https://d-id-talks-prod.s3.us-west-2.amazonaws.com/google-oauth2%7C102022364966578092329/tlk_oN8msyaMh51AWYI46JsAT/1718668468514.mp4?AWSAccessKeyId=AKIA5CUMPJBIK65W6FGA&Expires=1718754872&Signature=d85zMB1veC9YhL%2BAuY3Ab7%2BQ200%3D"
    return JSONResponse(content={"video_url": video_url})


@app.get("/initial-greeting")
async def initial_greeting():
    #api_key = "am9zanVsbWFycGVyQGdtYWlsLmNvbQ:mayxCQouZ5S0_o9nLkFqr"
    #url_photo = "https://databuckeet.s3.us-east-1.amazonaws.com/photo_2024-06-18_22-09-24.jpg?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEHsaCXVzLWVhc3QtMSJHMEUCIQCKx%2BZuiLjsBR7X8%2FWlRNNUZnepDaizRojltNCTtFat%2FwIgeXrhDCy2OXVwvkvn2P%2BJdwa4M5jvRuu%2Br2jFPaEp%2Bu0q5AIIIxAAGgw4NTE3MjUxNjg1MzIiDH%2BPP60y7kFAKE7z5CrBAisBjxu3uX9g9uU1bUgkRKwO9Spnvi%2FB22CtCTHDfyt%2B0bPkGXImsjywlxPvihuOVCiLIdbuTU%2F8AIUj2odJdOyX6np1QokCT1PUBWHTP33TwRA%2FlWunZWuFZaLpnVQcKQORwawvbDSNPQvQryoRWrXjSok4jeDQ%2F8ufkjdrh28MnVzJb55a4ws8a%2FsMKWeaKGlTFr4mciDtcu4MFvovrtQIIkPPz3YyJMyB6wH25BAZxVJ150rLz13oWq5MNFd4jji%2FBo7hKG0bcqVrjfYX%2BCPN6UkvGunNQc1opVlcw86r1wig%2BezgLVam5bTZ%2FPxnxpuaCu3NhRTHgUdm0aFKCNTzqrY29UD3pux3vs3GI0%2Bxg%2FomjjbgXlrBhqXE1VL63cRDXPcOs1dFHLgrchgBo5cApRgC2NoF4XKGyAHFMZX8ozDQ%2FMizBjqzAlh3A1F37yzBxGmO%2Bp2PbxQ9lgcG1btjg4i%2Fc2MkdScLOb%2BXr9fR16lvPPdG5dCYxRs67IGQUbrRmtcBy3gHBtaSPiTGTjZgsFo9cbCgKNbM6G2ftZHr4qOnOBB1b1pICwGRF%2BdNTDtr%2Fms%2F7d%2Fyp7Ux7YyAdqAjPxkw8ZcdA6iTzQ%2BjMma6yY7MBcuKLsYywUhUBj2gVyQGt0gEfFUTphReusBSIdfB84fnJ660i5RDKvv%2Fz2kN7rACdJ2Tb2aoTqmSqKGotM2ahgpK8gTWldAtUhboFQCPO2lH79l615fApPoLm6MKpTOsJxeXjU5NfouFCb4yNwCJcZB52N0cIXnqOV%2BzDOaHEXrq2PoWNXGOLgD67uIuEMbHPEhAqwd38WTsubBqgP4h2PmlpUqvr6k8vWk%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240619T023902Z&X-Amz-SignedHeaders=host&X-Amz-Expires=43200&X-Amz-Credential=ASIA4MTWGV6KC74ONFMP%2F20240619%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=8502e15a8b7e24c83efbbbc262c53940788d9469294f6a220264bbb14cf3c4f2"
    # Saludo inicial o mensaje del chatbot
    #text = "Hola soy tu asistente personal en que puedo ayudarte?"
    #id = create_talk(api_key, url_photo, text)
    #time.sleep(5)
    #video_url = get_talk(api_key,id)
    video_url = initialTalks
    #print(video_url)
    #video_url = "https://d-id-talks-prod.s3.us-west-2.amazonaws.com/google-oauth2%7C102022364966578092329/tlk_oN8msyaMh51AWYI46JsAT/1718668468514.mp4?AWSAccessKeyId=AKIA5CUMPJBIK65W6FGA&Expires=1718754872&Signature=d85zMB1veC9YhL%2BAuY3Ab7%2BQ200%3D"
    return JSONResponse(content={"video_url": video_url})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request
    })

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
