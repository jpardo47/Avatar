"""Validate the generated rig and actual morph data without launching a renderer."""
import json
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]

class AvatarAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw=(ROOT/'static/models/kaspian.glb').read_bytes()
        length=struct.unpack_from('<I',raw,12)[0]
        cls.document=json.loads(raw[20:20+length])
        cls.binary=raw[28+length:]

    def test_face_controls_have_matching_vertex_counts(self):
        doc=self.document
        head=next(m for m in doc['meshes'] if m['name']=='Wolf3D_Head')
        expected={'mouthOpen','mouthSmile','eyesClosed','noseUpturn','faceWidth','browOuterUpLeft','browOuterUpRight'}
        self.assertTrue(expected.issubset(head['extras']['targetNames']))
        for mesh in doc['meshes']:
            for primitive in mesh['primitives']:
                count=doc['accessors'][primitive['attributes']['POSITION']]['count']
                for morph in primitive.get('targets',[]):
                    self.assertEqual(doc['accessors'][morph['POSITION']]['count'],count)
            if 'weights' in mesh:self.assertEqual(len(mesh['weights']),len(mesh['extras']['targetNames']))

    def test_blink_has_real_displacement(self):
        doc=self.document;head=next(m for m in doc['meshes'] if m['name']=='Wolf3D_Head')
        target=head['primitives'][0]['targets'][head['extras']['targetNames'].index('eyesClosed')]
        accessor=doc['accessors'][target['POSITION']];view=doc['bufferViews'][accessor['bufferView']]
        values=struct.unpack_from('<'+'f'*(accessor['count']*3),self.binary,view['byteOffset'])
        self.assertGreater(max(abs(x) for x in values),.001)

    def test_original_and_collar_preserved(self):
        self.assertTrue((ROOT/'static/models/kaspian-original.glb').is_file())
        self.assertTrue(any(m['name']=='Kaspian_Collar' for m in self.document['meshes']))
        self.assertTrue(self.document['skins'])

if __name__=='__main__':unittest.main()
