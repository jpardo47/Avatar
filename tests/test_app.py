import os
import unittest
from unittest.mock import patch, Mock
from app import app
from services.chat import answer, ProviderError

class AppTests(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ, {'OPENROUTER_API_KEY':'','CHAT_MODEL':''})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.client=app.test_client()

    def test_home_and_assets(self):
        page=self.client.get('/')
        self.assertEqual(page.status_code,200)
        self.assertIn(b'avatar-stage',page.data)
        for path in ('css/app.css','js/app.js','js/avatar-view.js','js/editor.js','js/settings.mjs','models/kaspian.glb','vendor/three/three.module.js','vendor/three/addons/loaders/GLTFLoader.js'):
            with self.client.get('/static/'+path) as result:
                self.assertEqual(result.status_code,200,path)

    def test_demo_response_and_expression(self):
        result=self.client.post('/api/chat',json={'message':'Hola'})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json['expression'],'happy')
        self.assertEqual(result.json['mode'],'demo')
        self.assertEqual(self.client.get('/health').json['mode'],'demo')

    def test_module_mime_type(self):
        with self.client.get('/static/js/settings.mjs') as result:
            self.assertIn(result.mimetype,('text/javascript','application/javascript'))

    def test_invalid_messages(self):
        for value in ({},[],None,{'message':2},{'message':' '},{'message':'a'*2001}):
            self.assertEqual(self.client.post('/api/chat',json=value).status_code,400)
        self.assertEqual(self.client.post('/api/chat',data='oops',content_type='application/json').status_code,400)

    @patch('services.chat.requests.post')
    def test_provider(self, post):
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':'test','CHAT_MODEL':'test-model'}):
            post.return_value=Mock(json=lambda:{'choices':[{'message':{'content':'¡Hola!'}}]})
            self.assertEqual(answer('Hola')['mode'],'online')
            post.return_value=Mock(json=lambda:{'choices':[]})
            self.assertEqual(self.client.post('/api/chat',json={'message':'Hola'}).status_code,502)

if __name__=='__main__':
    unittest.main()
