from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Analytics(db.Model):
    __tablename__ = 'analytics'
    analytics_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    log_image = db.Column(db.String(255))
    log_video = db.Column(db.String(255))
    create_date = db.Column(db.String(255))
    message = db.Column(db.String(255))
    camera_id = db.Column(db.String(255), nullable=False)
    camera_location = db.Column(db.String(255))
    action = db.Column(db.String(255))
    time_to_action = db.Column(db.String(255))
    status = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(50), nullable=False)  # user_id added

    def __repr__(self):
        return f'<Analytics {self.analytics_id}>'
