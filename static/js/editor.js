import {DEFAULTS,STORAGE_KEY,readSettings,validateSettings} from './settings.mjs?v=2';

const palettes={
  skin:[['Clara','#f1cfb5'],['Porcelana','#f7dfcc'],['Media','#d7a07c'],['Morena','#a86c48'],['Oscura','#704832']],
  eyes:[['Café claro','#ad7b42'],['Avellana','#8b7042'],['Café oscuro','#493125'],['Verde','#597453'],['Azul','#547e99']],
  hair:[['Castaño oscuro','#38291f'],['Negro','#161515'],['Castaño','#72503a'],['Rubio','#b3925b'],['Gris','#9b9790']],
  sweater:[['Beige','#cbb597'],['Crema','#e4d9c5'],['Verde salvia','#798b74'],['Azul marino','#35485d'],['Terracota','#ad725b'],['Negro','#292b2e']]
};

export function setupEditor(avatar){
  const $=id=>document.getElementById(id);let settings=readSettings();
  const message=text=>{$('editor-status').textContent=text;};
  function sync(){
    document.querySelectorAll('[data-setting]').forEach(input=>{input.value=settings[input.dataset.setting];});
    document.querySelectorAll('[data-color]').forEach(button=>button.setAttribute('aria-pressed',String(settings[button.dataset.kind].toLowerCase()===button.dataset.color)));
    document.querySelectorAll('[data-hairstyle]').forEach(button=>button.setAttribute('aria-pressed',String(settings.hairstyle===button.dataset.hairstyle)));
    for(const key of ['nose','faceWidth','hairLength'])$(key+'-value').value=Math.round(settings[key]*100)+'%';
    $('hairLength').disabled=settings.hairstyle==='cropped';
    document.documentElement.style.setProperty('--sweater',settings.sweater);
  }
  function apply(){
    settings=validateSettings(settings);avatar.applySettings(settings);sync();
    try{localStorage.setItem(STORAGE_KEY,JSON.stringify(settings));message('Guardado en este navegador.');}
    catch{message('Cambios aplicados. El navegador no permite guardarlos; puedes exportarlos.');}
  }
  for(const[kind,colors]of Object.entries(palettes)){
    const container=document.querySelector(`[data-palette="${kind}"]`);
    for(const[name,color]of colors){
      const button=document.createElement('button');button.className='swatch';button.style.setProperty('--swatch',color);button.dataset.color=color;button.dataset.kind=kind;button.setAttribute('aria-label',`${kind==='skin'?'Piel':kind==='eyes'?'Ojos':kind==='hair'?'Cabello':'Suéter'}: ${name}`);button.title=name;
      button.onclick=()=>{settings[kind]=color;apply();};container.append(button);
    }
  }
  document.querySelectorAll('[data-setting]').forEach(input=>input.addEventListener('input',()=>{settings[input.dataset.setting]=input.type==='range'?Number(input.value):input.value;apply();}));
  document.querySelectorAll('[data-hairstyle]').forEach(button=>button.onclick=()=>{settings.hairstyle=button.dataset.hairstyle;apply();});
  const tabs=[...document.querySelectorAll('[data-tab]')];
  function setFrame(view){avatar.frame(view);document.querySelectorAll('[data-view]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.view===view)));}
  function selectTab(button){
    tabs.forEach(tab=>{const active=tab===button;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;$('panel-'+tab.dataset.tab).hidden=!active;});
    setFrame(button.dataset.tab==='outfit'?'portrait':'face');
  }
  tabs.forEach((button,index)=>{
    button.onclick=()=>selectTab(button);
    button.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(index+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;selectTab(tabs[next]);tabs[next].focus();};
  });
  function openEditor(open){
    $('customizer').hidden=!open;document.querySelector('.conversation').hidden=open;$('edit-avatar').setAttribute('aria-expanded',String(open));
    if(open){selectTab(tabs[0]);$('close-editor').focus();}else{setFrame('portrait');$('edit-avatar').focus();}
  }
  $('edit-avatar').onclick=()=>openEditor($('customizer').hidden);
  $('close-editor').onclick=()=>openEditor(false);
  $('customizer').addEventListener('keydown',event=>{if(event.key==='Escape')openEditor(false);});
  document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>setFrame(button.dataset.view));
  $('reset-avatar').onclick=()=>{settings={...DEFAULTS};apply();message('Apariencia solicitada restablecida.');};
  $('export-avatar').onclick=()=>{
    const blob=new Blob([JSON.stringify({format:'kaspian-avatar',version:2,settings},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='kaspian-apariencia.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('Ajustes exportados. El archivo no incluye el modelo 3D.');
  };
  $('import-avatar').onchange=async event=>{
    const file=event.target.files[0];if(!file)return;
    try{
      if(file.size>10000)throw new Error();const data=JSON.parse(await file.text());
      if(data.format!=='kaspian-avatar'||data.version!==2||!data.settings||typeof data.settings!=='object'||Array.isArray(data.settings))throw new Error();
      settings=validateSettings(data.settings);apply();message('Ajustes importados y aplicados.');
    }catch{message('Archivo no válido. Importa un JSON exportado por este editor.');}finally{event.target.value='';}
  };
  sync();avatar.applySettings(settings);$('edit-avatar').disabled=false;
}
