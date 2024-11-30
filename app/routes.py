from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from app.forms import ClientForm
from datetime import datetime, timedelta
from decorators.role_decorator import role_decorator
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


@app.route("/login")
def login():
    return render_template("login.html")

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
    clients_list = list(db.clients.find(query).sort(
        sort_by, 1).skip(skip).limit(per_page))
    total_clients = db.clients.count_documents(query)
    total_pages = (total_clients + per_page - 1) // per_page

    return render_template("clients.html", clients=clients_list, page=page, total_pages=total_pages, sort_by=sort_by, gender=gender, zodiac_sign=zodiac_sign, age_min=age_min, age_max=age_max)

# Додавання нового клієнта


@app.route("/add_client", methods=["GET", "POST"])
@role_decorator("operator")
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        registration_date = datetime.combine(
            form.registration_date.data, datetime.min.time())
        new_client = {
            "gender": form.gender.data,
            "registration_date": registration_date,
            "age": form.age.data,
            "height": form.height.data,
            "weight": form.weight.data,
            "zodiac_sign": form.zodiac_sign.data,
            "self_description": form.self_description.data,
            "partner_requirements": {
                "zodiac_sign": form.partner_zodiac_sign.data,
                "min_age": form.partner_min_age.data,
                "max_age": form.partner_max_age.data,
                "min_height": form.partner_min_height.data,
                "max_height": form.partner_max_height.data,
                "min_weight": form.partner_min_weight.data,
                "max_weight": form.partner_max_weight.data,
            },
        }
        db.clients.insert_one(new_client)
        flash("Client added successfully!", "success")
        return redirect(url_for("clients", page=1))
    return render_template("add_client.html", form=form)


# Редагування клієнта
@app.route("/edit_client/<client_id>", methods=["GET", "POST"])
@role_decorator("admin")
def edit_client(client_id):
    client = db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for("clients", page=1))

    form = ClientForm()
    if form.validate_on_submit():
        updated_client = {
            "gender": request.form.get("gender"),
            "registration_date": datetime.combine(form.registration_date.data, datetime.min.time()),
            "age": form.age.data,
            "height": form.height.data,
            "weight": form.weight.data,
            "zodiac_sign": form.zodiac_sign.data,
            "self_description": form.self_description.data,
            "partner_requirements": {
                "zodiac_sign": request.form.getlist("partner_zodiac_sign"),
                "min_age": request.form.get("partner_min_age"),
                "max_age": request.form.get("partner_max_age"),
                "min_height": request.form.get("partner_min_height"),
                "max_height": request.form.get("partner_max_height"),
                "min_weight": request.form.get("partner_min_weight"),
                "max_weight": request.form.get("partner_max_weight"),
            },
        }
        db.clients.update_one({"_id": ObjectId(client_id)}, {
                              "$set": updated_client})
        flash("Client updated successfully!", "success")
        return redirect(url_for("clients", page=1))

    form.gender.data = client.get("gender")
    form.registration_date.data = client.get("registration_date")
    form.age.data = client.get("age")
    form.height.data = client.get("height")
    form.weight.data = client.get("weight")
    form.zodiac_sign.data = client.get("zodiac_sign")
    form.self_description.data = client.get("self_description")
    return render_template("edit_client.html", form=form, client=client)

# Видалення клієнта


@app.route("/delete_client/<client_id>", methods=["DELETE"])
@role_decorator("owner")
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

    # Отримуємо всі зустрічі з бази
    meetings_list = list(db.meetings.find().skip(skip).limit(per_page))

    # Завантажуємо деталі клієнтів для кожної зустрічі
    for meeting in meetings_list:
        meeting["client1"] = db.clients.find_one(
            {"_id": ObjectId(meeting["client1_id"])})
        meeting["client2"] = db.clients.find_one(
            {"_id": ObjectId(meeting["client2_id"])})

    total_meetings = db.meetings.count_documents({})
    total_pages = (total_meetings + per_page - 1) // per_page

    return render_template("meetings.html", meetings=meetings_list, page=page, total_pages=total_pages)

# Додавання нової зустрічі


