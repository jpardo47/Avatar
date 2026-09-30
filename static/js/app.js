const $=id=>document.getElementById(id);
let avatar=null, busy=false, listening=false, recognizer=null, speechId=0, utterance=null, resetTimer;
const status=text=>{$('status').textContent=text;};
const state=(name,emotion)=>{clearTimeout(resetTimer);avatar?.setState(name,emotion);};

// Chat remains usable even if the device cannot initialize WebGL.
import('./avatar-view.js').then(({Avatar})=>{
  try{avatar=new Avatar($('avatar'),$('avatar-status'));import('./editor.js').then(({setupEditor})=>setupEditor(avatar)).catch(error=>{console.error('Editor failed',error);$('notice').textContent='No se pudo abrir el editor de apariencia. Recarga la página.';});}
  catch{$('avatar-status').textContent='El dispositivo no pudo iniciar la vista 3D.';}
}).catch(error=>{console.error('Viewer failed',error);$('avatar-status').textContent='No se pudo cargar el visor 3D. Recarga la página.';});

function controls(){
  $('send').disabled=busy||listening;
  $('mic').disabled=busy||!recognizer;
  $('demo').disabled=busy||listening;
  document.querySelectorAll('[data-question]').forEach(b=>b.disabled=busy||listening);
}
function addMessage(text,who='bot'){
  const entry=document.createElement('article');entry.className=`message ${who}`;
  const label=document.createElement('span');label.textContent=who==='user'?'Tú':'Kaspian';
  const content=document.createElement('p');content.textContent=text;
  entry.append(label,content);$('chat').append(entry);$('chat').scrollTop=$('chat').scrollHeight;
  return entry;
}
// Visual-only "typing" bubble; the status line already announces the wait to screen readers.
function addTyping(){
  const entry=addMessage('','bot');entry.classList.add('typing');entry.setAttribute('aria-hidden','true');
  entry.querySelector('p').append(...Array.from({length:3},()=>document.createElement('i')));
  return entry;
}
function stopSpeech(){
  speechId++;window.speechSynthesis?.cancel();utterance=null;
  if(avatar)avatar.speaking=false;
  if(!busy&&!listening){state('idle');status('Listo para conversar');}
}
function speak(text,emotion='explaining'){
  stopSpeech();state('responding',emotion);
  if(!$('voice-enabled').checked||!('speechSynthesis' in window)){
    if(!('speechSynthesis' in window))$('notice').textContent='Este navegador no tiene síntesis de voz; puedes leer las respuestas.';
    resetTimer=setTimeout(()=>{if(!busy&&!listening)state('idle');},4000);return;
  }
  const synth=window.speechSynthesis, id=++speechId;
  const u=new SpeechSynthesisUtterance(text.replace(/[*#_]/g,''));utterance=u;
  const voices=synth.getVoices();u.voice=voices.find(v=>v.lang==='es-CO')||voices.find(v=>v.lang.startsWith('es'))||null;
  u.lang=u.voice?.lang||'es-ES';u.rate=.96;
  let watchdog=setTimeout(()=>{
    if(id!==speechId)return;
    stopSpeech();$('notice').textContent='La voz no inició. Pulsa «Probar voz y expresiones» o revisa las voces del navegador.';
  },10000);
  u.onstart=()=>{clearTimeout(watchdog);if(id!==speechId)return;if(avatar)avatar.speaking=true;state('speaking',emotion);status('Kaspian está hablando…');};
  const finish=()=>{clearTimeout(watchdog);if(id!==speechId)return;if(avatar)avatar.speaking=false;utterance=null;state('idle');status('Listo para conversar');};
  u.onend=finish;
  u.onerror=event=>{finish();if(id===speechId&&!['interrupted','canceled'].includes(event.error))$('notice').textContent='No se pudo reproducir la voz. Comprueba las voces instaladas y el permiso de audio del navegador.';};
  try{synth.speak(u);}catch{finish();$('notice').textContent='La voz no está disponible en este navegador.';}
}
async function sendMessage(message){
  message=message.trim();if(!message||busy||listening)return;
  stopSpeech();busy=true;controls();state('thinking');status('Kaspian está pensando…');
  addMessage(message,'user');$('message').value='';
  const typing=addTyping();
  const controller=new AbortController(), timeout=setTimeout(()=>controller.abort(),45000);
  try{
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message}),signal:controller.signal});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'No se pudo obtener la respuesta.');
    typing.remove();addMessage(data.response);busy=false;status('Respuesta recibida');speak(data.response,data.expression);
  }catch(error){
    typing.remove();busy=false;state('idle','concerned');status('No se pudo completar la consulta');
    addMessage(error.name==='AbortError'?'La respuesta tardó demasiado. Inténtalo de nuevo.':error.message);
  }finally{typing.remove();clearTimeout(timeout);busy=false;controls();$('message').focus();}
}
$('chat-form').addEventListener('submit',event=>{event.preventDefault();sendMessage($('message').value);});
document.querySelectorAll('[data-question]').forEach(button=>button.onclick=()=>sendMessage(button.dataset.question));
$('stop').onclick=()=>{stopSpeech();if(listening)recognizer?.abort();};
$('voice-enabled').onchange=()=>{if(!$('voice-enabled').checked)stopSpeech();};
$('demo').onclick=()=>{
  $('voice-enabled').checked=true;
  speak('¡Hola! Soy Kaspian. Me alegra conocerte. Observa mis ojos, mis cejas y mi boca mientras hablamos de ingeniería biomédica.','happy');
};
$('zoom-in').onclick=()=>avatar?.zoom(-.25);$('zoom-out').onclick=()=>avatar?.zoom(.25);

const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(Recognition){
  recognizer=new Recognition();recognizer.lang='es-CO';recognizer.interimResults=false;recognizer.maxAlternatives=1;
  let transcript='', micError=false;
  recognizer.onstart=()=>{listening=true;micError=false;controls();state('listening');status('Te escucho…');$('mic-label').textContent='Terminar escucha';$('mic').setAttribute('aria-pressed','true');};
  recognizer.onresult=event=>{transcript=event.results[0][0].transcript;};
  recognizer.onerror=event=>{micError=true;status(event.error==='not-allowed'?'Permite el micrófono en el navegador para hablar.':'No se pudo reconocer la voz. Puedes escribir tu pregunta.');};
  recognizer.onend=()=>{
    listening=false;controls();$('mic-label').textContent='Usar micrófono';$('mic').setAttribute('aria-pressed','false');state('idle');
    const message=transcript;transcript='';if(message)sendMessage(message);else if(!micError)status('No se detectó una pregunta. Inténtalo de nuevo.');
  };
  $('mic').onclick=()=>{
    if(listening){recognizer.stop();return;}
    stopSpeech();transcript='';
    try{listening=true;controls();recognizer.start();}catch{listening=false;controls();status('No se pudo iniciar el micrófono.');}
  };
}else{$('notice').textContent='El reconocimiento de voz no está disponible en este navegador. Puedes escribir tus preguntas.';}
controls();
const health=(mode,text)=>{$('health').dataset.mode=mode;$('health-text').textContent=text;};
fetch('/health').then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{
  health(data.mode==='demo'?'demo':'online',data.mode==='demo'?'Modo demostración':'Conectado');
  if(data.mode==='demo')$('notice').textContent=($('notice').textContent+' Respuestas locales de demostración. Configura la IA en .env para consultas abiertas.').trim();
}).catch(()=>health('offline','Sin conexión'));
window.addEventListener('pagehide',()=>{stopSpeech();recognizer?.abort();});
