import ssl
import socket
import h2.connection
import h2.events
import h2.settings
import certifi
import time
import gzip
import io

class Http2Client:
    def __init__(self):
        # Create SSL context with TLS 1.3
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.context.load_verify_locations(certifi.where())
        self.context.set_alpn_protocols(['h2'])
        self.context.minimum_version = ssl.TLSVersion.TLSv1_3
        self.context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Create socket and wrap with SSL
        self.sock = socket.create_connection(('web-production.lime.bike', 443))
        self.sock = self.context.wrap_socket(
            self.sock,
            server_hostname='web-production.lime.bike',
            do_handshake_on_connect=True
        )
        
        # Initialize H2 connection
        self.conn = h2.connection.H2Connection()
        self.conn.initiate_connection()
        self.sock.send(self.conn.data_to_send())
        
        # Store the TLS session for reuse
        self.session = self.sock.session
        
        print(f"Protocol: {self.sock.version()}")
        print(f"Cipher: {self.sock.cipher()}")
        print(f"ALPN: {self.sock.selected_alpn_protocol()}")
        
    def send_request(self):
        # Send the exact headers from flow 367
        headers = [
            (':method', 'GET'),
            (':path', '/lime_web_app/promos/coupons/new?authToken=eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX3Rva2VuIjoiS1BRNVFKRERGWDNLWiIsImxvZ2luX2NvdW50IjoyfQ.ZpSr-FI8hB8DNx_AXZk0KZ2m_7e5x152iy0urZ7zLBA'),
            (':scheme', 'https'),
            (':authority', 'web-production.lime.bike'),
            ('sec-ch-ua', '"Android WebView";v="129", "Not=A?Brand";v="8", "Chromium";v="129"'),
            ('sec-ch-ua-mobile', '?0'),
            ('sec-ch-ua-platform', '"Android"'),
            ('upgrade-insecure-requests', '1'),
            ('user-agent', 'Mozilla/5.0 (Linux; Android 9; SM-S908E Build/TP1A.220624.014; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.6668.70 Safari/537.36'),
            ('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'),
            ('x-requested-with', 'com.limebike'),
            ('sec-fetch-site', 'none'),
            ('sec-fetch-mode', 'navigate'),
            ('sec-fetch-user', '?1'),
            ('sec-fetch-dest', 'document'),
            ('accept-encoding', 'gzip, deflate, br, zstd'),
            ('accept-language', 'en-US,en;q=0.9'),
            ('cookie', 'authToken=eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX3Rva2VuIjoiS1BRNVFKRERGWDNLWiIsImxvZ2luX2NvdW50IjoyfQ.ZpSr-FI8hB8DNx_AXZk0KZ2m_7e5x152iy0urZ7zLBA; _language=en-US; _os=Android; _os_version=28; _app_version=3.191.2; _device_token=af350b64-9d44-40ae-8143-18df830b3595; _user_token=KPQ5QJDDFX3KZ; _user_latitude=46.073272; _user_longitude=23.580489; amplitudeSessionId=1735193891531; __stripe_mid=59d74421-4c6e-4b72-9d02-b1c53f1f29335a7b8d; __stripe_sid=f59059fa-dce1-4ab8-970c-f55de106b6b9b1e9c1; __cf_bm=.llrv1XXkYllMwVcBKJ2FeXL20gyKzh1_Snhzip3P08-1735194872-1.0.1.1-_WKnHD2FEzsnHFG_3SRmBp_rnlbYH.5m7s2myGOCNpkEqtTivlR3R44kOLo44fP6Nowf5bLYPbBFi5og8TPjQA; _mkra_stck=mysql%3A1735195161.0615816; _limebike-web_session=QHizPf%2BiTazjkbnpJyuYhKpl2%2ByT6RCUj6uxXRyt%2F1MZ%2BBHpmGJVLly5d2dHCPKDZbCURXfd8YfP20WbnXt1Bfl06dYDUehJNpWnxoH8xvIGHrGQPrEP9rqbqRFQqLZsGoZ5wiZ%2Fwy6uKoSJM1iSVr0TmgtMBX4LG5FK6sfhJef3dwCumc0RoGo26ucqMNG9773z16NOh8z7TWbXBV0dffpCPRspe8wZ28%2BDFh3Bb5Gv4L7yZG7cGG8OCDCOOXw227CDAA3PCP19%2B29qY0aBg5%2FxMpf5I9RhgBhLBRm8Zf8kd%2Fw5OeLxRXu3wLsnETLRfZlne30ShhTQ1S5BSmUaaV2pTpGKgtht7fnolho1HwgpwKQcfqImAS3PjmeUVBgf0%2FYbzrwXyDxhu0SsKQRt2UyMGDObcmxOFpTYI%2Fpg5v2trJuBcg%3D%3D--v05VNegeda2zOM4l--yzbkeLjLpv%2F3fSeVbz70ng%3D%3D'),
            ('priority', 'u=0, i')
        ]
        
        stream_id = self.conn.get_next_available_stream_id()
        self.conn.send_headers(stream_id, headers, end_stream=True)
        self.sock.send(self.conn.data_to_send())
        
        # Read response
        response_data = b""
        response_headers = {}
        while True:
            try:
                data = self.sock.recv(65536)
                if not data:
                    break
                response_data += data
                events = self.conn.receive_data(data)
                
                for event in events:
                    if isinstance(event, h2.events.ResponseReceived):
                        print(f"\nResponse headers:")
                        for name, value in event.headers:
                            name = name.decode()
                            value = value.decode()
                            response_headers[name] = value
                            print(f"{name}: {value}")
                    elif isinstance(event, h2.events.DataReceived):
                        print(f"\nResponse data:")
                        try:
                            if response_headers.get('content-encoding') == 'gzip':
                                decompressed = gzip.decompress(event.data)
                                print(decompressed.decode())
                            else:
                                print(event.data.decode())
                        except UnicodeDecodeError:
                            print(event.data)
                    elif isinstance(event, h2.events.StreamEnded):
                        print("\nStream ended")
                    elif isinstance(event, h2.events.WindowUpdated):
                        print(f"\nWindow updated: stream_id={event.stream_id}, delta={event.delta}")
                    else:
                        print(f"\nOther event: {event}")
                
                # Send any pending data
                outbound_data = self.conn.data_to_send()
                if outbound_data:
                    self.sock.send(outbound_data)
                    
            except socket.timeout:
                break
                
            time.sleep(0.1)  # Small delay to prevent busy waiting

if __name__ == "__main__":
    client = Http2Client()
    client.send_request() 