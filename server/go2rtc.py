import os
import time
import subprocess
import requests
import yaml
from urllib import parse

class Go2RTC:
    def __init__(self, bundle_dir, config, log_level, logger):
        self.logger = logger
        self.proc = None

        self.bin = os.path.join(bundle_dir, "bin", "go2rtc")
        self.config = os.path.join(bundle_dir, "bin", "go2rtc.yaml")
        self.ffmpeg = os.path.join(bundle_dir, "bin", "ffmpeg.bin")

        # Get video stream config from settings.ini
        streams = {
            stream: device
            for stream, device in config.items('video_streams')
            if device
        }
        
        # Construct go2rtc config
        self.go2rtc_config = {
            'ffmpeg': {'bin': self.ffmpeg, 'mjpeg': '-c:v mjpeg -q:v 2 -vf "unsharp=5:5:0.5:5:5:0.0"'},
            'webrtc': {'listen': ':8555', 'candidates': ['stun:8555']},
            'streams': streams,
            'log': {'format': 'text', 'level': log_level}
        }

    def get_devices(self, url):
        response = requests.get(url)
        data = response.json()

        devices = []
        video_count = 0
        for source in data.get('sources', []):
            url_str = source.get('url', '')
            if not url_str:
                continue

            parsed_url = parse.urlparse(url_str)
            query_params = parse.parse_qs(parsed_url.query)
            if 'video' not in query_params:
                continue

            device_name = query_params['video'][0]
            query_params['video'] = [str(video_count)]
            new_query = parse.urlencode(query_params, doseq=True)
            fragment_parts = parsed_url.fragment.split('#')
            clean_fragment = '#'.join(part for part in fragment_parts if 'hardware' not in part)
            modified_url = parse.urlunparse(parsed_url._replace(query=new_query, fragment=clean_fragment))

            devices.append({
                'index': video_count,
                'name': device_name,
                'url': modified_url,
                'source_url': url_str,
            })
            video_count += 1

        return devices

    def start(self):
        with open(self.config, 'w') as f:
            yaml.dump(self.go2rtc_config, f, default_flow_style=False, sort_keys=False)

        self.proc = subprocess.Popen([self.bin, "-c", self.config])

        for _ in range(10):
            try:
                devices = self.get_devices("http://127.0.0.1:1984/api/ffmpeg/devices")
                for device in devices:
                    print(f" * Found go2rtc video device {device['index']} - {device['name']} - {device['url']}")
                return
            except Exception:
                time.sleep(0.2)

    def stop(self):
        if self.proc:
            self.proc.terminate()
