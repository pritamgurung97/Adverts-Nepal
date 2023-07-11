from flask import Flask,render_template,redirect
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


app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap(app)
app.config['SECRET_KEY'] = "hello"

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
    img_url = db.Column(db.String(250))
    description = db.Column(db.Text, nullable=False)
    author = relationship('User', back_populates='posts')
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

# Create a Flask_Form for posting an ad to the database

class Ad_details(FlaskForm):
    ad_title = StringField('Title', validators=[DataRequired()])
    ad_description = StringField('Description', validators=[DataRequired()])
    image_url = StringField('Image URL')
    submit = SubmitField('Post Ad')

# Create the database
# with app.app_context():
#     db.create_all()

@app.route('/')
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
        new_ad = Ad(ad_title=title, description=description, img_url=img_url)
        db.session.add(new_ad)
        db.session.commit()
    return render_template('post.html',form=form)









if __name__ == "__main__":
    app.run(debug=True)
