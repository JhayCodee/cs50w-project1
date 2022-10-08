import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['JSON_SORT_KEYS'] = False #para que no ordene los diccionarios
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#maneja errores 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#Ruta principal
@app.route("/", methods=["GET", "POST"])
def index():

    if 'user_id' in session: # verifica si el usuario esta logueado

        # selecciona el nombre del usuario
        username = db.execute("SELECT username FROM users WHERE id = :id", {"id": session['user_id']}).fetchone()[0]

        if request.method == "POST":

            # obtiene la busqueda del usuario
            search = request.form.get("search").lstrip(' ').rstrip(' ') # elimina espacios en blanco al inicio y al final

            if not search:
                return render_template("index.html", user=username) 

            else:
                # consulta a la base de datos por isbn, titulo o autor ignorando el case sensitive (ilike)
                books = db.execute("SELECT * FROM books WHERE isbn ILIKE :search OR title ILIKE :search OR author ILIKE :search", 
                {"search": f"%{search}%"}).fetchall()
                
                return render_template("index.html", books=books, user=username)

        else:
            #isbn='080213825X'
            # response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()
            # print(response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"])
            return render_template("index.html", user=username)

    else:
        return redirect(url_for('login'))


''' Books'''
@app.route("/book/<string:book_isbn>", methods=["GET", "POST"])
def book(book_isbn):
    
    # verifica si el usuario esta logueado
    if 'user_id' in session: 

        username = db.execute("SELECT username FROM users WHERE id = :id", {"id": session['user_id']}).fetchone()[0]

        if request.method == "GET":
            
            # busca el libro por isbn en la base de datos
            book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()

            # si el libro no existe en la base de datos retorna 404
            if book is None:
                return render_template("404.html"), 404

            else:

                # consulta a la api de google books por el isbn del libro
                response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+book_isbn).json()

                # busca si existe un review del usuario logueado
                user_review = db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id",
                {"book_id": book.id, "user_id": session['user_id']}).fetchone()
                
                # verifica que todo este bien con la respuesta de la api
                try:
                    img = response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
                    description = response["items"][0]["volumeInfo"]["description"]
                    average_rating = response["items"][0]["volumeInfo"]["averageRating"]
                    ratingsCount = response["items"][0]["volumeInfo"]["ratingsCount"]
                except:
                    img = "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/5f6a7e32906eb1d5f22a4508cfdc7509~c5_720x720.jpeg?x-expires=1665284400&x-signature=FpnuaQ%2F8BQzYMVDLvr3RlvsAUZ0%3D"
                    description = "No hay"
                    average_rating = "No hay"
                    ratingsCount = "No hay"

                # context donde almacenamos los datos del libro, de la base de datos y de la api
                context = {
                    "book": book,
                    "img" : img,
                    "description": description,
                    "average_rating": average_rating,
                    "ratingsCount": ratingsCount,
                    "isReview": True, #flag para las reviews de los usuarios
                    "form": False   #flag para el formulario de reviews
                }

                if user_review is None:
                    context["form"] = True

                # buscar todas las reviews
                reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", 
                {"book_id": book.id}).fetchall()
                
                users = db.execute("SELECT id, username FROM users ").fetchall()

                if reviews is None:
                    context["isReview"] = False
                else:                                                                                                                 
                    context["reviews"] = reviews

                # validaciones locas xD (activa y desactiva form y comentarios)
                try:

                    if 'message' in request.args:
                        message = request.args.get('message')

                        if user_review is None:
                            context["form"] = True
                        else:
                            context["form"] = False
                            context["reviews"] = reviews
                    else:
                        message = False

                except:
                    message = False

               
                return render_template("book.html", **context, user=username, users=users, message=message)

        elif request.method == "POST":

            '''
                buscar el libro en bd
                ver si el user tiene una review en el libro
                cargar reviews si hay
            '''

            review = request.form["review"].lstrip(' ')
            rating = request.form["rating"]
            
            try:
                rating = int(rating)
                print(rating)
            except:
                print("no es un numero")
                return redirect(url_for('book', book_isbn=book_isbn)) 


            if not review or not rating:
                print("espacios en blanco")
                return redirect(url_for('book', book_isbn=book_isbn)) 

            else:

                # busca el libro en la base de datos
                book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()

                #verificar si el usuario ya hizo un review
                user_review = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", 
                {"user_id": session['user_id'], "book_id": book.id}).fetchone()

                if user_review is None:
                    #guardar el review
                    db.execute("INSERT INTO reviews (review, book_id, user_id, rating) VALUES (:review, :book_id, :user_id, :rating)",
                    {
                        "review": review,
                        "book_id": book.id,  
                        "user_id": session['user_id'], 
                        "rating": rating
                    })

                    db.commit()
                    return redirect(url_for('book', book_isbn=book_isbn))
                
                else:
                    return redirect(url_for('book', book_isbn=book_isbn))  
        
    else:
        return redirect(url_for('login'))
        
