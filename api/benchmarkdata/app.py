from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import datetime
import random
import os 

# Initialize the Flask App
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///benchmarkdata_db.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your_secure_token"  # Change this to a secure secret in production

db = SQLAlchemy(app)
def get_random_file(directory):
    files = os.listdir(directory)
    return os.path.join(directory, random.choice(files)) if files else None

jwt = JWTManager(app)

# Utility to generate random camera IDs and messages
def generate_random_camera():
    return f"Camera{random.randint(1, 6)}"

def generate_random_message():
    return random.choice(["Coveralls", "Boots", "Hardhat", "Gloves"])


# Models
class User(db.Model):
    userid = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=True)
    mob = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    permission = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=False)

class Camera(db.Model):
    camera_id = db.Column(db.Integer, primary_key=True)
    camera_url = db.Column(db.String(255), nullable=False)
    camera_location = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=False)

class Analytics(db.Model):
    analytics_id = db.Column(db.Integer, primary_key=True)
    #user_id = db.Column(db.String(255), unique=True, nullable=False)  # user_id should match the column in the database
    log_image = db.Column(db.String(255))
    log_video = db.Column(db.String(255))
    create_date = db.Column(db.String(255))
    message = db.Column(db.String(255))
    camera_id = db.Column(db.String(255), nullable=False)
    camera_location = db.Column(db.String(255))
    action = db.Column(db.String(255))
    time_to_action = db.Column(db.String(255))
    status = db.Column(db.String(255), nullable=False)

class Subscription(db.Model):
    subscription_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    machine_id = db.Column(db.String(255), nullable=False)
    expiry_date = db.Column(db.String(255), nullable=False)
    camera_count = db.Column(db.String(255), nullable=False)
    ai_module = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)

class Device(db.Model):
    device_id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.String(255), unique=True, nullable=False)
    device_location = db.Column(db.String(255), nullable=True)

# Routes
######################################### login page #########################################
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(user_id=data["user_id"], password=data["password"]).first()
    if user:
        access_token = create_access_token(identity=user.user_id)
        return jsonify({"token": access_token, "user_id": user.user_id, "status": user.status}), 200
    return jsonify({"msg": "Invalid credentials"}), 400

##################################### Register page ##########################################
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    new_user = User(
        user_id=data["user_id"],
        email=data["email"],
        mob=data["mob"],
        password=data["password"],
        name=data["name"],
        permission=data["permission"],
        company=data["company"],
        address=data["address"],
        status=data["status"],
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User registered successfully"}), 201

################################# dashboard page #################################################

@app.route("/dashboard", methods=["POST"])
@jwt_required()
def dashboard():
    data = request.get_json()
    start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(data["end date"], "%Y-%m-%d")

    total_analytics = Analytics.query.count()
    positive_count = Analytics.query.filter(Analytics.status == "true").count()
    negative_count = Analytics.query.filter(Analytics.status == "false").count()
    cam_count = Camera.query.count()

    return jsonify({
        "analytics_id_count": total_analytics,
        "positive_status_count": positive_count,
        "negative_status_count": negative_count,
        "camera_count": cam_count,
    }), 200




################################## analytics  page ################################################
def fileupload(directory):
    files = os.listdir(directory)
    if not files:
        return None, False  # Return None if no files are available
    file_path = os.path.join(directory, random.choice(files))
    return file_path, True

@app.route('/analytics-action', methods=['POST'])
def analytics_action():
    if 'image' not in request.files or 'video' not in request.files:
        return jsonify({'status': 'error', 'message': 'Image or video file not provided'}), 400

    image_file = request.files['image']
    video_file = request.files['video']

    # Save the uploaded files
    if image_file.filename == '' or video_file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected files'}), 400

    image_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
    video_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')

    # Ensure directories exist
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    image_path = os.path.join(image_dir, image_file.filename)
    video_path = os.path.join(video_dir, video_file.filename)

    image_file.save(image_path)
    video_file.save(video_path)

    # Create a new analytics entry
    new_action = Analytics(
        log_image=image_path,
        log_video=video_path,
        create_date=str(datetime.now()),
        message=generate_random_message(),
        camera_id=generate_random_camera(),
        camera_location="Location A",
        action=request.form.get('action_text', 'Default Action'),
        status="Action Received"
    )
    db.session.add(new_action)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Action added successfully',
        'log_image': image_path,
        'log_video': video_path
    })

