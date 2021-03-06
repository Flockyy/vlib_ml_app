from flask_login import UserMixin

from apps import db, login_manager

from apps.authentication.util import hash_pass

class Users(db.Model, UserMixin):

    __tablename__ = 'Users'

    id = db.Column(db.Integer(), primary_key=True, nullable=False, unique=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    city = db.Column(db.String(64), unique=False)
    password = db.Column(db.LargeBinary)
    fname = db.Column(db.String, nullable=True)
    lname = db.Column(db.String, nullable=True)
    address = db.Column(db.String, nullable=True)
    country = db.Column(db.String, nullable=True)
    postcode = db.Column(db.String, nullable=True)
    aboutme = db.Column(db.String, nullable=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)
    
    def json(self):
        return {
            'username': self.username,
            'email': self.email,
            'city': self.city,
            'password' : self.password,
            'fname' : self.fname,
            'lname' : self.lname,
            'address' : self.address,
            'country' : self.country,
            'postcode' : self.postcode,
            'aboutme': self.aboutme
            }
            
class Predictions(db.Model):
    
    id = db.Column(db.Integer(), primary_key=True, nullable=False, unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('Users.id'), nullable=False)
    datetime = db.Column(db.String(), nullable=False)
    season = db.Column(db.String(), nullable=False)
    weather = db.Column(db.String(), nullable=False)
    workday = db.Column(db.String(), nullable=False)
    temperature = db.Column(db.Float(), nullable=False)
    atemperature = db.Column(db.Float(), nullable=False)
    humidity = db.Column(db.Float(), nullable=False)
    windspeed = db.Column(db.Float(), nullable=False)
    count = db.Column(db.Float(), nullable=False)
    
    def __repr__(self):
        return f'Prediction id: {self.id}'
    
    def json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'datetime': self.datetime,
            'season': self.season,
            'weather': self.weather,
            'workday': self.workday,
            'temperature': self.temperature,
            'atemperature': self.atemperature,
            'humidity': self.humidity,
            'windspeed': self.windspeed,
            'count': self.count
        }
    
    @classmethod
    def find_by_user_id(cls, user_id):
        prediction_list = []
        for pred in cls.query.filter_by(user_id=user_id).all():
            prediction_list.append(pred.json())
        return prediction_list
    
    @classmethod
    def get_all_in_list_with_user_name(cls):
        pred_list = []
        for pred in cls.query.join(Users).with_entities(Users.username, cls.datetime, cls.season, cls.weather, cls.workday, cls.temperature, cls.atemperature, cls.humidity, cls.windspeed, cls.count).all():
            pred_list.append(pred)
        return pred_list
    
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
    
    def last_prediction_by_user_id(cls, user_id):
        prediction = cls.query.filter_by(user_id=user_id).first().json()
        return prediction

@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None