@app.route("/add_meeting", methods=["GET", "POST"])
@role_decorator("operator")
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
@role_decorator("admin")
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

        db.meetings.update_one({"_id": ObjectId(meeting_id)}, {
                               "$set": updated_meeting})

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


@app.route("/delete_meeting/<meeting_id>", methods=["DELETE"])
@role_decorator("owner")
def delete_meeting(meeting_id):
    db.meetings.delete_one({"_id": ObjectId(meeting_id)})
    return jsonify({"message": "meeting deleted successfully"})


@app.route("/resolved_pairs")
def resolved_pairs():
    # Отримати всі пари з архіву
    pairs = list(db.archive.find())

    # Оновити кожну пару з деталями клієнтів
    for pair in pairs:
        pair["client1"] = db.clients.find_one(
            {"_id": ObjectId(pair["client1_id"])})
        pair["client2"] = db.clients.find_one(
            {"_id": ObjectId(pair["client2_id"])})

    # Логування для перевірки даних
    print(f"Знайдено {len(pairs)} пар у архіві.")
    for pair in pairs:
        print(pair)

    return render_template("resolved_pairs.html", pairs=pairs)


@app.route("/meetings_current_month", methods=["GET"])
def meetings_current_month():
    """Відображення зустрічей на поточний місяць."""
    today = datetime.now()
    start_date = today.replace(day=1)
    end_date = (start_date + timedelta(days=31)
                ).replace(day=1) - timedelta(seconds=1)

    # Отримуємо зустрічі за поточний місяць
    meetings = list(db.meetings.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }))

    return render_template("meetings_month.html", meetings=meetings, month="current")


@app.route("/meetings_next_month", methods=["GET"])
def meetings_next_month():
    """Відображення зустрічей на наступний місяць."""
    today = datetime.now()
    start_date = (today.replace(day=1) + timedelta(days=31)).replace(day=1)
    end_date = (start_date + timedelta(days=31)
                ).replace(day=1) - timedelta(seconds=1)

    # Отримуємо зустрічі за наступний місяць
    meetings = list(db.meetings.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }))

    return render_template("meetings_month.html", meetings=meetings, month="next")


@app.route("/clients_by_period", methods=["GET"])
def clients_by_period():
    # Поточна дата
    today = datetime.now()

    # Отримання параметра періоду
    period = request.args.get("period", "last_month")

    if period == "last_month":
        # Розрахунок дат для минулого місяця
        if today.month == 1:  # Січень
            start_date = datetime(today.year - 1, 12, 1)
            end_date = datetime(today.year, 1, 1)
        else:
            start_date = datetime(today.year, today.month - 1, 1)
            end_date = datetime(today.year, today.month, 1)
    elif period == "last_6_months":
        # Розрахунок дат для останніх 6 місяців
        start_date = datetime(today.year, today.month, 1) - timedelta(days=180)
        end_date = today
    else:
        flash("Невірний період!", "danger")
        return redirect(url_for("index"))

    # Запит до бази даних
    clients = list(db.clients.find(
        {"registration_date": {"$gte": start_date, "$lt": end_date}}))

    # Логування
    print(f"Знайдено {len(clients)} клієнтів за період {
          period}: {start_date} - {end_date}")

    return render_template("clients_by_period.html", clients=clients, period=period)


@app.route("/non_missing_partners", methods=["GET"])
def non_missing_partners():
    # Отримання статі з параметрів
    gender = request.args.get("gender", None)

    if not gender:
        # Якщо стать не обрана, повертаємо форму
        return render_template("non_missing_partners.html", partners=[])

    # Запит до MongoDB для клієнтів із обраною статтю
    clients = list(db.clients.find({"gender": gender}))

    # Фільтрація клієнтів, які не пропустили жодної зустрічі
    result = []
    for client in clients:
        meetings = list(db.meetings.find(
            {"$or": [{"client1_id": str(client["_id"])}, {"client2_id": str(client["_id"])}]}))
        if all(meeting["status"] == "completed" for meeting in meetings):
            result.append(client)

    # Логування
    print(f"Знайдено {len(result)} клієнтів, які не пропустили зустрічей.")

    return render_template("non_missing_partners.html", partners=result, gender=gender)


