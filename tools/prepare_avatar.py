"""Rebuild the editable GLB from the recovered local RPM avatar (requires numpy).

The original GLB is never modified. Transfers blink via matching UV topology;
adds geometric customization targets and retains the rig, textures and mouth.
"""
from pathlib import Path
import json
import struct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

class GLB:
    def __init__(self, path):
        raw = Path(path).read_bytes()
        length = struct.unpack_from('<I', raw, 12)[0]
        self.doc = json.loads(raw[20:20+length])
        self.binary = bytearray(raw[28+length:])

    def read(self, index):
        accessor = self.doc['accessors'][index]
        view = self.doc['bufferViews'][accessor['bufferView']]
        dtype = np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[accessor['componentType']])
        width = {'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1,'MAT4':16}[accessor['type']]
        return np.ndarray((accessor['count'],width), dtype=dtype, buffer=self.binary,
            offset=view.get('byteOffset',0)+accessor.get('byteOffset',0),
            strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()

    def add(self, values, kind='VEC3', component=5126):
        values = np.asarray(values,dtype={5126:'<f4',5125:'<u4'}[component])
        while len(self.binary)%4:self.binary.append(0)
        view = len(self.doc['bufferViews'])
        self.doc['bufferViews'].append({'buffer':0,'byteOffset':len(self.binary),'byteLength':values.nbytes})
        self.binary.extend(values.tobytes())
        accessor = {'bufferView':view,'componentType':component,'count':len(values),'type':kind,
            'min':values.min(axis=0).tolist(),'max':values.max(axis=0).tolist()}
        self.doc['accessors'].append(accessor)
        return len(self.doc['accessors'])-1

    def morph(self, mesh, name, delta):
        mesh.setdefault('extras',{}).setdefault('targetNames',[]).append(name)
        mesh.setdefault('weights',[0]*(len(mesh['extras']['targetNames'])-1)).append(0)
        mesh['primitives'][0].setdefault('targets',[]).append({'POSITION':self.add(delta)})

    def save(self,path):
        self.doc['buffers'][0]['byteLength']=len(self.binary)
        payload=json.dumps(self.doc,separators=(',',':')).encode()
        payload+=b' '*((-len(payload))%4)
        self.binary.extend(b'\x00'*((-len(self.binary))%4))
        Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(payload)+len(self.binary))+
            struct.pack('<II',len(payload),0x4e4f534a)+payload+
            struct.pack('<II',len(self.binary),0x004e4942)+self.binary)