# Route: /analytics-insertinto
@app.route('/analytics-insertinto', methods=['POST'])
def analytics_insertinto():
    image_dir = r"D:\company\Innovatiostech\aicams.in\logs\images"
    video_dir = r"D:\company\Innovatiostech\aicams.in\logs\videos"

    log_image, image_uploaded = fileupload(image_dir)
    log_video, video_uploaded = fileupload(video_dir)

    if not (image_uploaded and video_uploaded):
        return jsonify({'status': 'error', 'message': 'Files not uploaded'}), 404

    new_record = Analytics(
        log_image=log_image,
        log_video=log_video,
        create_date=str(datetime.now()),
        message=generate_random_message(),
        camera_id=generate_random_camera(),
        camera_location="Location B",
        action="New Action",
        status="Active"
    )
    db.session.add(new_record)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Record inserted successfully',
        'log_image': log_image,
        'log_video': log_video
    })

# Route: /analytics-report
@app.route('/analytics-report', methods=['POST'])
def analytics_report():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    report_data = Analytics.query.filter(Analytics.create_date.between(start_date, end_date)).all()

    return jsonify({
        'status': 'success',
        'data': [
            {
                'analytics_id': item.analytics_id,
                'message': item.message,
                'create_date': item.create_date
            }
            for item in report_data
        ]
    })

# Route: /analytics-viewall
@app.route('/analytics-viewall', methods=['POST'])
def analytics_viewall():
    data = request.get_json()
    token = data.get('token', 'your_secure_token')  # Default token for now
    if token != "your_secure_token":
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 401

    row_count = data.get('row_count', 10)
    analytics_id = data.get('analytics_id')

    query = Analytics.query
    if analytics_id:
        query = query.filter(Analytics.analytics_id == analytics_id)

    results = query.limit(row_count).all()

    response_data = [
        {
            'log_image': item.log_image,
            'log_video': item.log_video,
            'create_date': item.create_date,
            'message': item.message,
            'camera_id': item.camera_id,
            'camera_location': item.camera_location,
            'action': item.action,
            'status': item.status
        }
        for item in results
    ]

    return jsonify({
        'status': 'success',
        'data': response_data
    })

# Route: /analytics-delete
@app.route('/analytics-delete', methods=['POST'])
def analytics_delete():
    data = request.get_json()
    analytics_id = data.get('analytics_id')

    record = Analytics.query.get(analytics_id)
    if record:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Record deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Record not found'}), 400

# Route: /analytics-delete-all
@app.route('/analytics-delete-all', methods=['POST'])
def analytics_delete_all():
    Analytics.query.delete()
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'All records deleted successfully'})


########################################### Settings page ####################################################


#camera
@app.route("/settings-camera", methods=["POST"])
@jwt_required()
def settings_camera():
    cameras = Camera.query.all()
    result = [
        {
            "camera_id": c.camera_id,
            "camera_url": c.camera_url,
            "camera_location": c.camera_location,
            "status": c.status,
        }
        for c in cameras
    ]
    return jsonify(result), 200

