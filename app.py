from flask import Flask, flash, redirect, render_template, request, session, send_file, after_this_request
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_apscheduler import APScheduler
from functools import wraps
import csv
import datetime
from cs50 import SQL
import tempfile
import os

# Configure application
app = Flask(__name__)
scheduler = APScheduler()

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Kolkata'


app.config.from_object(Config())
scheduler.init_app(app)
scheduler.start()

db = SQL("sqlite:///project.db")


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


global school


def create_tables(school):
    """Create necessary tables for a new user."""
    # Create buses table
    db.execute(f"""
    CREATE TABLE IF NOT EXISTS {school}_buses (
        userid INT NOT NULL,
        RouteNo INT NOT NULL PRIMARY KEY,
        RegistrationNo TEXT NOT NULL,
        NameOfDriver TEXT,
        NameOfConductor TEXT,
        NumberOfStudents INT,
        FOREIGN KEY (userid) REFERENCES users(id)

        )
        """)

    # Create daily_records table
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS {school}_maintain_records (
            userid INT NOT NULL,
            today_date DATE,
            RouteNo INT NOT NULL,
            out_time TIME,
            out_odometer INT,
            students_in INT,
            in_time TIME,
            in_odometer INT,
            out_flag INT,
            students_out INT,
            trip_no INT,
            FOREIGN KEY (userid) REFERENCES users(id)
            )
            """)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Ensure username was submitted
        if not username:
            return apology("Username not provided", 400)

        # Ensure password was submitted
        if not password:
            return apology("Password not provided", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = :username", username=username)
        # rows = [{"id": 1, "username": "test", "hash": generate_password_hash("password")}]

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session['username'] = rows[0]['username']
        session['school'] = rows[0]['school']

        # Redirect user to home page
        flash("Logged In!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    flash("Logged out!")
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        school = request.form.get("schoolname").replace(" ", "_")
        # Ensure username was submitted
        if not username:
            return apology("Inalid username", 400)

        # Ensure password was submitted
        if not password:
            return apology("Invalid password", 400)

        # Ensure confirmation was submitted
        if not confirm:
            return apology("Invalid password confirmation", 400)

        # Ensure password and confirmation match
        if password != confirm:
            return apology("Passwords dont match", 400)

        if not school:
            return apology("No school name provided", 400)
        # Hash user's password
        hash = generate_password_hash(request.form.get("password"))

        # Insert the new user into the database
        rows = db.execute(
            "SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) > 0:
            return apology("Username already exists", 400)

        db.execute("INSERT INTO users (username, hash, school) VALUES (:username, :hash, :school)",
                   username=username,
                   hash=hash,
                   school=school)

        create_tables(school)

        # Redirect user to home page
        flash("Succesfully registered! Please login using your credentials")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/")
@login_required
def index():
    """Show overview of buses and their maintenance records"""

    # Retrieve the school name from the session
    school = session["school"]

    if not school:
        return apology("No school information available", 400)

    # Format the school name to match the table names
    school = school.replace(" ", "_")

    # Fetch data from school-specific tables
    buses = db.execute(
        f"SELECT * FROM {school}_buses WHERE userid = :user_id", user_id=session["user_id"])
    records = db.execute(f"""
        SELECT r.*, b.RegistrationNo, b.NameOfDriver, b.NameOfConductor, b.NumberOfStudents, b.RouteNo
        FROM {school}_maintain_records r
        JOIN {school}_buses b ON r.RouteNo = b.RouteNo
        WHERE r.userid = :user_id
    """, user_id=session["user_id"])

    return render_template("index.html", buses=buses, records=records)


def delete_records():

    school = session["school"]  # Use default_school if no school in session
    db.execute(f"DELETE FROM {school}_maintain_records WHERE date(today_date) < date('now')")


@app.route("/add_bus", methods=["POST", "GET"])
@login_required
def add_bus():

    if request.method == "POST":
        registration = request.form.get("registration_no").upper()
        driver = request.form.get("driver_name").title()
        conductor = request.form.get("conductor_name").title()
        students_num = request.form.get("number_of_students")
        route = request.form.get("route_no")
        school = session["school"].replace(" ", "_")

        if not registration:
            return apology("No registration number provided", 400)

        if not driver:
            return apology("No driver name provided", 400)

        if not conductor:
            return apology("No conductor name provided", 400)

        if not students_num:
            return apology("Number of students not provided", 400)

        if not route:
            return apology("No route number provided", 400)

        if not school:
            return apology("School doesn't exist", 400)

        db.execute(f"""
                INSERT INTO {school}_buses (RegistrationNo, NameOfDriver, NameOfConductor, NumberOfStudents, RouteNo, userid)
                VALUES (:registration_no, :driver_name, :conductor_name, :number_of_students, :route_no, :user_id)
            """,
                   registration_no=registration,
                   driver_name=driver,
                   conductor_name=conductor,
                   number_of_students=students_num,
                   route_no=route,
                   user_id=session["user_id"])

        flash("Bus added succesfully!")
        return redirect("/")
    else:
        return render_template("add_bus.html")


@app.route("/remove_bus", methods=["POST", "GET"])
@login_required
def remove_bus():
    if request.method == "POST":
        identifier = request.form.get("identifier").lower()
        value = request.form.get("value")
        school = session["school"]

        if not identifier:
            return apology("Choose valid deletion method", 400)
        if not value:
            return apology("Value is required", 400)

        # Check if the bus exists
        bus_exists = None
        if identifier == "route_no":
            bus_exists = db.execute(f"SELECT * FROM {school}_buses WHERE RouteNo = :value AND userid = :user_id",
                                    value=value, user_id=session["user_id"])
        if identifier == "registration_no":
            bus_exists = db.execute(f"SELECT * FROM {school}_buses WHERE RegistrationNo = :value AND userid = :user_id",
                                    value=value, user_id=session["user_id"])
        else:
            return apology("Invalid identifier", 400)

        if not bus_exists:
            return apology("Bus not found", 400)

        # Remove the bus
        try:
            if identifier == "route_no":
                db.execute(f"DELETE FROM {school}_buses WHERE RouteNo = :value AND userid = :user_id",
                           value=value, user_id=session["user_id"])
            if identifier == "registration_no":
                db.execute(f"DELETE FROM {school}_buses WHERE RegistrationNo = :value AND userid = :user_id",
                           value=value, user_id=session["user_id"])

            flash("Bus successfully removed", "success")
            return redirect("/")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect("/remove_bus")

    return render_template("remove_bus.html")


@app.route("/update_bus", methods=["POST", "GET"])
@login_required
def update_bus():
    if request.method == "POST":
        identifier = request.form.get("identifier").lower()
        value = request.form.get("value")
        new_registration_no = request.form.get("new_registration_no")
        new_driver = request.form.get("NameOfDriver")
        new_conductor = request.form.get("NameOfConductor")
        new_number_of_students = request.form.get("NumberOfStudents")
        new_route_number = request.form.get("new_route_no")
        school = session["school"]

        if not identifier or not value:
            flash("Identifier and value are required!")
            return redirect("/update_bus")

        # Check if the bus exists
        bus_exists = None
        if identifier == "route_no":
            bus_exists = db.execute(
                f"SELECT * FROM {school}_buses WHERE RouteNo = :value AND userid = :user_id",
                value=value,
                user_id=session["user_id"],
            )
        elif identifier == "registration_no":
            value = value.upper()
            bus_exists = db.execute(
                f"SELECT * FROM {school}_buses WHERE RegistrationNo = :value AND userid = :user_id",
                value=value,
                user_id=session["user_id"],
            )
        else:
            flash("Invalid identifier!")
            return redirect("/update_bus")

        print(f"Bus exists: {bus_exists}")

        if not bus_exists:
            flash("Bus not found!")
            return redirect("/update_bus")

        update_fields = {}
        if new_registration_no:
            update_fields["RegistrationNo"] = new_registration_no.upper()
        if new_driver:
            update_fields["NameOfDriver"] = new_driver.title()
        if new_conductor:
            update_fields["NameOfConductor"] = new_conductor.title()
        if new_number_of_students:
            update_fields["NumberOfStudents"] = new_number_of_students
        if new_route_number:
            update_fields["RouteNo"] = new_route_number

        if not update_fields:
            flash("No new values provided for update!")
            return redirect("/update_bus")

        set_clause = ", ".join(f"{key} = :{key}" for key in update_fields.keys())
        update_fields["value"] = value
        update_fields["user_id"] = session["user_id"]

        print(f"Update fields: {update_fields}")

        try:
            if identifier == "route_no":
                db.execute(
                    f"UPDATE {school}_buses SET {set_clause} WHERE RouteNo = :value AND userid = :user_id",
                    **update_fields,
                )
            elif identifier == "registration_no":
                db.execute(
                    f"UPDATE {school}_buses SET {set_clause} WHERE RegistrationNo = :value AND userid = :user_id",
                    **update_fields,
                )

            flash("Bus details successfully updated!")
            return redirect("/")
        except Exception as e:
            flash(f"An error occurred: {e}")
            print(f"Exception: {e}")
            return redirect("/update_bus")

    return render_template("update_bus.html")

@app.route("/maintain_records", methods=["POST", "GET"])
@login_required
def maintain_records():
    if request.method == "POST":
        choice = request.form.get("choice")
        route_no = request.form.get("route_no")
        school = session["school"]
        user_id = session["user_id"]

        if not choice or not route_no:
            flash("choice and route number are required", "error")
            return redirect("/maintain_records")

        try:
            today_date = datetime.date.today()

            if choice.upper() == "O":
                out_odometer = request.form.get("out_odometer")
                students_out = request.form.get("students_out")

                if not out_odometer or not students_out:
                    flash(
                        "Odometer reading and number of students are required!", 400)
                    return redirect("/maintain_records")

                # Check if the bus is already outside
                bus_outside = db.execute("SELECT * FROM {}_maintain_records WHERE RouteNo = :route_no AND out_flag = 1".format(school),
                                         route_no=route_no)
                if bus_outside:
                    flash("Bus is already outside the premises")
                    return redirect("/maintain_records")

                out_time = datetime.datetime.now().strftime('%H:%M:%S')
                trip_no = db.execute("SELECT MAX(trip_no) FROM {}_maintain_records WHERE RouteNo = :route_no AND today_date = :today_date".format(school),
                                     route_no=route_no, today_date=today_date)
                trip_no_new = 1 if trip_no[0]['MAX(trip_no)'] is None else trip_no[0]['MAX(trip_no)'] + 1

                db.execute("INSERT INTO {}_maintain_records (RouteNo, today_date, students_out, out_odometer, out_time, out_flag, trip_no, userid) VALUES (:route_no, :today_date, :students_out, :out_odometer, :out_time, 1, :trip_no, :user_id)".format(school),
                           route_no=route_no, today_date=today_date, students_out=students_out, out_odometer=out_odometer, out_time=out_time, trip_no=trip_no_new, user_id=user_id)

            elif choice.upper() == "I":
                in_odometer = request.form.get("in_odometer")
                students_in = request.form.get("students_in")

                if not in_odometer or not students_in:
                    flash(
                        "Odometer reading and number of students are required!")
                    return redirect("/maintain_records")

                # Check if the bus is actually outside
                bus_outside = db.execute("SELECT * FROM {}_maintain_records WHERE RouteNo = :route_no AND out_flag = 1".format(school),
                                         route_no=route_no)
                if not bus_outside:
                    flash("Bus is already inside!")
                    return redirect("/maintain_records")

                in_time = datetime.datetime.now().strftime('%H:%M:%S')
                db.execute("UPDATE {}_maintain_records SET students_in = :students_in, in_odometer = :in_odometer, in_time = :in_time, out_flag = 0 WHERE RouteNo = :route_no AND out_flag = 1".format(school),
                           students_in=students_in, in_odometer=in_odometer, in_time=in_time, route_no=route_no)

            flash("Bus record successfully updated!")
            return redirect("/maintain_records")

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect("/maintain_records")

    return render_template("maintain_records.html", update_another=False)


@app.route("/pending_buses")
@login_required
def pending_buses():

    try:
        school = session["school"]
        user_id = session["user_id"]

        # Query to get buses with out_flag = 1 (pending buses) by joining the two tables
        buses = db.execute(f"""
            SELECT
                b.RouteNo,
                b.NameOfDriver,
                b.NameOfConductor,
                b.RegistrationNo
            FROM
                {school}_buses b
            JOIN
                {school}_maintain_records r
            ON
                b.RouteNo = r.RouteNo
            WHERE
                r.out_flag = 1 AND b.userid = :user_id
        """, user_id=user_id)

        return render_template("pending_buses.html", buses=buses)

    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect("/")

@app.route("/report")
@login_required
def report():
    return render_template("download_report.html")

@app.route("/download_report")
@login_required
def download_report():
    """Download daily report."""
    fields = ['Route No', 'Trip No', 'Students In', 'Students Out', 'Dist. Covered', 'Out Time', 'In Time']
    school = session["school"]
    userid = session["user_id"]
    today = datetime.date.today()

    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        filename = temp_file.name

        # Query the database
        query = f"""
        SELECT
            RouteNo AS "Route No",
            trip_no AS "Trip No",
            students_in AS "Students In",
            students_out AS "Students Out",
            ABS(out_odometer - in_odometer) AS "Dist. Covered",
            out_time AS "Out Time",
            in_time AS "In Time"
        FROM {school}_maintain_records
        WHERE today_date = current_date AND out_flag = 0 AND userid = :userid
        ORDER BY RouteNo
        """
        records = db.execute(query, userid=userid)

        # Write the data to a CSV file
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            for record in records:
                csvwriter.writerow([record[field] for field in fields])


        @after_this_request
        def remove_file(response):
            try:
                os.remove(filename)
            except Exception as error:
                app.logger.error(f"Error removing file: {error}")
            return response

        return send_file(filename, as_attachment=True, download_name=f"{today}_daily_record.csv")

    except Exception as e:
        flash(f"An error occurred while generating the report: {e}", "error")
        print(f"Error: {e}")
        return redirect("/")


scheduler.add_job(id='Delete Records', func=delete_records,
                  trigger='cron', hour=0)  # Runs every day at midnight



