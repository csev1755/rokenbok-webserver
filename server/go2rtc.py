import os
import time
import subprocess
import requests
import yaml

class Go2RTC:
    def __init__(self, bundle_dir, config, log_level, logger):
        self.logger = logger
        self.proc = None

        self.bin = os.path.join(bundle_dir, "bin", "go2rtc")
        self.config = os.path.join(bundle_dir, "bin", "go2rtc.yaml")

        # Get video stream config from rokenbok_webserver.ini
        streams = {
            stream: device
            for stream, device in config.items('video_streams')
            if device
        }
        
        # Construct go2rtc config
        self.go2rtc_config = {
            'ffmpeg': {'mjpeg': '-c:v mjpeg -q:v 2 -vf "unsharp=5:5:0.5:5:5:0.0"'},
            'webrtc': {'listen': ':8555', 'candidates': ['stun:8555']},
            'streams': streams,
            'log': {'format': 'text', 'level': log_level}
        }

    def start(self):
        with open(self.config, 'w') as f:
            yaml.dump(self.go2rtc_config, f, default_flow_style=False, sort_keys=False)

        self.proc = subprocess.Popen([self.bin, "-c", self.config])

        # Print device list
        for _ in range(10):
            try:
                response = requests.get('http://127.0.0.1:1984/api/ffmpeg/devices')
                data = response.json()
                for source in data.get('sources', []):
                    self.logger.info(f"Found go2rtc ffmpeg device: {source.get('url')}")
                return
            except Exception:
                time.sleep(0.2)

    def stop(self):
        if self.proc:
            self.proc.terminate()
