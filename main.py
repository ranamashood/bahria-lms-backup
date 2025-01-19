from dotenv import load_dotenv
import requests
import os

load_dotenv()

session = requests.Session()

session_cookie = os.getenv("SESSION_COOKIE")

if not session_cookie:
    raise SystemExit("Set session cookie value first")

cookies = {
    "PHPSESSID": session_cookie,
}
session.cookies.update(cookies)

url = "https://lms.bahria.edu.pk/Student/Dashboard.php"
response = session.get(url)

if response.url != url:
    raise SystemExit("Session cookie value is not correct")

print("Request successful!")

url = "https://lms.bahria.edu.pk/Student/CourseOutline.php"
response = session.get(url)

print(response.text)
