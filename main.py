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
        os.makedirs(f"{backup_path}/{semester}/{course}/Course Outline", exist_ok=True)

        ############################
        ########## Quizzes #########
        ############################

        url = f"https://lms.bahria.edu.pk/Student/Quizzes.php?s={semesters[semester]}&oc={courses[course]}"
        response = session.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        quizzes = {
            cells[1].text.strip(): [
                cells[2].find("a").get("href") if cells[2].find("a") else "",
                cells[4].find("a").get("href") if cells[4].find("a") else "",
            ]
            for row in soup.select("tr")
            if (len(cells := row.find_all("td")) > 1)
        }

        os.makedirs(f"{backup_path}/{semester}/{course}/Quizzes", exist_ok=True)

        if not len(quizzes):
            os.rename(
                f"{backup_path}/{semester}/{course}/Quizzes",
                f"{backup_path}/{semester}/{course}/Quizzes (Empty)",
            )

        for quiz in quizzes:
            os.makedirs(
                f"{backup_path}/{semester}/{course}/Quizzes/{quiz}", exist_ok=True
            )

            url = f"https://lms.bahria.edu.pk/Student/{quizzes[quiz][0]}"
            response = requests.get(url, headers=headers)

            if response.status_code != 200 or not quizzes[quiz][0]:
                os.rename(
                    f"{backup_path}/{semester}/{course}/Quizzes/{quiz}",
                    f"{backup_path}/{semester}/{course}/Quizzes/{quiz} (Empty)",
                )
                continue

            filename = response.headers["content-disposition"].split('filename="')[1][
                :-1
            ]
            filepath = f"{backup_path}/{semester}/{course}/Quizzes/{quiz}/{filename}"

            with open(filepath, "wb") as file:
                file.write(response.content)

            if quizzes[quiz][1]:
                url = f"https://lms.bahria.edu.pk/Student/{quizzes[quiz][1]}"
                response = requests.get(url, headers=headers)

                filename = response.headers["content-disposition"].split('filename="')[
                    1
                ][:-1]
                filepath = f"{backup_path}/{semester}/{course}/Quizzes/{quiz}/Solution - {filename}"

                with open(filepath, "wb") as file:
                    file.write(response.content)

    ############################
    ###### Course Outline ######
    ############################

    url = f"https://lms.bahria.edu.pk/Student/CourseOutline.php?s={semesters[semester]}"
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    course_outlines = {
        cells[1].text.strip(): (
            cells[2].find("a").get("href") if cells[2].find("a") else ""
        )
        for row in soup.select("tr")
        if (cells := row.find_all("td"))
    }

    for course in course_outlines:
        url = f"https://lms.bahria.edu.pk/Student/{course_outlines[course]}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200 or not course_outlines[course]:
            os.rename(
                f"{backup_path}/{semester}/{course}/Course Outline",
                f"{backup_path}/{semester}/{course}/Course Outline (Empty)",
            )
            continue

        filename = response.headers["content-disposition"].split('filename="')[1][:-1]
        filepath = f"{backup_path}/{semester}/{course}/Course Outline/{filename}"

        with open(filepath, "wb") as file:
            file.write(response.content)
