import os
import unicodedata
import requests

class ProviderError(Exception):
    pass

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

def expression(text):
    text = normalize(text)
    if any(word in text for word in ('hola', 'gusto', 'alegra', 'excelente')):
        return 'happy'
    if any(word in text for word in ('no dispongo', 'no puedo', 'lo siento')):
        return 'concerned'
    return 'explaining'

def answer(message):
    key, model = os.getenv('OPENROUTER_API_KEY'), os.getenv('CHAT_MODEL')
    if key and model:
        try:
            result = requests.post('https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {key}'},
                json={'model': model, 'max_tokens': 450, 'messages': [
                    {'role': 'system', 'content': 'Eres Kaspian, asistente educativo de ingeniería biomédica. Responde en español, breve y amable. No inventes información específica de la UAN; remite a sus canales oficiales para matrículas, precios y fechas. No diagnostiques ni prescribas.'},
                    {'role': 'user', 'content': message}]}, timeout=35)
            result.raise_for_status()
            response = result.json()['choices'][0]['message']['content']
            if not isinstance(response, str) or not response.strip():
                raise ValueError('Respuesta vacía')
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError() from exc
        return {'response': response, 'expression': expression(response), 'mode': 'online'}
    text = normalize(message)
    if any(word in text for word in ('hola', 'buenos dias', 'buenas tardes')):
        response = '¡Hola! Soy Kaspian. Puedes preguntarme qué es la ingeniería biomédica, sobre equipos médicos o las áreas de trabajo. Estoy en modo demostración con respuestas locales.'
    elif any(word in text for word in ('gracias', 'genial', 'excelente')):
        response = '¡Con mucho gusto! Me alegra acompañarte a explorar la ingeniería biomédica.'
    elif any(word in text for word in ('uan', 'matricula', 'precio', 'inscripcion', 'semestre')):
        response = 'Para conocer el plan de estudios, costos y fechas de la UAN, consulta sus canales oficiales. En modo demostración no dispongo de información institucional actualizada.'
    elif any(word in text for word in ('equipo', 'dispositivo', 'tecnologia')):
        response = 'La ingeniería biomédica trabaja con tecnologías para la salud, como monitores de signos vitales, prótesis y equipos de imagen. Combina diseño, mantenimiento y evaluación de dispositivos médicos.'
    elif any(word in text for word in ('trabajo', 'campo', 'laboral')):
        response = 'Algunas áreas de trabajo son la ingeniería clínica en hospitales, el desarrollo de dispositivos médicos, la rehabilitación y la investigación. Cada área combina conocimientos de ingeniería y salud.'
    elif any(word in text for word in ('biomedica', 'carrera', 'estudia')):
        response = 'La ingeniería biomédica aplica la ingeniería a problemas de biología y salud. Integra electrónica, programación, mecánica y ciencias biológicas para desarrollar y gestionar tecnologías médicas.'
    else:
        response = 'Estoy en modo demostración. Puedo explicar qué es la ingeniería biomédica, sus áreas de trabajo y los equipos médicos. Para preguntas abiertas, configura el servicio de inteligencia artificial siguiendo el README.'
    return {'response': response, 'expression': expression(response), 'mode': 'demo'}
