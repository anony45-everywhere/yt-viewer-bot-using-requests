import requests
import random
import time
from urllib.parse import urlencode, parse_qs, urlparse
import re
import json
import logging
from typing import List, Optional, Dict
import os
import concurrent.futures
from tqdm import tqdm
import sys
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_viewer.log'),
        logging.StreamHandler()
    ]
)

class ProxyManager:
    def __init__(self):
        self.best_proxy: Optional[dict] = None
        self.logger = logging.getLogger(__name__)
        self.tested_count = 0
        self.working_count = 0
        self.total_proxies = 0
        self.max_working_proxies = 10  # Reduced since we're only using HTTPS
        
    def test_proxy_speed(self, proxy: str) -> Optional[float]:
        """Test a single proxy's speed"""
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            # Use a faster test URL (Google's favicon)
            start_time = time.time()
            response = requests.get('https://www.google.com/favicon.ico', 
                                 proxies=proxy_dict, 
                                 timeout=2,  # Further reduced timeout
                                 verify=False)  # Skip SSL verification for speed
            
            if response.status_code == 200:
                speed = time.time() - start_time
                self.working_count += 1
                return speed
            return None
            
        except Exception:
            return None
        finally:
            self.tested_count += 1
            
    def test_proxies(self, proxies: List[str]) -> Dict[str, float]:
        """Test multiple proxies concurrently"""
        proxy_speeds = {}
        self.total_proxies = len(proxies)
        self.tested_count = 0
        self.working_count = 0
        
        # Create progress bar
        pbar = tqdm(total=self.total_proxies, desc="Testing HTTPS proxies", 
                   bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
        
        def update_progress():
            pbar.update(1)
            success_rate = (self.working_count / self.tested_count * 100) if self.tested_count > 0 else 0
            pbar.set_postfix({
                'Working': self.working_count,
                'Success Rate': f'{success_rate:.1f}%'
            })
        
        # Use more workers for faster testing
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:  # Increased workers
            # Submit initial batch of proxies
            future_to_proxy = {}
            batch_size = 100  # Smaller batch size for HTTPS only
            
            for i in range(0, len(proxies), batch_size):
                batch = proxies[i:i + batch_size]
                for proxy in batch:
                    future = executor.submit(self.test_proxy_speed, proxy)
                    future_to_proxy[future] = proxy
                
                # Process completed futures
                for future in concurrent.futures.as_completed(future_to_proxy):
                    proxy = future_to_proxy[future]
                    try:
                        speed = future.result()
                        if speed is not None:
                            proxy_speeds[proxy] = speed
                            # Early stopping if we have enough working proxies
                            if len(proxy_speeds) >= self.max_working_proxies:
                                executor._threads.clear()
                                concurrent.futures.thread._threads_queues.clear()
                                break
                    except Exception as e:
                        self.logger.debug(f"Proxy {proxy} test failed: {str(e)}")
                    finally:
                        update_progress()
                    
                    # Break outer loop if we have enough proxies
                    if len(proxy_speeds) >= self.max_working_proxies:
                        break
                
                # Clear futures for next batch
                future_to_proxy.clear()
        
        pbar.close()
        return proxy_speeds
        
    def load_and_test_proxies(self):
        """Load proxies, test them, and select the best one"""
        try:
            # Download fresh proxies
            print("\nDownloading HTTPS proxies...")
            https_response = requests.get('https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt', timeout=5)
            
            if https_response.status_code != 200:
                print("Failed to download HTTPS proxies")
                return False
                
            proxies = [p.strip() for p in https_response.text.split('\n') if p.strip()]
            random.shuffle(proxies)  # Shuffle for better distribution
            
            if not proxies:
                print("No HTTPS proxies found")
                return False
                
            print(f"Downloaded {len(proxies)} HTTPS proxies")
                
            # Test proxies and get speeds
            print(f"\nTesting proxies for speed (will stop after finding {self.max_working_proxies} working proxies)...")
            proxy_speeds = self.test_proxies(proxies)
            
            if not proxy_speeds:
                print("No working HTTPS proxies found")
                return False
                
            # Select the fastest proxy
            fastest_proxy = min(proxy_speeds.items(), key=lambda x: x[1])[0]
            self.best_proxy = {
                'http': f'http://{fastest_proxy}',
                'https': f'http://{fastest_proxy}'
            }
            
            print(f"\nProxy Testing Results:")
            print(f"Total HTTPS Proxies Tested: {self.tested_count}")
            print(f"Working Proxies Found: {self.working_count}")
            print(f"Success Rate: {(self.working_count / self.tested_count * 100):.1f}%")
            print(f"Selected fastest proxy: {fastest_proxy} (speed: {proxy_speeds[fastest_proxy]:.2f}s)")
            
            return True
                
        except Exception as e:
            print(f"Error loading and testing proxies: {str(e)}")
            return False

    def get_proxy(self) -> Optional[dict]:
        """Get the selected best proxy"""
        return self.best_proxy

class YouTubeViewer:
    def __init__(self):
        self.base_url = "https://www.youtube.com/api/stats/watchtime"
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site'
        })
        self.logger = logging.getLogger(__name__)
        
        print("\nInitializing YouTube Viewer...")
        # Initialize and select best proxy
        self.proxy_manager = ProxyManager()
        if self.proxy_manager.load_and_test_proxies():
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                self.session.proxies.update(proxy)
                print("Successfully configured session with best proxy")
            else:
                print("No proxy available, using direct connection")
        else:
            print("Failed to load proxies, using direct connection")

    def get_video_info(self, video_id):
        """Get video information"""
        try:
            # List of Invidious instances to try
            invidious_instances = [
                "https://vid.puffyan.us",
                "https://invidious.kavin.rocks",
                "https://invidious.snopyta.org",
                "https://y.com.sb",
                "https://invidious.namazso.eu"
            ]
            
            # First try Invidious instances
            for instance in invidious_instances:
                try:
                    api_url = f"{instance}/api/v1/videos/{video_id}"
                    print(f"Trying Invidious instance: {instance}")
                    
                    response = self.session.get(api_url, timeout=5)
                    if response.status_code == 200:
                        try:
                            video_data = response.json()
                            duration = int(video_data.get('lengthSeconds', 0))
                            if duration > 0:
                                print(f"Video duration from Invidious: {duration} seconds")
                                return duration
                        except json.JSONDecodeError:
                            continue
                except Exception as e:
                    print(f"Error with {instance}: {str(e)}")
                    continue

            # Try the embed endpoint
            embed_url = f"https://www.youtube.com/embed/{video_id}"
            print(f"\nFetching video info from embed URL: {embed_url}")
            
            response = self.session.get(embed_url, timeout=10)
            
            if response.status_code == 200:
                # Try to get video info from ytInitialPlayerResponse
                try:
                    player_response_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', response.text)
                    if player_response_match:
                        player_response = json.loads(player_response_match.group(1))
                        if 'videoDetails' in player_response:
                            duration = int(player_response['videoDetails'].get('lengthSeconds', 0))
                            if duration > 0:
                                print(f"Video duration: {duration} seconds")
                                return duration
                except Exception as e:
                    print(f"Error parsing player response: {str(e)}")

                # Try multiple patterns to find video duration
                patterns = [
                    r'"lengthSeconds":"(\d+)"',
                    r'"lengthSeconds":(\d+)',
                    r'approxDurationMs":"(\d+)"',
                    r'"duration":"PT(\d+)M(\d+)S"',
                    r'"duration":(\d+)',
                    r'lengthSeconds\\*":\\*"(\d+)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        if 'PT' in pattern:
                            minutes, seconds = map(int, match.groups())
                            duration = minutes * 60 + seconds
                        elif 'approxDurationMs' in pattern:
                            duration = int(int(match.group(1)) / 1000)
                        else:
                            duration = int(match.group(1))
                        if duration > 0:
                            print(f"Video duration: {duration} seconds")
                            return duration

            # Try the oEmbed endpoint
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            print(f"\nTrying oEmbed endpoint: {oembed_url}")
            
            try:
                oembed_response = self.session.get(oembed_url, timeout=10)
                if oembed_response.status_code == 200:
                    oembed_data = oembed_response.json()
                    title = oembed_data.get('title', '')
                    print(f"Video title: {title}")
            except Exception as e:
                print(f"Error with oEmbed endpoint: {str(e)}")

            # If all else fails, try to get duration from video page metadata
            watch_url = f"https://www.youtube.com/watch?v={video_id}"
            response = self.session.get(watch_url, timeout=10)
            
            if response.status_code == 200:
                # Try to find duration in meta tags
                duration_match = re.search(r'<meta itemprop="duration" content="PT(\d+)M(\d+)S">', response.text)
                if duration_match:
                    minutes, seconds = map(int, duration_match.groups())
                    duration = minutes * 60 + seconds
                    print(f"Video duration from meta tag: {duration} seconds")
                    return duration
            
            print("Could not find video duration. Saving page content for debugging...")
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Page content saved to debug_page.html")
            
            # If we have a title but no duration, use a default duration
            if 'title' in locals():
                print("Using default duration of 180 seconds since we found the title")
                return 180
                
            return None

        except Exception as e:
            print(f"Error getting video info: {str(e)}")
            return None

    def generate_cpn(self):
        """Generate a random CPN (Client Playback Nonce)"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        return ''.join(random.choice(alphabet) for _ in range(16))

    def create_payload(self, video_id, current_time, duration, cpn):
        """Create payload for watchtime request"""
        payload = {
            'ns': 'yt',
            'el': 'detailpage',
            'cpn': cpn,
            'ver': '2',
            'cmt': str(current_time),
            'fmt': '399',
            'fs': '0',
            'rt': str(current_time + 2),
            'lact': str(int(time.time() * 1000)),
            'cl': '706555921',
            'state': 'playing',
            'volume': '100',
            'cbr': 'Chrome',
            'cbrver': '131.0.0.0',
            'c': 'WEB',
            'cver': '2.20241219.01.01',
            'cplayer': 'UNIPLAYER',
            'cos': 'Windows',
            'cosver': '10.0',
            'cplatform': 'DESKTOP',
            'hl': 'en_US',
            'cr': 'US',
            'len': str(duration),
            'rtn': str(min(current_time + 5, duration)),
            'afmt': '251',
            'idpj': '-7',
            'ldpj': '-13',
            'rti': str(int(current_time)),
            'st': str(max(0, current_time - 5)),
            'et': str(current_time),
            'muted': '0',
            'docid': video_id,
        }
        return payload

    def send_watchtime_request(self, video_id, current_time, duration, cpn):
        """Send a single watchtime request"""
        try:
            payload = self.create_payload(video_id, current_time, duration, cpn)
            url = f"{self.base_url}?{urlencode(payload)}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 204:
                print(f"Watchtime request at {current_time:.1f}s successful")
                return True
            else:
                print(f"Watchtime request failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error in watchtime request: {str(e)}")
            return False

    def simulate_view(self, video_id):
        """Simulate a video view by sending watchtime requests"""
        try:
            print(f"\nStarting view simulation for video ID: {video_id}")
            
            # First get the video info
            duration = self.get_video_info(video_id)
            if duration is None:
                print("Failed to get video duration")
                return False

            # Generate a single CPN for the entire session
            cpn = self.generate_cpn()
            
            # Calculate target watch duration (50-75% of video length)
            watch_percentage = random.uniform(0.5, 0.75)
            target_duration = duration * watch_percentage
            print(f"Target watch duration: {target_duration:.1f} seconds ({watch_percentage*100:.1f}% of video)")

            # Create progress bar for view simulation
            with tqdm(total=int(target_duration), desc="Simulating view", 
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}s [{elapsed}<{remaining}]') as pbar:
                
                # Start watching from beginning
                current_time = 0
                update_interval = min(5, duration / 10)

                # Initial watchtime request
                if not self.send_watchtime_request(video_id, 0, duration, cpn):
                    print("Failed to send initial watchtime request")
                    return False

                # Simulate watching the video with periodic updates
                while current_time < target_duration:
                    sleep_time = random.uniform(update_interval * 0.8, update_interval * 1.2)
                    time.sleep(sleep_time)
                    current_time += sleep_time
                    pbar.update(min(int(sleep_time), int(target_duration - pbar.n)))

                    if not self.send_watchtime_request(video_id, current_time, duration, cpn):
                        print(f"Failed watchtime request at {current_time:.1f}s, continuing anyway")
                        continue

            # Send final watchtime request
            final_success = self.send_watchtime_request(video_id, target_duration, duration, cpn)
            if final_success:
                print(f"Successfully completed watching {watch_percentage*100:.1f}% of the video")
            else:
                print("Final watchtime request failed")
            
            return final_success
            
        except Exception as e:
            self.logger.error(f"Error occurred: {str(e)}", exc_info=True)
            return False

if __name__ == "__main__":
    try:
        # Example usage
        viewer = YouTubeViewer()
        video_id = "Lw0omg4YGKU"  # Replace with your video ID
        success = viewer.simulate_view(video_id)
        print(f"\nView simulation {'successful' if success else 'failed'}")
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1) 