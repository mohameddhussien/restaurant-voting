from flask import Flask, render_template, request, redirect, url_for, session, flash
import db
import utils
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import validators
import os


voting = Flask(__name__)
connection = db.connect_to_database()
voting.secret_key = "u29h3e29h2e91h2e9w2jmqw09h23jq9hq"
limiter = Limiter(
    app=voting, key_func=get_remote_address, default_limits=["10 per minute"]
)


# @app.route("/home")
# def restaurant():
#     if 'username' in session:
#         return render_template("restaurant.html", restaurants=db.get_all_restaurants(connection), username= session['username'])


@voting.route("/home", methods=["GET", "POST"])
def restaurant():
    if "username" in session:
        if request.method == "POST":
            # searchtext = request.args.get('search')
            searchtext = request.form["search"]
            results = db.search_restaurants(connection, searchtext)
            # print('searching..')
            return render_template(
                "restaurant.html", restaurants=results, username=session["username"]
            )
        return render_template(
            "restaurant.html",
            restaurants=db.get_all_restaurants(connection),
            username=session["username"],
        )
    return redirect(url_for(login))


@voting.route("/restaurant/<restaurant_id>", methods=["GET", "POST"])
def getrestaurant(restaurant_id):
    if request.method == "POST":
        review = request.form["review"]
        try:
            rating = int(request.form["rating"])
        except:
            flash("Rating from 0-10", "danger")
            return render_template(
                "view-restaurant.html",
                restaurant=db.get_restaurant(connection, restaurant_id),
                reviews=db.get_reviews_for_restaurant(connection, restaurant_id),
            )

        if rating > 10 or rating < 0:
            flash("Rating out of 10!", "danger")
            return render_template(
                "view-restaurant.html",
                restaurant=db.get_restaurant(connection, restaurant_id),
                reviews=db.get_reviews_for_restaurant(connection, restaurant_id),
            )
        user_id = session["user_id"]
        db.add_review(connection, user_id, restaurant_id, rating, review)
        return redirect(url_for("getrestaurant", restaurant_id=restaurant_id))
    else:
        return render_template(
            "view-restaurant.html",
            restaurant=db.get_restaurant(connection, restaurant_id),
            reviews=db.get_reviews_for_restaurant(connection, restaurant_id),
        )


@voting.route("/remove-restaurant/<restaurant_id>")
def remove_restaurant(restaurant_id):
    db.RemoveRestaurant(connection, restaurant_id)
    return redirect(url_for("restaurant"))


@voting.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["emailorUsername"]
        username = request.form["emailorUsername"]
        password = request.form["password"]

        user = db.get_user(connection, email, username)

        if db.seed_admin_user(username, password):
            session["username"] = username
            # session['user_id'] = user[0]
            return render_template(
                "restaurant.html",
                restaurants=db.get_all_restaurants(connection),
                username=session["username"],
            )

        if user:
            if utils.is_password_match(password, user[5]):
                session["username"] = user[4]
                session["user_id"] = user[0]
                return redirect(url_for("restaurant"))
            else:
                flash("Password does not match!", "danger")
                return render_template("login.html")

        else:
            flash("Invalid email or password!", "danger")
            return render_template("login.html")

    return render_template("login.html")


@voting.route("/signup", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        if not utils.is_strong_password(password):
            flash(
                "Sorry You Entered a weak Password Please Choose a stronger one",
                "danger",
            )
            return render_template("signup.html")

        user = db.get_user(connection, email, username)
        if user:
            flash("Username or Email already exists. Please try again !", "danger")
            return render_template("signup.html")

        else:
            db.add_user(connection, first_name, last_name, email, username, password)
            return redirect(url_for("login"))

    return render_template("signup.html")


@voting.route("/logout")
def logout():
    session.pop("username", None)

    session.pop("user_id", None)
    return redirect(url_for("login"))


# @app.route("/admin")
# def admin():
#     if request.method == "GET":
#         return render_template("admin.html")


@voting.route("/UploadRestaurant", methods=["GET", "POST"])
def uploadRest():
    if request.method == "POST":
        try:
            if not "username" in session:
                flash("You Are Not Logged In", "danger")
                return redirect(url_for("login"))
            if session["username"] != "admin":
                flash("Unauthorized user..", "danger")
                return redirect(url_for("restaurant"))

            restaurant_image = request.files["image"]
            if not restaurant_image or restaurant_image.filename == "":
                flash("Image Is Required", "danger")
                return render_template("UploadRestaurant.html")

            if not (
                validators.allowed_file(restaurant_image.filename)
            ) or not validators.allowed_file_size(restaurant_image):
                flash("Invalid File is Uploaded", "danger")
                return render_template("UploadRestaurant.html")

            title = request.form["title"]
            description = request.form["description"]
            if len(description) > 40:
                description = description[0:40] + "..."

            image_url = f"uploads/{restaurant_image.filename}"
            restaurant_image.save(os.path.join("static", image_url))

            db.add_restaurant(connection, title, description, image_url)
        except:
            print("ex")
        return redirect(url_for("restaurant"))
    return render_template("UploadRestaurant.html")


@voting.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    db.init_db(connection)
    db.init_restaurant(connection)
    db.init_reviews(connection)
    voting.run(debug=True, host='192.168.1.33')
