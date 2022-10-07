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
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#maneja errores 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/", methods=["GET", "POST"])
def index():

    if 'user_id' in session: # verifica si el usuario esta logueado

        if request.method == "POST":

            search = request.form.get("search")

            if not search:
                return render_template("index.html", message="mensaje en blanco") 

            else:
                # consulta a la base de datos por isbn, titulo o autor ignorando el case sensitive (ilike)
                books = db.execute("SELECT * FROM books WHERE isbn ILIKE :search OR title ILIKE :search OR author ILIKE :search", 
                {"search": f"%{search}%"}).fetchall()
                
                return render_template("index.html", books=books, f=True)

        else:
            #isbn='080213825X'
            # response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()
            # print(response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"])
            return render_template("index.html")

    else:
        return redirect(url_for('login'))


''' Books'''
@app.route("/book/<string:book_isbn>", methods=["GET", "POST"])
def book(book_isbn):
    
    # verifica si el usuario esta logueado
    if 'user_id' in session: 

        if request.method == "GET":
            
            # busca el libro por isbn en la base de datos
            book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()

            # si el libro no existe en la base de datos retorna 404
            if book is None:
                return "404"

            else:

                # consulta a la api de google books por el isbn del libro
                response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+book_isbn).json()

                # busca si existe un review del usuario logueado
                user_review = db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id",
                {"book_id": book.id, "user_id": session['user_id']}).fetchone()
                
                # context donde almacenamos los datos del libro, de la base de datos y de la api
                context = {
                    "book": book,
                    "img" : response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"],
                    "description": response["items"][0]["volumeInfo"]["description"],
                    "isReview": True, #flag para las reviews de los usuarios
                    "form": False   #flag para el formulario de reviews
                }

                if user_review is None:
                    context["form"] = True

                # buscar todas las reviews
                reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", 
                {"book_id": book.id}).fetchall()

                if reviews is None:
                    context["isReview"] = False
                else:                                                                                                                 
                    context["reviews"] = reviews
                
               
                return render_template("book.html", **context)

        elif request.method == "POST":

            '''
                buscar el libro en bd
                ver si el user tiene una review en el libro
                cargar reviews si hay
            '''

            review = request.form["review"]
            rating = request.form["rating"]
            try:
                rating = int(rating)
                print(rating)
            except:
                return "Rating no valido"


            if not review or not rating:
                return "Espacios en blanco"
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

        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()

        if book is None:
            return "404"
        
        review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchone()[0]
        average_score = db.execute("SELECT AVG(rating) FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchone()[0]
        
        book_api = {
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": review_count,
            "average_score": round(average_score, 1)
        }

        return jsonify(book_api) 


''' LOGIN '''
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            print("campos vacios")
            return render_template("login.html")
        
        else:

            if db.execute("SELECT * FROM users WHERE username = :username", 
                        {"username": username}).rowcount == 0:
                print("usuario no existe")
                return render_template("login.html")
            else:
                user = db.execute("SELECT * FROM users WHERE username = :username", 
                                {"username": username}).fetchone()

                if check_password_hash(user.password, password):
                    session["user_id"] = user.id
                    print("usuario logueado")
                    return redirect(url_for("index"))
                else:
                    print("contraseña incorrecta")
                    return render_template("login.html")
    else:
        return render_template("login.html")


''' REGISTER '''
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # obtiene los datos del formulario
        username = request.form.get("username")
        password = request.form.get("password")
        cpassword = request.form.get("cf-password")

        # verifica que los campos no esten vacios
        if not username or not password or not cpassword:
            print("falta informacion")
            return render_template("register.html")
        
        else:

            # verifica que las contraseñas coincidan
            if password != cpassword:
                print("no coinciden")
                render_template("register.html")
            else:

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

                    redirect(url_for("index"))

                else:
                    print("usuario ya existe")
                    render_template("register.html")

            return render_template ("register.html") 
            
    else:
        return render_template("register.html")


''' LOGOUT '''
@app.route("/logout")
def logout():
    # limpia la sesion y redirige a la pagina de login
    session.clear()
    return redirect(url_for("index"))


