from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import requests
import base64
import os
import socket
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings if we need to disable verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client with API key from environment variable
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None

def get_image_base64(image_url):
    """Download image from URL and convert to base64"""
    try:
        # Get proxy settings from environment variables
        # Clash for Windows typically uses port 7890 for HTTP proxy
        http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
        
        # If no proxy is set in env, try common Clash ports (7890, 7891)
        # You can set HTTP_PROXY=http://127.0.0.1:7890 in your .env file to override
        if not http_proxy and not https_proxy:
            # Try to detect Clash proxy - common ports
            for port in [7890, 7891]:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('127.0.0.1', port))
                    sock.close()
                    if result == 0:  # Port is open
                        http_proxy = f'http://127.0.0.1:{port}'
                        https_proxy = f'http://127.0.0.1:{port}'
                        break
                except:
                    continue
        
        proxies = {}
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        
        # Headers to make request look more like a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
        }
        
        # Try with proxy first, then without if it fails
        try:
            response = requests.get(
                image_url, 
                timeout=30,
                proxies=proxies if proxies else None,
                headers=headers,
                verify=False,  # Disable SSL verification to avoid proxy SSL issues
                allow_redirects=True
            )
        except (requests.exceptions.ProxyError, requests.exceptions.SSLError, requests.exceptions.ConnectionError) as proxy_error:
            # If proxy fails, try without proxy (direct connection)
            print(f"Proxy connection failed, trying direct connection: {proxy_error}")
            response = requests.get(
                image_url,
                timeout=30,
                headers=headers,
                verify=False,
                allow_redirects=True
            )
        
        response.raise_for_status()
        
        # Get image content
        image_content = response.content
        
        # Convert to base64
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # Determine image format from content type or URL
        content_type = response.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type or image_url.lower().endswith(('.jpg', '.jpeg')):
            image_format = 'jpeg'
        elif 'png' in content_type or image_url.lower().endswith('.png'):
            image_format = 'png'
        elif 'gif' in content_type or image_url.lower().endswith('.gif'):
            image_format = 'gif'
        elif 'webp' in content_type or image_url.lower().endswith('.webp'):
            image_format = 'webp'
        else:
            image_format = 'jpeg'  # Default to jpeg
        
        return f"data:image/{image_format};base64,{image_base64}"
    except Exception as e:
        raise Exception(f"Error downloading image: {str(e)}")

@app.route('/')
def index():
    """Render the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading template: {str(e)}", 500

@app.route('/test')
def test():
    """Test route to check if Flask is working"""
    return jsonify({'status': 'OK', 'message': 'Flask is running!'})

@app.route('/describe', methods=['POST'])
def describe_image():
    """Process image URL and get description from OpenAI"""
    try:
        data = request.get_json()
        image_url = data.get('image_url', '').strip()
        
        if not image_url:
            return jsonify({'error': 'Please provide an image URL'}), 400
        
        # Validate URL
        if not (image_url.startswith('http://') or image_url.startswith('https://')):
            return jsonify({'error': 'Invalid URL. Please provide a valid HTTP/HTTPS URL'}), 400
        
        # Download and convert image to base64
        try:
            image_data = get_image_base64(image_url)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
        # Check if API key is set
        if not client:
            return jsonify({'error': 'OpenAI API key is not configured. Please set OPENAI_API_KEY in your .env file.'}), 500
        
        # Call OpenAI Vision API
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # You can also use "gpt-4-turbo" or "gpt-4-vision-preview"
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this image in detail. Include all visible elements, colors, objects, people, text, layout, style, and any other relevant details. Be thorough and specific."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            description = response.choices[0].message.content
            
            return jsonify({
                'success': True,
                'description': description,
                'image_url': image_url,
                'image_data': image_data  # Include base64 image data
            })
            
        except Exception as e:
            error_msg = str(e)
            error_lower = error_msg.lower()
            
            # Check for specific OpenAI error types
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_type = error_data['error'].get('type', '')
                        error_code = error_data['error'].get('code', '')
                        
                        if error_type == 'insufficient_quota' or error_code == 'insufficient_quota':
                            return jsonify({
                                'error': 'OpenAI API quota exceeded. Your account has run out of credits or has no billing set up. Please check your OpenAI account billing and add payment method at https://platform.openai.com/account/billing'
                            }), 429
                        elif error_type == 'invalid_api_key' or 'authentication' in error_lower:
                            return jsonify({'error': 'Invalid OpenAI API key. Please check your API key in the .env file.'}), 401
                        elif error_type == 'rate_limit_exceeded' or 'rate limit' in error_lower:
                            return jsonify({'error': 'OpenAI API rate limit exceeded. Please try again later.'}), 429
                except:
                    pass
            
            # Fallback to string matching
            if 'authentication' in error_lower or 'api key' in error_lower or 'invalid' in error_lower:
                return jsonify({'error': 'Invalid OpenAI API key. Please check your API key in the .env file.'}), 401
            elif 'quota' in error_lower or 'insufficient_quota' in error_lower:
                return jsonify({
                    'error': 'OpenAI API quota exceeded. Your account has run out of credits or has no billing set up. Please check your OpenAI account billing and add payment method at https://platform.openai.com/account/billing'
                }), 429
            elif 'rate limit' in error_lower:
                return jsonify({'error': 'OpenAI API rate limit exceeded. Please try again later.'}), 429
            else:
                return jsonify({'error': f'Error calling OpenAI API: {error_msg}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    # Disable debug mode reloader to avoid issues
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)

