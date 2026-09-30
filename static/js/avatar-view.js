import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {readSettings,validateSettings} from './settings.mjs?v=2';

export class Avatar {
  constructor(canvas,label){
    this.label=label;this.canvas=canvas;this.settings=readSettings();this.state='idle';this.emotion='happy';this.speaking=false;
    this.level=0;this.nextBlink=2;this.blinkAt=-10;this.meshes=[];this.materials={};this.baseBones=[];this.yaw=0;this.targetYaw=0;
    this.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.scene=new THREE.Scene();this.camera=new THREE.PerspectiveCamera(30,1,.01,100);
    this.camera.position.set(0,1.6,1.85);this.camera.lookAt(0,1.51,0);
    this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
    this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));this.renderer.outputColorSpace=THREE.SRGBColorSpace;
    this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.12;
    this.scene.add(new THREE.HemisphereLight(0xffffff,0x697b80,2));
    const key=new THREE.DirectionalLight(0xffefe4,2.6);key.position.set(-2,3,4);this.scene.add(key);
    const fill=new THREE.DirectionalLight(0xe7f0ff,1.25);fill.position.set(3,2,2);this.scene.add(fill);
    const rim=new THREE.DirectionalLight(0xffe2be,1.8);rim.position.set(1,3,-2);this.scene.add(rim);
    this.root=new THREE.Group();this.scene.add(this.root);
    this.observer=new ResizeObserver(()=>{const{width,height}=canvas.getBoundingClientRect();if(!width||!height)return;this.renderer.setSize(width,height,false);this.camera.aspect=width/height;this.camera.updateProjectionMatrix();});this.observer.observe(canvas);
    let pointer=null;
    canvas.addEventListener('pointerdown',e=>{pointer={id:e.pointerId,x:e.clientX,yaw:this.targetYaw};canvas.setPointerCapture(e.pointerId);});
    canvas.addEventListener('pointermove',e=>{if(pointer&&pointer.id===e.pointerId)this.targetYaw=pointer.yaw+(e.clientX-pointer.x)*.009;});
    const release=()=>{pointer=null;};canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);canvas.addEventListener('lostpointercapture',release);
    canvas.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){this.targetYaw+=e.key==='ArrowLeft'?-.15:.15;e.preventDefault();}});
    this.clock=new THREE.Clock();this.renderer.setAnimationLoop(()=>this.update());
    this.ready=this.load();
  }
  customizeMaterial(material,kind){
    const color={value:new THREE.Color(this.settings[kind])};
    material=material.clone();material.roughness=kind==='eyes'?.3:kind==='sweater'?.94:.72;material.metalness=0;
    if(kind==='sweater')material.map=null;
    const skinColor={value:new THREE.Color(this.settings.skin)},fade={value:1};
    material.onBeforeCompile=shader=>{
      shader.uniforms.avatarColor=color;shader.uniforms.skinColor=skinColor;shader.uniforms.fadeAmount=fade;
      shader.vertexShader='varying vec3 avatarPosition;\n'+shader.vertexShader;
      shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\navatarPosition = position;');
      shader.fragmentShader='uniform vec3 avatarColor; uniform vec3 skinColor; uniform float fadeAmount; varying vec3 avatarPosition;\n'+shader.fragmentShader;
      const chunks={
        skin:`float lum=dot(diffuseColor.rgb,vec3(.299,.587,.114)); diffuseColor.rgb=mix(diffuseColor.rgb,avatarColor*clamp(lum/.38,.18,1.4),.82);`,
        // Iris is a ring centred in the eye texture (pupil r<.05, sclera r>.2); the sclera is pinkish, so mask by UV radius, not colour.
        eyes:`float lum=dot(diffuseColor.rgb,vec3(.299,.587,.114)); float r=length(vMapUv-.5); float iris=smoothstep(.05,.075,r)*(1.-smoothstep(.17,.195,r))*(1.-smoothstep(.12,.22,lum)); diffuseColor.rgb=mix(diffuseColor.rgb,avatarColor*clamp(lum/.14,.3,1.5),iris);`,
        hair:`float lum=dot(diffuseColor.rgb,vec3(.299,.587,.114)); float strands=.94+.06*sin(avatarPosition.x*2200.+avatarPosition.z*300.); diffuseColor.rgb=avatarColor*clamp(lum/.12,.32,1.5)*strands; float fade=(1.-smoothstep(1.69,1.795,avatarPosition.y))*fadeAmount; diffuseColor.rgb=mix(diffuseColor.rgb,skinColor*.55,fade*.85);`,
        sweater:`float knit=sin(avatarPosition.x*1400.)*sin(avatarPosition.y*1700.); diffuseColor.rgb=avatarColor*(.97+.03*knit);`
      };
      shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\n'+chunks[kind]);
    };
    material.customProgramCacheKey=()=>`kaspian-${kind}-v2`;
    (this.materials[kind]??=[]).push({material,color,skinColor,fade});return material;
  }
  async load(){
    try{
      const gltf=await new GLTFLoader().loadAsync('/static/models/kaspian.glb?v=4');
      this.model=gltf.scene;this.root.add(this.model);
      this.model.traverse(object=>{
        if(object.isMesh){
          object.frustumCulled=false;
          if(object.morphTargetDictionary)this.meshes.push(object);
          const names={Wolf3D_Head:'skin',Wolf3D_Body:'skin',EyeLeft:'eyes',EyeRight:'eyes',Wolf3D_Hair:'hair',Wolf3D_Outfit_Top:'sweater',Kaspian_Collar:'sweater'};
          if(names[object.name])object.material=this.customizeMaterial(object.material,names[object.name]);
          if(object.name==='Kaspian_Collar')object.material.side=THREE.DoubleSide;
        }
        if(object.isBone&&['Head','Neck','LeftArm','RightArm'].includes(object.name))this.baseBones.push({bone:object,quaternion:object.quaternion.clone()});
      });
      this.model.updateMatrixWorld(true);
      for(const pose of this.baseBones){
        if(!['LeftArm','RightArm'].includes(pose.bone.name))continue;
        const parent=pose.bone.parent.getWorldQuaternion(new THREE.Quaternion());
        const rotation=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),pose.bone.name==='LeftArm'?-.32:.32);
        pose.quaternion.premultiply(parent.clone().invert().multiply(rotation).multiply(parent));
      }
      this.applySettings(this.settings);this.label.textContent='Kaspian · Avatar original recuperado';this.canvas.dataset.ready='true';
    }catch(error){this.label.textContent='No se pudo cargar el avatar. Recarga la página.';this.canvas.dataset.ready='error';console.error('Avatar load failed',error);}
  }
  applySettings(value){
    this.settings=validateSettings(value);
    for(const[kind,entries]of Object.entries(this.materials))for(const entry of entries){entry.color.value.set(this.settings[kind]);entry.skinColor.value.set(this.settings.skin);entry.fade.value=this.settings.hairstyle==='classic'?0:1;}
  }
  setState(state,emotion='explaining'){this.state=state;this.emotion=emotion;this.label.textContent=({idle:'Listo para conversar',thinking:'Pensando…',listening:'Te escucho',speaking:'Hablando…',responding:'Respondiendo'})[state]||'Listo';}
  frame(view){this.targetYaw=0;if(view==='full'){this.camera.position.set(0,1.05,3.9);this.camera.lookAt(0,.95,0);}else{this.camera.position.set(0,1.65,view==='face'?.85:1.85);this.camera.lookAt(0,view==='face'?1.71:1.51,0);}}
  zoom(amount){this.camera.position.z=THREE.MathUtils.clamp(this.camera.position.z+amount,.65,4.5);}
  update(){
    const dt=Math.min(this.clock.getDelta(),.05),t=this.clock.elapsedTime;
    if(t>this.nextBlink){this.blinkAt=t;this.nextBlink=t+2.5+Math.random()*3;}
    const blink=Math.max(0,1-Math.abs(t-this.blinkAt-.085)/.085);
    this.level=THREE.MathUtils.damp(this.level,this.speaking?.14+.74*Math.abs(Math.sin(t*15))*Math.abs(Math.sin(t*8.3)):0,22,dt);
    this.yaw=THREE.MathUtils.damp(this.yaw,this.targetYaw,12,dt);this.root.rotation.y=this.yaw+(this.reduced?0:Math.sin(t*.65)*.018);
    const happy=this.emotion==='happy'?.6:this.state==='idle'?.12:.18;
    const targets={mouthOpen:this.level,mouthSmile:happy,eyesClosed:blink,
      browOuterUpLeft:this.state==='thinking'?.65:this.state==='listening'?.4:.1,
      browOuterUpRight:this.state==='listening'?.4:this.emotion==='concerned'?.35:.08,
      noseUpturn:this.settings.nose,faceWidth:this.settings.faceWidth,
      taperFade:this.settings.hairstyle==='classic'?0:1,hairLength:this.settings.hairstyle==='cropped'?0:this.settings.hairLength};
    for(const mesh of this.meshes)for(const[name,index]of Object.entries(mesh.morphTargetDictionary))mesh.morphTargetInfluences[index]=THREE.MathUtils.damp(mesh.morphTargetInfluences[index],targets[name]??0,20,dt);
    for(const{bone,quaternion}of this.baseBones){bone.quaternion.copy(quaternion);if(bone.name==='Head'&&!this.reduced){bone.rotateX(Math.sin(t*(this.speaking?3:1))*(this.speaking?.018:.007));bone.rotateZ(this.state==='thinking'?.045:0);}}
    this.canvas.dataset.speaking=String(this.speaking);this.renderer.render(this.scene,this.camera);
  }
}
