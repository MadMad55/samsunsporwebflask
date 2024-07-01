from datetime import date
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from forms import CreatePostForm, FlaskForm, StringField, PasswordField, DataRequired, SubmitField, CreateComment
import locale


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# FLASK-LOGIN
from flask_login import LoginManager

login_manager = LoginManager()

login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Database tabloları

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    rel_posts = relationship("BlogPost", back_populates="rel_users")
    rel_comments = relationship("Comments", back_populates="rel_users")


class BlogPost(db.Model):
    __tablename__ = 'blogpost'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    rel_users = relationship("User", back_populates="rel_posts")
    rel_comments = relationship("Comments", back_populates="rel_posts", cascade='all, delete-orphan')



class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("blogpost.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    rel_posts = relationship("BlogPost", back_populates="rel_comments")
    rel_users = relationship("User", back_populates="rel_comments")


with app.app_context():
    db.create_all()


class Form(FlaskForm):
    name = StringField(label="İsim", validators=[DataRequired()])
    email = StringField(label="Eposta", validators=[DataRequired()])
    password = PasswordField(label="Şifre", validators=[DataRequired()])
    submit = SubmitField("ÜYE OL")


class Login(FlaskForm):
    email = StringField(label="Eposta", validators=[DataRequired()])
    password = PasswordField(label="Şifre", validators=[DataRequired()])
    submit = SubmitField("GİRİŞ YAP")



@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    locale.setlocale(locale.LC_ALL, "tr_TR")
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = Form()
    if form.validate_on_submit():
        if not User.query.filter_by(email=request.form.get("email")).first():
            new_user = User(
                name=request.form.get("name"),
                email=request.form.get("email"),
                password=generate_password_hash(password=request.form.get("password"), salt_length=16)
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("get_all_posts"))
        else:
            flash("Bu eposta adresiyle bir kayıt mevcut. Lütfen giriş yapın.")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = Login()
    if form.validate_on_submit():
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("get_all_posts"))
        flash("Yanlış eposta veya şifre.")
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    locale.setlocale(locale.LC_ALL, "tr_TR")
    form = CreateComment()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        comment = Comments(
            text=request.form.get("comment"),
            post_id=post_id,
            user_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
    comments = Comments.query.all()
    return render_template("post.html", post=requested_post, form=form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_only
def add_new_post():
    locale.setlocale(locale.LC_ALL, "tr_TR")
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            date=date.today().strftime("%B %d, %Y"),
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
