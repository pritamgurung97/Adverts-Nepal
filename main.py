from flask import Flask,render_template,redirect,flash, url_for,abort
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



class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    contact_number = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    posts = relationship('Ad', back_populates='author')

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
    email = StringField('Email', validators=[DataRequired()])
    contact_number = IntegerField('Contact Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

#Create a Flask_Form to login users.
class Login_form(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

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
        email = register_form.email.data
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
        return redirect(url_for('home', logged_in=current_user.is_authenticated))
    return render_template('register.html', form=register_form)

@app.route('/login',methods=['GET','POST'])
def login():
    login_form = Login_form()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('The email does not exists, please try again')
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




if __name__ == "__main__":
    app.run(debug=True, port="5001")
