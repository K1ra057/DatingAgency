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
        # Преобразуем дату регистрации из datetime.date в datetime.datetime
        registration_date = datetime.combine(form.registration_date.data, datetime.min.time())

        new_client = {
            "gender": form.gender.data,
            "registration_date": registration_date,
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

    # Перевіряємо формат поля "registration_date"
    if "registration_date" in client:
        # Якщо це рядок, перетворюємо його в datetime
        if isinstance(client["registration_date"], str):
            client["registration_date"] = datetime.strptime(client["registration_date"], "%Y-%m-%d")
        # Якщо це об'єкт типу datetime.date, конвертуємо його в datetime.datetime
        elif isinstance(client["registration_date"], datetime):
            client["registration_date"] = client["registration_date"]

    form = ClientForm(data=client)

    if form.validate_on_submit():
        # Преобразуем дату в datetime.datetime
        registration_date = datetime.combine(form.registration_date.data, datetime.min.time())

        updated_client = {
            "gender": form.gender.data,
            "registration_date": registration_date,
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
@app.route("/meetings/<int:page>")
def meetings(page=1):
    per_page = 5
    skip = (page - 1) * per_page

    # Отримуємо всі зустрічі з бази
    meetings_list = list(db.meetings.find().skip(skip).limit(per_page))

    # Завантажуємо деталі клієнтів для кожної зустрічі
    for meeting in meetings_list:
        meeting["client1"] = db.clients.find_one({"_id": ObjectId(meeting["client1_id"])})
        meeting["client2"] = db.clients.find_one({"_id": ObjectId(meeting["client2_id"])})

    total_meetings = db.meetings.count_documents({})
    total_pages = (total_meetings + per_page - 1) // per_page

    return render_template("meetings.html", meetings=meetings_list, page=page, total_pages=total_pages)

# Додавання нової зустрічі
@app.route("/add_meeting", methods=["GET", "POST"])
def add_meeting():
    if request.method == "POST":
        # Отримання даних із форми
        client1_id = request.form.get("client1_id")
        client2_id = request.form.get("client2_id")
        date_str = request.form.get("date")
        
        try:
            # Перетворення дати з рядка у формат datetime
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for("add_meeting"))

        new_meeting = {
            "client1_id": client1_id,
            "client2_id": client2_id,
            "date": date,  # Зберігаємо дату у форматі datetime
            "status": "planned"
        }

        # Збереження зустрічі в MongoDB
        db.meetings.insert_one(new_meeting)
        flash("Meeting added successfully!", "success")
        return redirect(url_for("meetings", page=1))

    # Завантаження клієнтів для форми створення зустрічі
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

# Сторінка перегляду клієнтів за кварталом
@app.route("/clients_by_quarter", methods=["GET"])
def clients_by_quarter():
    quarter = request.args.get("quarter", None)

    if not quarter:
        return render_template("clients_by_quarter.html", clients=[], quarter=None)

    try:
        quarter = int(quarter)
    except ValueError:
        flash("Invalid quarter value!", "danger")
        return redirect(url_for("clients_by_quarter"))

    current_year = datetime.now().year
    if quarter == 1:
        start_date = datetime(current_year, 1, 1)
        end_date = datetime(current_year, 3, 31)
    elif quarter == 2:
        start_date = datetime(current_year, 4, 1)
        end_date = datetime(current_year, 6, 30)
    elif quarter == 3:
        start_date = datetime(current_year, 7, 1)
        end_date = datetime(current_year, 9, 30)
    elif quarter == 4:
        start_date = datetime(current_year, 10, 1)
        end_date = datetime(current_year, 12, 31)
    else:
        flash("Invalid quarter!", "danger")
        return redirect(url_for("clients_by_quarter"))

    clients_in_quarter = list(db.clients.find({
        "registration_date": {"$gte": start_date, "$lte": end_date}
    }))

    if not clients_in_quarter:
        flash("No clients found for this quarter.", "warning")

    return render_template("clients_by_quarter.html", clients=clients_in_quarter, quarter=quarter)

@app.route("/edit_meeting/<meeting_id>", methods=["GET", "POST"])
def edit_meeting(meeting_id):
    # Отримання зустрічі з бази даних
    meeting = db.meetings.find_one({"_id": ObjectId(meeting_id)})
    if not meeting:
        flash("Meeting not found!", "danger")
        return redirect(url_for("meetings", page=1))

    # Отримання всіх клієнтів для заповнення форми
    clients_list = list(db.clients.find())

    if request.method == "POST":
        # Отримання даних із форми
        client1_id = request.form.get("client1_id")
        client2_id = request.form.get("client2_id")
        date_str = request.form.get("date")
        status = request.form.get("status")

        try:
            # Конвертація дати з рядка у формат datetime
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for("edit_meeting", meeting_id=meeting_id))

        # Оновлення даних зустрічі
        updated_meeting = {
            "client1_id": client1_id,
            "client2_id": client2_id,
            "date": date,
            "status": status
        }

        db.meetings.update_one({"_id": ObjectId(meeting_id)}, {"$set": updated_meeting})

        # Якщо статус змінено на "completed", перенесення в архів
        if status == "completed":
            db.archive.insert_one({
                "client1_id": client1_id,
                "client2_id": client2_id,
                "archive_date": date
            })
            # Видалення завершеної зустрічі з активних
            db.meetings.delete_one({"_id": ObjectId(meeting_id)})

        flash("Meeting updated successfully!", "success")
        return redirect(url_for("meetings", page=1))

    return render_template("edit_meeting.html", meeting=meeting, clients=clients_list)

@app.route("/resolved_pairs")
def resolved_pairs():
    # Отримати всі пари з архіву
    pairs = list(db.archive.find())

    # Оновити кожну пару з деталями клієнтів
    for pair in pairs:
        pair["client1"] = db.clients.find_one({"_id": ObjectId(pair["client1_id"])})
        pair["client2"] = db.clients.find_one({"_id": ObjectId(pair["client2_id"])})

    # Логування для перевірки даних
    print(f"Знайдено {len(pairs)} пар у архіві.")
    for pair in pairs:
        print(pair)

    return render_template("resolved_pairs.html", pairs=pairs)
