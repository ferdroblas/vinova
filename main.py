from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai
import json
import random

# Configuración de API Keys
openai.api_key = "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"
GOOGLE_API_KEY = "AIzaSyBcd4h5sJQasrU_Mlr0ZI9LY4jprCwaS9o"
SEARCH_ENGINE_ID = "108981853455873244007"

# Inicializar FastAPI
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Modelo para recibir consultas
class UserInput(BaseModel):
    query: str
    history: list = []  # Historial de mensajes

def generar_cierre():
    """
    Genera una respuesta de cierre amigable usando GPT o un valor por defecto.
    """
    cierre_prompt = """
    Genera 5 respuestas amigables y cortas para cerrar una conversación en tono argentino, invitando a seguir preguntando. 
    Por ejemplo: "Si querés saber más o tenés alguna otra pregunta, no dudes en preguntar. ¡Estoy acá para ayudarte! 😊"

    Responde en formato JSON, como:
    {
        "cierres": [
            "respuesta 1",
            "respuesta 2",
            "respuesta 3",
            "respuesta 4",
            "respuesta 5"
        ]
    }
    """
    try:
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sos un asistente que genera frases de cierre amigables en tono argentino."},
                {"role": "user", "content": cierre_prompt}
            ],
            temperature=0.7,
            max_tokens=200,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        response_content = gpt_response["choices"][0]["message"]["content"]
        cierres = json.loads(response_content)["cierres"]
        return random.choice(cierres)
    except Exception as e:
        print(f"Error al generar respuestas de cierre: {str(e)}")
        # Si falla GPT, usar un cierre predeterminado
        return "Si querés saber más o tenés alguna otra pregunta, no dudes en preguntar. ¡Estoy acá para ayudarte! 😊"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Renderiza la página principal con el chatbot.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat/")
async def chat(input: UserInput):
    """
    Procesa la consulta del usuario y genera una respuesta manteniendo el historial.
    """
    try:
        # Construir mensajes para GPT a partir del historial
        messages = [{"role": "system", "content": "Sos un sommelier virtual especializado en vinos y maridajes. Usá un tono amable y argentino en las respuestas."}]
        for msg in input.history:
            messages.append(msg)
        messages.append({"role": "user", "content": input.query})

        # Llamada a GPT para obtener la respuesta
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        # Extraer respuesta
        reply = gpt_response["choices"][0]["message"]["content"]
        if "vino" in input.query.lower():
                reply += "\n\n🍷 **Notas de cata**:\n👀 Vista: Color brillante y profundo.\n👃 Nariz: Aromas frutales intensos.\n👅 Boca: Suave y elegante."
        elif "plato" in input.query.lower():
            reply += "\n\n🍽️ **Ingredientes principales**:\n🥩 Carne, 🥔 Papas, 🌶️ Especias."

        # Generar cierre dinámico
        cierre = generar_cierre()
        reply += f"\n\n{cierre}"

        # Agregar la respuesta al historial
        input.history.append({"role": "user", "content": input.query})
        input.history.append({"role": "assistant", "content": reply})

        return {"reply": reply, "history": input.history}

    except Exception as e:
        print(f"Error interno: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
