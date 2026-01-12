import os
import socket
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse

def check_connection():
    print("🔍 DIAGNOSTIC TOOL: Azure OpenAI Connection Check")
    print("================================================")
    
    # 1. Load Configuration
    load_dotenv()
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not endpoint:
        print("❌ Error: AZURE_OPENAI_ENDPOINT not found in .env")
        return
    
    print(f"📡 Target Endpoint: {endpoint}")
    
    # 2. Check My IP
    try:
        my_ip = requests.get('https://api.ipify.org').text
        print(f"📍 Your Current Public IP: {my_ip}")
    except Exception as e:
        print(f"⚠️  Could not detect public IP: {e}")

    # 3. DNS Resolution
    try:
        parsed = urlparse(endpoint)
        hostname = parsed.hostname
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ DNS Resolution: {hostname} -> {ip_address}")
    except Exception as e:
        print(f"❌ DNS Error: Could not resolve {endpoint}")
        print(f"   Details: {e}")
        return

    # 4. HTTP Check (Timeout test)
    print("\n⏳ Testing connection (5s timeout)...")
    try:
        # Just checking if we can reach the server, auth error is GOOD (means connection established)
        response = requests.get(endpoint, timeout=5)
        print(f"✅ Connection Successful! Status Code: {response.status_code}")
        if response.status_code == 404 or response.status_code == 401:
            print("   (This is expected for the root endpoint. The server is reachable.)")
    except requests.exceptions.ConnectTimeout:
        print("❌ TIMEOUT: Could not connect to the server.")
        print("   👉 CAUSE: likely Firewall blocking or IP Restriction.")
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL CERTIFICATE ERROR: Your network is intercepting traffic.")
        print(f"   Details: {e}")
        print("\n🔄 Retrying with SSL Verification DISABLED (Testing only)...")
        try:
            response = requests.get(endpoint, timeout=5, verify=False)
            print(f"   ⚠️  Connection SUCCESSFUL (Insecure): Status {response.status_code}")
            print("   👉 CAUSE: Your network (WiFi) requires a custom certificate or is a Captive Portal.")
            print("   👉 FIX: Switch networks OR bypass SSL.")
        except Exception as e2:
             print(f"   ❌ Still failed after disabling SSL: {e2}")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Network unreachable.")
        print("   👉 CAUSE: DNS failure or local network blocking.")
    except Exception as e:
        print(f"❌ unexpected error: {e}")

    print("\n================================================")
    print("💡 RECOMMENDATION:")
    print("If you see a TIMEOUT or CONNECTION ERROR, but DNS works:")
    print("1. Go to Azure Portal -> Your OpenAI Resource")
    print("2. Click 'Networking' in the sidebar")
    print("3. Check the 'Firewall' section")
    print("4. Ensure 'Selected Networks' allows your new IP Address")
    print(f"   (Add Client IP: {my_ip})")

if __name__ == "__main__":
    check_connection()
