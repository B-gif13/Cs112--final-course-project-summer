
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "preview-only-not-secure"

MOCK_CLINICIAN = {"id": "CLN-01", "name": "Dr. Ama Boateng", "role": "clinician"}
MOCK_PATIENT = {"id": "PAT-01", "name": "Kwesi Owusu", "role": "patient"}

 
@app.context_processor
def inject_defaults():
    return {"unread_message_count": 2}


def current_user():
    return MOCK_CLINICIAN if session.get("role", "clinician") == "clinician" else MOCK_PATIENT


@app.route("/")
def root():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["role"] = request.form.get("role", "clinician")
        flash("Logged in successfully.", "success")
        return redirect(url_for("clinician_dashboard" if session["role"] == "clinician" else "patient_dashboard"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard/clinician")
def clinician_dashboard():
    stats = {"open_tasks": 12, "pending_review": 4, "patients_active": 18, "overdue": 2}
    tasks = [
        {"id": "T1", "patient_name": "Kwesi Owusu", "title": "Weekly symptom log", "status": "submitted", "due_date": "2026-09-01", "overdue": False},
        {"id": "T2", "patient_name": "Ama Serwaa", "title": "Medication adherence sheet", "status": "pending", "due_date": "2026-08-25", "overdue": True},
        {"id": "T3", "patient_name": "Yaw Mensah", "title": "Lab results upload", "status": "reviewed", "due_date": "2026-08-20", "overdue": False},
    ]
    return render_template("clinician_dashboard.html", current_user=MOCK_CLINICIAN, active_page="dashboard", stats=stats, tasks=tasks)


@app.route("/dashboard/patient")
def patient_dashboard():
    tasks = [
        {"id": "T1", "title": "Weekly symptom log", "clinician_name": "Dr. Ama Boateng", "status": "submitted", "due_date": "2026-09-01",
         "instructions": "Log your symptoms daily and upload as a .csv by Sunday.", "feedback": None},
        {"id": "T4", "title": "Post-visit reflection", "clinician_name": "Dr. Ama Boateng", "status": "reviewed", "due_date": "2026-08-15",
         "instructions": "Write a short reflection on how you're feeling since the last visit.", "feedback": "Thanks for the detail — keep this up next week."},
    ]
    return render_template("patient_dashboard.html", current_user=MOCK_PATIENT, active_page="dashboard", tasks=tasks)


@app.route("/tasks/new", methods=["GET", "POST"])
def task_create():
    patients = [{"id": "PAT-01", "name": "Kwesi Owusu"}, {"id": "PAT-02", "name": "Ama Serwaa"}]
    if request.method == "POST":
        flash("Task created.", "success")
        return redirect(url_for("clinician_dashboard"))
    return render_template("task_create.html", current_user=MOCK_CLINICIAN, active_page="task_create", patients=patients)


@app.route("/submit/<task_id>", methods=["GET", "POST"])
def submission(task_id="T1"):
    task = {"id": task_id, "title": "Weekly symptom log", "instructions": "Log your symptoms daily and upload as a .csv by Sunday.",
            "clinician_name": "Dr. Ama Boateng", "due_date": "2026-09-01"}
    if request.method == "POST":
        flash("Submission received.", "success")
        return redirect(url_for("patient_dashboard"))
    return render_template("submission.html", current_user=MOCK_PATIENT, active_page="submission", task=task)


@app.route("/review", methods=["GET", "POST"])
@app.route("/review/<task_id>", methods=["GET", "POST"])
def review(task_id=None):
    queue = [
        {"id": "T1", "patient_name": "Kwesi Owusu", "title": "Weekly symptom log", "submitted_at": "2026-08-27 14:02", "status": "submitted"},
        {"id": "T2", "patient_name": "Ama Serwaa", "title": "Medication adherence sheet", "submitted_at": "2026-08-26 09:11", "status": "submitted"},
    ]
    selected = None
    if task_id:
        selected = {"id": task_id, "patient_name": "Kwesi Owusu", "title": "Weekly symptom log",
                    "instructions": "Log your symptoms daily and upload as a .csv by Sunday.",
                    "note": "Felt better by Thursday.", "file_name": "symptom_log.csv", "file_url": "#",
                    "submitted_at": "2026-08-27 14:02", "status": "submitted", "feedback": None}
    if request.method == "POST":
        flash("Feedback saved.", "success")
        return redirect(url_for("review", task_id=task_id))
    return render_template("review.html", current_user=MOCK_CLINICIAN, active_page="review", queue=queue, selected=selected)


@app.route("/messages", methods=["GET", "POST"])
@app.route("/messages/<thread_id>", methods=["GET", "POST"])
def messages(thread_id=None):
    threads = [
        {"id": "TH1", "other_name": "Kwesi Owusu", "last_message": "Thanks, uploaded it just now.", "unread": True},
        {"id": "TH2", "other_name": "Ama Serwaa", "last_message": "Can I submit a day late?", "unread": False},
    ]
    active_thread = None
    if thread_id:
        active_thread = {"id": thread_id, "other_name": "Kwesi Owusu", "messages": [
            {"from_me": False, "text": "Hi doctor, quick question about the log format.", "sent_at": "10:02 AM"},
            {"from_me": True, "text": "Sure — just list symptoms and severity 1-5 per day.", "sent_at": "10:05 AM"},
            {"from_me": False, "text": "Thanks, uploaded it just now.", "sent_at": "10:20 AM"},
        ]}
    if request.method == "POST":
        return redirect(url_for("messages", thread_id=thread_id))
    return render_template("messages.html", current_user=MOCK_CLINICIAN, active_page="messages", threads=threads, active_thread=active_thread)


@app.route("/analytics")
def analytics():
    summary = {"total_tasks": 46, "completion_rate": 78.3, "avg_review_hours": 5.4, "active_patients": 18}
    status_breakdown = [{"label": "Pending", "count": 9}, {"label": "Submitted", "count": 6}, {"label": "Reviewed", "count": 31}]
    tasks_per_clinician = [{"label": "Dr. Ama Boateng", "count": 22}, {"label": "Dr. Kofi Danso", "count": 15}, {"label": "Dr. Efua Sarpong", "count": 9}]
    return render_template("analytics.html", current_user=MOCK_CLINICIAN, active_page="analytics",
                            summary=summary, status_breakdown=status_breakdown, tasks_per_clinician=tasks_per_clinician)


if __name__ == "__main__":
    app.run(port=5099)
