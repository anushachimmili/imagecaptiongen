from datetime import datetime
from imagecaptiongen import db, login_manager
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    membership_type = db.Column(db.String(10), nullable=False, default='free')
    captions = db.relationship('ImgCap', backref='author', lazy=True)

    def get_reset_token(self):
        key = current_app.config['SECRET_KEY']
        print(f'key: {key} ')
        s = Serializer(current_app.config['SECRET_KEY'])
        print(s.dumps({'user_id': self.id}))
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.membership_type}')"
    
    def is_premium(self):
        return self.membership_type == 'premium'


class ImgCap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.Text, unique=True, nullable=False)  
    name = db.Column(db.Text, nullable=False)
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    mimetype = db.Column(db.Text, nullable=False)  
    selected_model = db.Column(db.Text, nullable=False)
    num_models_used = db.Column(db.Integer, nullable=True)
    caption = db.Column(db.Text, nullable=False)
    is_user_modified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, nullable=True, default=0.0)
    tag = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
       return f"Img('{self.img}','{self.name}', '{self.mimetype}','{self.date_uploaded}','{self.selected_model}','{self.num_models_used}','{self.caption}','{self.is_user_modified}','{self.rating}', '{self.tag}','{self.user_id}')"