@app.route("/api/<string:book_isbn>")
def api(book_isbn):

    if request.method == "GET":

        # busca el libro por isbn en la base de datos
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()

        # si el libro no existe en la base de datos retorna 404
        if book is None:
            return render_template("404.html") ,404

        # verifica si el libro tiene reviews y puntaje
        try:
            review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchone()[0]
            average_score = db.execute("SELECT AVG(rating) FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchone()[0]
            average_score = round(average_score, 1)
        except:
            review_count = 0
            average_score = 0

        # diccionario con los datos del libro para retornar en formato json
        book_api = {
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": review_count,
            "average_score": average_score
        }

        return jsonify(book_api) 


''' LOGIN '''
@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":

        # obtener los datos del formulario
        username = request.form.get("username").lstrip(' ')
        password = request.form.get("password")
        
        # verificar que los campos no esten vacios
        if not username or not password:
            print("campos vacios")
            return render_template("login.html", message="Porfavor rellene los campos vacios")
        
        else:
            # buscar el usuario en la base de datos (si existe)
            if db.execute("SELECT * FROM users WHERE username = :username", 
                        {"username": username}).rowcount == 0:

                return render_template("login.html", message="El usuario no existe")

            else:
                # buscar el usuario en la base de datos
                user = db.execute("SELECT * FROM users WHERE username = :username", 
                                {"username": username}).fetchone()

                # verificar la contraseña
                if check_password_hash(user.password, password):
                    session["user_id"] = user.id
                    print("usuario logueado")
                    return redirect(url_for("index"))

                else:
                    return render_template("login.html", message="La contraseña es incorrecta")
    else:
        return render_template("login.html")


''' REGISTER '''
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # obtiene los datos del formulario
        username = request.form.get("username").lstrip(' ')
        password = request.form.get("password")
        cpassword = request.form.get("cf-password")

        # verifica que los campos no esten vacios
        if not username or not password or not cpassword:
            print("falta informacion")
            return render_template("register.html", message="Porfavor rellene los campos vacios")
        
        else:
            # verifica que las contraseñas coincidan
            if password == cpassword:
                # verifica que el usuario no exista
                if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 0:
                
                    '''Guardar en la base de datos'''
                    hash = generate_password_hash(password)

                    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                            {"username": username, "password": hash})
                    db.commit()

                    # guarda el id del usuario en la sesion
                    user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
                    session["user_id"] = user.id
                    print("usuario registrado")
                    
                    return redirect("/")
                else:
                    return render_template("register.html", message="El nombre de usuario ya está en uso, seleccione otro")

            else:
                return render_template("register.html", message="Las contraseñas no coinciden")

    else:
        return render_template("register.html")


''' LOGOUT '''
@app.route("/logout")
def logout():
    # limpia la sesion y redirige a la pagina de login
    session.clear()
    return redirect(url_for("index"))