@app.route("/matching_grooms", methods=["GET"])
def matching_grooms():
    # Отримати всіх жінок із бази
    brides = list(db.clients.find({"gender": "female"}))
    results = []

    for bride in brides:
        # Отримання вимог до партнера
        partner_requirements = bride.get("partner_requirements", {})

        # Отримуємо діапазон віку
        age_min = partner_requirements.get("min_age", 0)
        age_max = partner_requirements.get("max_age", 120)

        # Отримуємо діапазон зросту
        height_min = partner_requirements.get("min_height", 0)
        height_max = partner_requirements.get("max_height", 250)

        # Отримуємо діапазон ваги
        weight_min = partner_requirements.get("min_weight", 0)
        weight_max = partner_requirements.get("max_weight", 300)

        # Отримуємо знаки зодіаку
        zodiac_signs = partner_requirements.get("zodiac_signs", [])
        if not isinstance(zodiac_signs, list):  # Переконуємося, що це список
            zodiac_signs = [zodiac_signs]

        # Формуємо запит для пошуку
        query = {
            "gender": "male",
            "age": {"$gte": age_min, "$lte": age_max},
            "height": {"$gte": height_min, "$lte": height_max},
            "weight": {"$gte": weight_min, "$lte": weight_max},
            "zodiac_sign": {"$in": zodiac_signs} if zodiac_signs else {"$exists": True}
        }

        # Підрахунок чоловіків, які відповідають вимогам
        matching_grooms_count = db.clients.count_documents(query)

        # Додаємо результати для нареченої
        results.append({
            "bride": bride.get("self_description", "No description provided"),
            "matching_grooms_count": matching_grooms_count,
        })

    # Відображення результату
    return render_template("matching_grooms.html", results=results)



@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    print(login)
    print(password)
    user = db.Keys.find_one({"login": login, "password": password})
    if user is not None:
        return jsonify({"role": user['role']}), 200
    else:
        return jsonify({"error": "Invalid login or password"}), 401


@app.route('/api/register', methods=['POST'])
@role_decorator("admin")
def register():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    role = data.get('role')
    current_role = request.cookies.get('role')
    user = db.Keys.find_one({"login": login})
    if user is not None:
        return jsonify({"error": "User already exists"}), 409
    if (role == "admin" and current_role != "owner"):
        return jsonify({"error": "Only owner can add admin"}), 403
    db.Keys.insert_one({"login": login, "password": password, "role": role})
    return jsonify({"message": "User registered successfully"}), 201


@app.route('/api/forgot-password', methods=['GET'])
def forgot_password():
    login = request.args.get('login')
    user = db.Keys.find_one({"login": login})
    if user is not None:
        return jsonify({"password": user['password']}), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route("/select_user", methods=["GET"])
def select_user():
    users = list(db.clients.find())  # Отримати список користувачів
    return render_template("select_user.html", users=users)


@app.route("/matches/<user_id>", methods=["GET"])
def matches(user_id):
    user = db.clients.find_one({"_id": ObjectId(user_id)})
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("select_user"))

    # Витягування вимог до партнера
    requirements = user.get("partner_requirements", {})
    query = {
        "age": {"$gte": requirements.get("min_age", 0), "$lte": requirements.get("max_age", 120)},
        "height": {"$gte": requirements.get("min_height", 0), "$lte": requirements.get("max_height", 250)},
        "weight": {"$gte": requirements.get("min_weight", 0), "$lte": requirements.get("max_weight", 300)},
        "zodiac_sign": {"$in": requirements.get("zodiac_sign", [])},
        "gender": "male" if user["gender"] == "female" else "female"
    }

    matches = list(db.clients.find(query))
    return render_template("matches.html", user=user, matches=matches)


@app.route('/canceled_meetings', methods=["GET"])
def canceled_meetings():
    result = list(db.meetings.find({"status": "cancelled"}))
    return render_template("canceled_meetings.html", meetings=result)


@app.route('/completed_meetings', methods=["GET"])
def completed_meetings():
    result = list(db.meetings.find({"status": "completed"}))
    return render_template("completed_meetings.html", meetings=result)