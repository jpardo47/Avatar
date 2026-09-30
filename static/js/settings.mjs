export const DEFAULTS=Object.freeze({skin:'#f1cfb5',eyes:'#ad7b42',hair:'#38291f',sweater:'#cbb597',hairstyle:'taper',hairLength:.25,nose:.65,faceWidth:0});
export const STORAGE_KEY='kaspian-avatar-v2';
export function validateSettings(input={}) {
  if(!input||typeof input!=='object'||Array.isArray(input))input={};
  const result={...DEFAULTS};
  for(const key of ['skin','eyes','hair','sweater'])if(typeof input[key]==='string'&&/^#[0-9a-f]{6}$/i.test(input[key]))result[key]=input[key];
  if(['taper','classic','cropped'].includes(input.hairstyle))result.hairstyle=input.hairstyle;
  for(const key of ['hairLength','nose','faceWidth'])if(typeof input[key]==='number'&&Number.isFinite(input[key]))result[key]=Math.max(key==='faceWidth'?-.6:0,Math.min(1,input[key]));
  return result;
}
export function readSettings(){try{return validateSettings(JSON.parse(localStorage.getItem(STORAGE_KEY)||'null'));}catch{return {...DEFAULTS};}}
