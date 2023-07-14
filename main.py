from flask import Flask,render_template,redirect,flash, url_for,abort,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import SubmitField,StringField,IntegerField,PasswordField
from functools import wraps
from datetime import date
from wtforms.validators import Email
from flask_ckeditor import CKEditorField
from flask_gravatar import Gravatar


app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap(app)
app.config['SECRET_KEY'] = "hello"
login_manager = LoginManager()
login_manager.init_app(app)

#Database initilization
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)



class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    contact_number = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    posts = relationship('Ad', back_populates='author')
    comments = relationship('Comment', back_populates='comment_author')

class Ad(db.Model):
    __tablename__ = "ads"
    id = db.Column(db.Integer,primary_key=True)
    ad_title = db.Column(db.String(250), nullable=False)
    ad_price = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.String(250))
    description = db.Column(db.Text, nullable=False)
    author = relationship('User', back_populates='posts')
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date = db.Column(db.String(250), nullable=False)

    #Parent relationship
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship('User',back_populates="comments")

    #child relationship
    ad_id = db.Column(db.Integer, db.ForeignKey("ads.id"))
    parent_post = relationship("Ad", back_populates="comments")
    text = db.Column(db.Text, nullable=False)



# Create a Flask_Form for posting an ad to the database

class Ad_details(FlaskForm):
    ad_title = StringField('Title', validators=[DataRequired()])
    ad_description = StringField('Description', validators=[DataRequired()])
    ad_price = IntegerField('Price', validators=[DataRequired()])
    image_url = StringField('Image URL')
    submit = SubmitField('Post Ad')

#Create a Flask_Form to register users.
class Register_form(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact_number = IntegerField('Contact Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

#Create a Flask_Form to login users.
class Login_form(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

#Create a Flask_Form to edit ad.

class Edit_form(FlaskForm):
    ad_title = StringField('Title')
    ad_description = StringField('Description')
    ad_price = IntegerField('Price')
    image_url = StringField('Image URL')
    submit = SubmitField('Post Ad')

class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


# Create the database
with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if current_user.id != 1:
            return abort(403)

        return f(*args,**kwargs)
    return decorated_function


def author_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"author_id from author only decorator: {kwargs['author_id']}")
        if current_user.id != kwargs['author_id']:
            return abort(403)

        return f(*args,**kwargs)
    return decorated_function




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
# Get all the ads in the home page.
def home():
    all_ads = Ad.query.all()
    return render_template('index.html', all_ads=all_ads)

@app.route('/post-ad', methods=['GET','POST'])
def post_ad():
    form = Ad_details()
    if form.validate_on_submit():
        title = form.ad_title.data
        description = form.ad_description.data
        img_url = form.image_url.data
        price = form.ad_price.data
        author = current_user
        current_date = date.today().strftime("%B %d, %Y")
        new_ad = Ad(ad_title=title, description=description, img_url=img_url, author=author, date=current_date,ad_price=price)
        db.session.add(new_ad)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('post.html',form=form)

@app.route('/register', methods=['POST', 'GET'])
def register():
    register_form = Register_form()
    if register_form.validate_on_submit():
        name = register_form.name.data.title()
        email = register_form.email.data.lower()
        contact_number = register_form.contact_number.data
        hashed_salted_password = generate_password_hash(register_form.password.data,method="pbkdf2:sha256",salt_length=8)
        print(name)
        user = User.query.filter_by(email=email).first()
        if user:
            flash('The email already exists, please try logging in instead')
            return redirect(url_for('login'))
        print(name)
        new_user = User(name=name,email=email,contact_number=contact_number,password=hashed_salted_password)
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(email=email).first()
        login_user(user)
        print(current_user)
        return redirect(url_for('home'))
    return render_template('register.html', form=register_form)

@app.route('/login',methods=['GET','POST'])
def login():
    login_form = Login_form()
    if login_form.validate_on_submit():
        email = login_form.email.data.lower()
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('The email does not exists, please sign up first')
            return redirect(url_for('login'))
        if check_password_hash(user.password, password):
            login_user(user)
            print(current_user)
            print(current_user.is_authenticated)
            return redirect(url_for('home'))
        else:
            flash('Password incorrect, please try again with correct credentials.')
    return render_template('login.html', form=login_form, logged_in=current_user.is_authenticated)

@app.route('/logout')
def logout():
    logout_user()
    print(current_user)
    print(current_user.is_authenticated)
    return redirect(url_for('home'))

@app.route('/delete/<int:post_id>')
@admin_only
def delete_post(post_id):
    post_to_delete = Ad.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/view-ad/<int:post_id>', methods=['GET','POST'])
def view_ad(post_id):
    form = CommentForm()
    requested_ad = Ad.query.get(post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to login or register to comment')
            return redirect(url_for('login'))
        text = form.comment.data
        new_comment = Comment(text=text, comment_author=current_user,parent_post=requested_ad)
        db.session.add(new_comment)
        db.session.commit()


    print(requested_ad)
    return render_template('view_ad.html', ad=requested_ad,current_user=current_user, form=form)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/edit-ad/<int:post_id>/<int:author_id>', methods=['GET', 'POST'])
@author_only
def edit_ad(post_id,author_id):
    ad_to_be_edited = Ad.query.get(post_id)
    print(f'author id : ')
    print(f'current user : {current_user.id}')
    edit_form = Edit_form(
        ad_title=ad_to_be_edited.ad_title,
        ad_price=ad_to_be_edited.ad_price,
        image_url=ad_to_be_edited.img_url,
        ad_description=ad_to_be_edited.description,
    )
    if edit_form.validate_on_submit():
        ad_to_be_edited.ad_title = edit_form.ad_title.data
        ad_to_be_edited.ad_price = edit_form.ad_price.data
        ad_to_be_edited.img_url = edit_form.image_url.data
        ad_to_be_edited.description = edit_form.ad_description.data
        db.session.commit()
        return redirect(url_for('view_ad', post_id=post_id))

    return render_template('post.html', form=edit_form)







if __name__ == "__main__":
    app.run(debug=True, port="5001")
