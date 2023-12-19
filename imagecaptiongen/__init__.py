from math import floor
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from imagecaptiongen.config import Config
from datetime import datetime
import stripe


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    from imagecaptiongen.users.routes import users
    from imagecaptiongen.captions.routes import captions
    from imagecaptiongen.main.routes import main
    from imagecaptiongen.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(captions)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    
    # Define the time_since function
    def time_since(dt):
        now = datetime.utcnow()
        diff = now - dt

        periods = (
            (diff.days / 365, "year", "years"),
            (diff.days / 30, "month", "months"),
            (diff.days / 7, "week", "weeks"),
            (diff.days, "day", "days"),
            (diff.seconds / 3600, "hour", "hours"),
            (diff.seconds / 60, "min", "mins"),
            (diff.seconds, "second", "seconds"),
        )

        for period, singular, plural in periods:
            if floor(period) >= 1:
                return "%d %s ago" % (period, singular if floor(period) == 1 else plural)

        return "just now"

    # Register the time_since function as a Jinja filter
    app.jinja_env.filters['time_since'] = time_since

    return app
