from dotenv import load_dotenv
import requests
import os
from bs4 import BeautifulSoup

load_dotenv()

backup_path = "LMS Backup"
os.makedirs(backup_path, exist_ok=True)

session = requests.Session()

session_cookie = os.getenv("SESSION_COOKIE")

if not session_cookie:
    raise SystemExit("Set session cookie value first")

cookies = {
    "PHPSESSID": session_cookie,
}
session.cookies.update(cookies)

headers = {
    "Cookie": f"PHPSESSID={session_cookie}",
}

url = "https://lms.bahria.edu.pk/Student/Dashboard.php"
response = session.get(url, headers=headers)

if response.url != url:
    raise SystemExit("Session cookie value is not correct")

print("Logged in to LMS")

soup = BeautifulSoup(response.text, "html.parser")

url = "https://lms.bahria.edu.pk/Student/CourseOutline.php"
response = session.get(url, headers=headers)

semesters = {
    option.text.strip(): option["value"]
    for option in reversed(soup.select("#semesterId option"))
}

for key, value in list(semesters.items()):
    url = f"https://lms.bahria.edu.pk/Student/CourseOutline.php?s={value}"
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    if len(soup.select("table td")) == 1:
        semesters.pop(key)

for semester in semesters:
    os.makedirs(f"{backup_path}/{semester}", exist_ok=True)

    url = f"https://lms.bahria.edu.pk/Student/CoursePlan.php?s={semesters[semester]}"
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    courses = {
        option.text.strip(): option["value"]
        for option in soup.select("#courseId option")
    }
    courses.pop("Select Course")

    for course in courses:
        os.makedirs(f"{backup_path}/{semester}/{course}", exist_ok=True)
        os.makedirs(f"{backup_path}/{semester}/{course}/Course Outline", exist_ok=True)

    url = f"https://lms.bahria.edu.pk/Student/CourseOutline.php?s={semesters[semester]}"
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    course_current = 0
    for a_tag in soup.select("td a"):
        url = f"https://lms.bahria.edu.pk/Student/{a_tag.get('href')}"
        response = requests.get(url, headers=headers)
        filename = response.headers["content-disposition"].split('filename="')[1][:-1]
        filepath = f"{backup_path}/{semester}/{list(courses.keys())[course_current]}/Course Outline/{filename}"

        with open(filepath, "wb") as file:
            file.write(response.content)

        course_current += 1
