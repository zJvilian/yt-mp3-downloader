import io
import zipfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app import create_app
from app.routes import active_downloads
from app.downloader import download_youtube

class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app()
        self.app.config.update(TESTING=True, OUTPUT_DIR_MP3=self.temp.name, OUTPUT_DIR_MP4=self.temp.name)
        self.client = self.app.test_client()
        active_downloads.clear()

    def tearDown(self):
        self.temp.cleanup()

    def test_page_and_settings(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="quality"', response.data)

    def test_invalid_requests_do_not_start_jobs(self):
        with patch('app.routes.threading.Thread') as thread:
            for url in ['file:///etc/passwd', 'not-a-url']:
                self.client.post('/', data={'url': url})
            thread.assert_not_called()

    def test_delete_cannot_escape_directory(self):
        response = self.client.post('/delete/mp3/../outside.mp3')
        self.assertEqual(response.status_code, 400)

    def test_clear_all_removes_files_and_finished_jobs(self):
        for name in ('a.mp3', 'b.mp4', 'keep.txt'):
            (Path(self.temp.name) / name).touch()
        active_downloads.update(done={'status': 'completed'}, busy={'status': 'downloading'})
        self.assertTrue(self.client.post('/clear').get_json()['success'])
        self.assertEqual({p.name for p in Path(self.temp.name).iterdir()}, {'keep.txt'})
        self.assertEqual(list(active_downloads), ['busy'])

    def test_download_all_zips_one_type(self):
        for name in ('a.mp3', 'b.mp3', 'c.mp4'):
            (Path(self.temp.name) / name).write_bytes(name.encode())
        response = self.client.get('/download-all/mp3')
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            self.assertEqual(sorted(zf.namelist()), ['a.mp3', 'b.mp3'])
            self.assertEqual(zf.read('a.mp3'), b'a.mp3')
        response.close()
        self.assertEqual(self.client.get('/download-all/txt').status_code, 400)

    def test_stream_has_app_context(self):
        response = self.client.get('/events', buffered=False)
        self.assertIn(b'"type": "initial"', next(response.response))
        response.close()

    def test_options_and_cleanup(self):
        with patch('app.downloader.yt_dlp.YoutubeDL') as ydl:
            ydl.return_value.__enter__.return_value.download.return_value = 0
            download_youtube('https://example.com/video', output_dir=self.temp.name, quality='320', playlist=True)
            options = ydl.call_args.args[0]
            self.assertFalse(options['noplaylist'])
            self.assertEqual(options['postprocessors'][0]['preferredquality'], '320')
            self.assertFalse(Path(options['paths']['temp']).exists())

    def test_failure_status(self):
        with patch('app.routes.threading.Thread') as thread, patch('app.routes.download_youtube', side_effect=RuntimeError('failed')):
            self.client.post('/', data={'url': 'https://example.com/video'})
            thread.call_args.kwargs['target']()
        self.assertEqual(next(iter(active_downloads.values()))['status'], 'failed')

if __name__ == '__main__':
    unittest.main()
