from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from app.forms import ClientForm
from datetime import datetime

# Ініціалізація Flask-додатка
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Підключення до MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['DatingAgency_Local']

# Головна сторінка
@app.route("/")
def index():
    return render_template("index.html")

# Сторінка клієнтів із фільтрацією, сортуванням та пагінацією
@app.route("/clients/<int:page>")
def clients(page=1):
    per_page = 5
    skip = (page - 1) * per_page

    # Параметри фільтрації та сортування
    sort_by = request.args.get("sort_by", "age")
    gender = request.args.get("gender", "")
    zodiac_sign = request.args.get("zodiac_sign", "")
    age_min = int(request.args.get("age_min", 0))
    age_max = int(request.args.get("age_max", 120))

    # Формування запиту до MongoDB
    query = {}
    if gender:
        query["gender"] = gender
    if zodiac_sign:
        query["zodiac_sign"] = zodiac_sign
    query["age"] = {"$gte": age_min, "$lte": age_max}

    # Отримання клієнтів із бази
    clients_list = list(db.clients.find(query).sort(sort_by, 1).skip(skip).limit(per_page))
    total_clients = db.clients.count_documents(query)
    total_pages = (total_clients + per_page - 1) // per_page

    return render_template("clients.html", clients=clients_list, page=page, total_pages=total_pages, sort_by=sort_by, gender=gender, zodiac_sign=zodiac_sign, age_min=age_min, age_max=age_max)

# Додавання нового клієнта
@app.route("/add_client", methods=["GET", "POST"])
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        new_client = {
            "gender": form.gender.data,
            "registration_date": form.registration_date.data.strftime("%Y-%m-%d"),
            "age": form.age.data,
            "height": form.height.data,
            "weight": form.weight.data,
            "zodiac_sign": form.zodiac_sign.data,
            "self_description": form.self_description.data
        }
        db.clients.insert_one(new_client)
        flash("Client added successfully!", "success")
        return redirect(url_for("clients", page=1))
    return render_template("add_client.html", form=form)

# Редагування клієнта
@app.route("/edit_client/<client_id>", methods=["GET", "POST"])
def edit_client(client_id):
    client = db.clients.find_one({"_id": ObjectId(client_id)})
    
    if "registration_date" in client:
        client["registration_date"] = datetime.strptime(client["registration_date"], "%Y-%m-%d")

    form = ClientForm(data=client)

    if form.validate_on_submit():
        updated_client = {
            "gender": form.gender.data,
            "registration_date": form.registration_date.data.strftime("%Y-%m-%d"),
            "age": form.age.data,
            "height": form.height.data,
            "weight": form.weight.data,
            "zodiac_sign": form.zodiac_sign.data,
            "self_description": form.self_description.data
        }
        db.clients.update_one({"_id": ObjectId(client_id)}, {"$set": updated_client})
        flash("Client updated successfully!", "success")
        return redirect(url_for("clients", page=1))

    return render_template("edit_client.html", form=form, client=client, client_id=client_id)

# Видалення клієнта
@app.route("/delete_client/<client_id>")
def delete_client(client_id):
    db.clients.delete_one({"_id": ObjectId(client_id)})
    flash("Client deleted successfully!", "success")
    return redirect(url_for("clients", page=1))

# Перегляд детальної інформації про клієнта
@app.route("/view_client/<client_id>")
def view_client(client_id):
    client = db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        flash("Client not found!", "danger")
        return redirect(url_for("clients", page=1))
    return render_template("view_client.html", client=client)

# Сторінка зустрічей із пагінацією
@app.route("/meetings/<int:page>")
def meetings(page=1):
    per_page = 5
    skip = (page - 1) * per_page
    meetings_list = list(db.meetings.find().skip(skip).limit(per_page))
    total_meetings = db.meetings.count_documents({})
    total_pages = (total_meetings + per_page - 1) // per_page
    return render_template("meetings.html", meetings=meetings_list, page=page, total_pages=total_pages)

# Додавання нової зустрічі
@app.route("/add_meeting", methods=["GET", "POST"])
def add_meeting():
    if request.method == "POST":
        new_meeting = {
            "client1_id": request.form.get("client1_id"),
            "client2_id": request.form.get("client2_id"),
            "date": request.form.get("date"),
            "status": "planned"
        }
        db.meetings.insert_one(new_meeting)
        flash("Meeting added successfully!", "success")
        return redirect(url_for("meetings", page=1))

    clients_list = list(db.clients.find())
    return render_template("add_meeting.html", clients=clients_list)

# Архів зустрічей
@app.route("/archive")
def archive():
    archive_list = list(db.archive.find())
    return render_template("archive.html", archive=archive_list)

# Архівування зустрічі
@app.route("/archive_meeting/<meeting_id>")
def archive_meeting(meeting_id):
    meeting = db.meetings.find_one({"_id": ObjectId(meeting_id)})
    if meeting:
        db.archive.insert_one({
            "client1_id": meeting["client1_id"],
            "client2_id": meeting["client2_id"],
            "archive_date": meeting["date"]
        })
        db.meetings.delete_one({"_id": ObjectId(meeting_id)})
        flash("Meeting archived successfully!", "success")
    return redirect(url_for("archive"))

# Пошук клієнтів
@app.route("/search_clients", methods=["GET", "POST"])
def search_clients():
    if request.method == "POST":
        gender = request.form.get("gender")
        zodiac_sign = request.form.get("zodiac_sign")
        age_min = int(request.form.get("age_min") or 0)
        age_max = int(request.form.get("age_max") or 100)

        query = {
            "gender": gender if gender else None,
            "zodiac_sign": zodiac_sign if zodiac_sign else None,
            "age": {"$gte": age_min, "$lte": age_max}
        }
        query = {k: v for k, v in query.items() if v}

        clients_list = list(db.clients.find(query))
        return render_template("search_clients.html", clients=clients_list)

    return render_template("search_clients.html", clients=[])
