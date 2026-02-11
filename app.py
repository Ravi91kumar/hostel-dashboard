
from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hostel_secret"

DATA_FILE = "data.xlsx"

def calculate(row):
    total = row.get("Total Payable", 0)
    paid = row.get("Total Paid", 0)
    due = max(total - paid, 0)
    refund = max(paid - total, 0)
    return total, paid, due, refund

def generate_pdf(student):
    styles = getSampleStyleSheet()
    filename = f"bill_{student['Reg No']}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    elements.append(Paragraph("Hostel & Mess Bill", styles["Title"]))
    elements.append(Paragraph(datetime.now().strftime("%d-%b-%Y"), styles["Normal"]))
    elements.append(Spacer(1, 12))

    total, paid, due, refund = calculate(student)

    data = [["Field", "Value"]]
    for k, v in student.items():
        data.append([k, str(v)])

    data += [
        ["Total Payable", total],
        ["Paid", paid],
        ["Due", due],
        ["Refund", refund],
    ]

    table = Table(data, colWidths=[220, 300])
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.black),
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))

    elements.append(table)
    doc.build(elements)
    return filename

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        reg = request.form["reg"]
        dob = request.form["dob"]

        df = pd.read_excel(DATA_FILE)
        s = df[(df["Reg No"]==reg) & (df["DOB"]==dob)]

        if not s.empty:
            session["reg"] = reg
            return redirect("/dashboard")

        return render_template("login.html", error="Invalid login")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "reg" not in session:
        return redirect("/")

    df = pd.read_excel(DATA_FILE)
    student = df[df["Reg No"]==session["reg"]].iloc[0].to_dict()
    totals = calculate(student)

    return render_template("dashboard.html",
                           student=student,
                           totals=totals)

@app.route("/admin", methods=["GET","POST"])
def admin():
    df = pd.read_excel(DATA_FILE)

    if request.method == "POST":
        reg = request.form["reg"]
        field = request.form["field"]
        value = request.form["value"]

        df.loc[df["Reg No"]==reg, field] = value
        df.to_excel(DATA_FILE, index=False)

    return render_template("admin.html",
                           data=df.to_dict(orient="records"))

@app.route("/payment", methods=["POST"])
def payment():
    df = pd.read_excel(DATA_FILE)

    reg = request.form["reg"]
    amount = float(request.form["amount"])

    df.loc[df["Reg No"]==reg, "Total Paid"] += amount
    df.to_excel(DATA_FILE, index=False)

    return redirect("/admin")

@app.route("/export")
def export():
    df = pd.read_excel(DATA_FILE)
    student = df[df["Reg No"]==session["reg"]].iloc[0].to_dict()
    file = generate_pdf(student)
    return send_file(file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