@app.route("/insert-camera", methods=["POST"])
@jwt_required()
def insert_camera():
    try:
        data = request.get_json()
        new_camera = Camera(
            camera_url=data["camera_url"],
            camera_location=data.get("camera_location", ""),
            status=data["status"]
        )
        db.session.add(new_camera)
        db.session.commit()
        return jsonify({"msg": "Camera added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/settings-camera-search", methods=["POST"])
@jwt_required()
def settings_camera_search():
    data = request.get_json()
    query = Camera.query.filter(Camera.camera_location.contains(data["query"]))
    result = [
        {
            "camera_id": c.camera_id,
            "camera_url": c.camera_url,
            "camera_location": c.camera_location,
            "status": c.status,
        }
        for c in query
    ]
    return jsonify(result), 200

@app.route("/settings-camera-delete", methods=["POST"])
@jwt_required()
def settings_camera_delete():
    data = request.get_json()
    camera = Camera.query.filter_by(camera_id=data["camera_id"]).first()
    if camera:
        db.session.delete(camera)
        db.session.commit()
        return jsonify({"msg": "Camera deleted"}), 200
    return jsonify({"msg": "Camera not found"}), 404

@app.route("/settings-camera-delete-all", methods=["POST"])
@jwt_required()
def settings_camera_delete_all():
    Camera.query.delete()
    db.session.commit()
    return jsonify({"msg": "All cameras deleted"}), 200

@app.route("/settings-camera-edit", methods=["POST"])
@jwt_required()
def settings_camera_edit():
    data = request.get_json()
    camera = Camera.query.filter_by(camera_id=data["camera_id"]).first()
    if camera:
        camera.camera_url = data["camera_url"]
        camera.camera_location = data["camera_location"]
        camera.status = data["status"]
        db.session.commit()
        return jsonify({"msg": "Camera updated"}), 200
    return jsonify({"msg": "Camera not found"}), 404

@app.route("/camera-viewall", methods=["GET"])
@jwt_required()
def camera_viewall():
    try:
        cameras = Camera.query.all()
        result = [
            {
                "camera_id": c.camera_id,
                "camera_url": c.camera_url,
                "camera_location": c.camera_location,
                "status": c.status,
            }
            for c in cameras
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/settings-camera-close", methods=["POST"])
@jwt_required()
def settings_camera_close():
    return jsonify({"msg": "Camera settings closed"}), 200


#users

@app.route("/settings-users", methods=["POST"])
@jwt_required()
def settings_users():
    users = User.query.all()
    result = [
        {
            "user_id": u.user_id,
            "email": u.email,
            "name": u.name,
            "permission": u.permission,
            "status": u.status,
        }
        for u in users
    ]
    return jsonify(result), 200

@app.route("/insert-user", methods=["POST"])
@jwt_required()
def insert_user():
    try:
        data = request.get_json()
        new_user = User(
            user_id=data["user_id"],
            email=data["email"],
            mob=data["mob"],
            password=data["password"],
            name=data["name"],
            permission=data["permission"],
            company=data["company"],
            address=data["address"],
            status=data["status"],
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/user-viewall", methods=["GET"])
@jwt_required()
def user_viewall():
    try:
        users = User.query.all()
        result = [
            {
                "user_id": u.user_id,
                "email": u.email,
                "mob": u.mob,
                "name": u.name,
                "company": u.company,
                "address": u.address,
                "status": u.status,
            }
            for u in users
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/settings-users-search", methods=["POST"])
@jwt_required()
def settings_users_search():
    data = request.get_json()
    query = User.query.filter(User.name.contains(data["query"]))
    result = [
        {
            "user_id": u.user_id,
            "email": u.email,
            "name": u.name,
            "permission": u.permission,
            "status": u.status,
        }
        for u in query
    ]
    return jsonify(result), 200

@app.route("/settings-users-delete", methods=["POST"])
@jwt_required()
def settings_users_delete():
    data = request.get_json()
    user = User.query.filter_by(user_id=data["user_id"]).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"msg": "User deleted"}), 200
    return jsonify({"msg": "User not found"}), 404

@app.route("/settings-users-delete-all", methods=["POST"])
@jwt_required()
def settings_users_delete_all():
    User.query.delete()
    db.session.commit()
    return jsonify({"msg": "All users deleted"}), 200

@app.route("/settings-users-edit", methods=["POST"])
@jwt_required()
def settings_users_edit():
    data = request.get_json()
    user = User.query.filter_by(user_id=data["user_id"]).first()
    if user:
        user.email = data["email"]
        user.name = data["name"]
        user.permission = data["permission"]
        user.status = data["status"]
        db.session.commit()
        return jsonify({"msg": "User updated"}), 200
    return jsonify({"msg": "User not found"}), 404

@app.route("/settings-users-close", methods=["POST"])
@jwt_required()
def settings_users_close():
    return jsonify({"msg": "User settings closed"}), 200


#subscription

@app.route("/settings-subscription", methods=["POST"])
@jwt_required()
def settings_subscription():
    subscriptions = Subscription.query.all()
    result = [
        {
            "subscription_id": s.subscription_id,
            "device_id": s.device_id,
            "user_id": s.user_id,
            "expiry_date": s.expiry_date,
            "camera_count": s.camera_count,
            "ai_module": s.ai_module,
            "status": s.status,
        }
        for s in subscriptions
    ]
    return jsonify(result), 200


@app.route("/insert-subscription", methods=["POST"])
@jwt_required()
def insert_subscription():
    try:
        data = request.get_json()
        new_subscription = Subscription(
            device_id=data["device_id"],
            user_id=data["user_id"],
            machine_id=data["machine_id"],
            expiry_date=data["expiry_date"],
            camera_count=data["camera_count"],
            ai_module=data["ai_module"],
            status=data["status"],
        )
        db.session.add(new_subscription)
        db.session.commit()
        return jsonify({"msg": "Subscription added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/subscription-viewall", methods=["GET"])
@jwt_required()
def subscription_viewall():
    try:
        subscriptions = Subscription.query.all()
        result = [
            {
                "subscription_id": s.subscription_id,
                "device_id": s.device_id,
                "user_id": s.user_id,
                "machine_id": s.machine_id,
                "expiry_date": s.expiry_date,
                "camera_count": s.camera_count,
                "ai_module": s.ai_module,
                "status": s.status,
            }
            for s in subscriptions
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400



@app.route("/settings-subscription-search", methods=["POST"])
@jwt_required()
def settings_subscription_search():
    data = request.get_json()
    query = Subscription.query.filter(Subscription.user_id.contains(data["query"]))
    result = [
        {
            "subscription_id": s.subscription_id,
            "device_id": s.device_id,
            "user_id": s.user_id,
            "expiry_date": s.expiry_date,
            "camera_count": s.camera_count,
            "ai_module": s.ai_module,
            "status": s.status,
        }
        for s in query
    ]
    return jsonify(result), 200

@app.route("/settings-subscription-delete", methods=["POST"])
@jwt_required()
def settings_subscription_delete():
    data = request.get_json()
    subscription = Subscription.query.filter_by(subscription_id=data["subscription_id"]).first()
    if subscription:
        db.session.delete(subscription)
        db.session.commit()
        return jsonify({"msg": "Subscription deleted"}), 200
    return jsonify({"msg": "Subscription not found"}), 404

@app.route("/settings-subscription-delete-all", methods=["POST"])
@jwt_required()
def settings_subscription_delete_all():
    Subscription.query.delete()
    db.session.commit()
    return jsonify({"msg": "All subscriptions deleted"}), 200

@app.route("/settings-subscription-edit", methods=["POST"])
@jwt_required()
def settings_subscription_edit():
    data = request.get_json()
    subscription = Subscription.query.filter_by(subscription_id=data["subscription_id"]).first()
    if subscription:
        subscription.device_id = data["device_id"]
        subscription.user_id = data["user_id"]
        subscription.expiry_date = data["expiry_date"]
        subscription.camera_count = data["camera_count"]
        subscription.ai_module = data["ai_module"]
        subscription.status = data["status"]
        db.session.commit()
        return jsonify({"msg": "Subscription updated"}), 200
    return jsonify({"msg": "Subscription not found"}), 404

@app.route("/settings-subscription-close", methods=["POST"])
@jwt_required()
def settings_subscription_close():
    return jsonify({"msg": "Subscription settings closed"}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