def build():
    avatar=GLB(ROOT/'static/models/kaspian-original.glb')
    # The RPM template lives in the local, untracked legacy Unity project.
    template='Asistente virtual/Asistente_Diagnostico/Assets/Samples/Ready Player Me Core/7.4.0/QuickStart/PreviewAvatar/PreviewMesh.glb'
    preview=GLB(next((p for p in (ROOT/'legacy'/template,ROOT/template) if p.is_file()),ROOT/'legacy'/template))
    for mesh in avatar.doc['meshes']:
        primitive=mesh['primitives'][0]
        points=avatar.read(primitive['attributes']['POSITION'])
        name=mesh['name']
        if name=='Wolf3D_Outfit_Top':
            # Hood and drawstrings are separate connected surfaces. Preserve the
            # complete sweatshirt body instead of cutting through its neckline.
            triangles=avatar.read(primitive['indices']).reshape(-1,3)
            _, welded=np.unique(np.round(points,5),axis=0,return_inverse=True)
            parents=list(range(int(welded.max())+1))
            def find(index):
                while parents[index]!=index:
                    parents[index]=parents[parents[index]]
                    index=parents[index]
                return index
            for row in welded[triangles]:
                for index in row[1:]:parents[find(index)]=find(row[0])
            groups={}
            for index,row in enumerate(triangles):groups.setdefault(find(welded[row[0]]),[]).append(index)
            body=max(groups.values(),key=len)
            primitive['indices']=avatar.add(triangles[body].reshape(-1,1),'SCALAR',5125)
            # Close the former hood opening with a collar following its actual edge.
            tri=welded[triangles[body]]
            edges=np.concatenate((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]))
            edges.sort(axis=1)
            edges,counts=np.unique(edges,axis=0,return_counts=True)
            unique=np.unique(np.round(points,5),axis=0)
            rim=unique[np.unique(edges[counts==1])]
            rim=rim[(rim[:,1]>1.45)&(abs(rim[:,0])<.18)]
            rim=rim[np.argsort(np.arctan2(rim[:,0],rim[:,2]+.025))]
            inner=rim.copy();inner[:,0]*=.78;inner[:,2]=(inner[:,2]+.025)*.78-.025;inner[:,1]+=.008
            collar_points=np.concatenate((rim,inner))
            faces=[];count=len(rim)
            for i in range(count):
                n=(i+1)%count;faces.extend(([i,n,i+count],[n,n+count,i+count]))
            faces=np.asarray(faces)
            normals=np.zeros_like(collar_points)
            for face in faces:
                a,b,c=collar_points[face];normal=np.cross(b-a,c-a)
                for index in face:normals[index]+=normal
            normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8)
            collar={'name':'Kaspian_Collar','primitives':[{'attributes':{'POSITION':avatar.add(collar_points),'NORMAL':avatar.add(normals)},'indices':avatar.add(faces.reshape(-1,1),'SCALAR',5125),'material':primitive['material']}]}
        if name in ('EyeLeft','EyeRight','Wolf3D_Head','Wolf3D_Teeth'):
            source=next(m for m in preview.doc['meshes'] if m['name']==name)
            sp=source['primitives'][0]
            uv=avatar.read(primitive['attributes']['TEXCOORD_0'])
            suv=preview.read(sp['attributes']['TEXCOORD_0'])
            # Both models use RPM topology, but exporters can reorder vertices.
            distance=((uv[:,None,:]-suv[None,:,:])**2).sum(axis=2)
            mapping=distance.argmin(axis=1)
            if float(distance.min(axis=1).max())>1e-7:
                raise ValueError(f'Incompatible UV topology: {name}')
            blink_index=source['extras']['targetNames'].index('eyesClosed')
            delta=preview.read(sp['targets'][blink_index]['POSITION'])[mapping]
            avatar.morph(mesh,'eyesClosed',delta)
        if name=='Wolf3D_Head':
            x,y,z=points.T
            # Smooth localized displacement, leaving the rest of the face intact.
            nose=np.exp(-((x/.022)**2+((y-1.696)/.021)**2+((z-.128)/.035)**2))
            delta=np.zeros_like(points);delta[:,1]=nose*.013;delta[:,2]=nose*.007
            avatar.morph(mesh,'noseUpturn',delta)
            delta=np.zeros_like(points);delta[:,0]=x*np.exp(-((y-1.67)/.12)**2)*.14
            avatar.morph(mesh,'faceWidth',delta)
            for side,label in ((1,'Left'),(-1,'Right')):
                weight=np.exp(-(((x-side*.033)/.029)**2+((y-1.756)/.016)**2+((z-.098)/.035)**2))
                delta=np.zeros_like(points);delta[:,1]=weight*.012
                avatar.morph(mesh,'browOuterUp'+label,delta)
        if name=='Wolf3D_Hair':
            # Shorten the side/back silhouette and lift the straight fringe.
            x,y,z=points.T
            delta=np.zeros_like(points)
            low=np.clip((1.795-y)/.13,0,1)
            delta[:,0]=-x*low*.12
            delta[:,1]=low*.025+np.clip((z-.04)/.11,0,1)*np.clip((1.83-y)/.12,0,1)*.012
            delta[:,2]=-np.maximum(z-.09,0)*.26
            avatar.morph(mesh,'taperFade',delta)
            delta=np.zeros_like(points);delta[:,1]=np.clip((y-1.78)/.07,0,1)*.025
            avatar.morph(mesh,'hairLength',delta)
    mesh_index=len(avatar.doc['meshes']);avatar.doc['meshes'].append(collar)
    node_index=len(avatar.doc['nodes']);avatar.doc['nodes'].append({'name':'Kaspian_Collar','mesh':mesh_index})
    avatar.doc['scenes'][avatar.doc.get('scene',0)]['nodes'].append(node_index)
    avatar.doc.setdefault('asset',{})['extras']={'source':'Recovered user avatar 68b4cf67bac430a52cce05e1','customization':'Kaspian local editor'}
    avatar.save(ROOT/'static/models/kaspian.glb')
    print('Prepared local avatar with mouth, smile, blink, brows and customization targets.')

if __name__=='__main__':build()
