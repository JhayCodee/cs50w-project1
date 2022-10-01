import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
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


@app.route("/", methods=["GET", "POST"])
def index():

    if 'user_id' in session:

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
            return render_template("index.html")

    else:
        return redirect(url_for('login'))


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

            if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 0:
                print("usuario no existe")
                return render_template("login.html")
            else:
                user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

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