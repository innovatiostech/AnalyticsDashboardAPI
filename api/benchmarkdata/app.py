import os
import random
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, jwt_required



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
    user_id = db.Column(db.String(255), unique=True, nullable=False)  # user_id should match the column in the database
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


app.config['MAX_CONTENT_LENGTH'] = 500 * 1000 * 1000  # 500 MB
app.config['UPLOAD_FOLDER'] = 'D:/Projects_ITech/ai.cam_github_repositories/AnalyticsDashboardAPI/api/benchmarkdata/uploads'  
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}

# Utility functions
def generate_random_camera():
    """Generate a random camera ID."""
    return f"Camera{random.randint(1, 6)}"

def generate_random_message():
    """Generate a random message."""
    return random.choice(["Coveralls", "Boots", "Hardhat", "Gloves"])

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def fileupload(directory):
    files = os.listdir(directory)
    if not files:
        return None, False  # Return None if no files are available
    file_path = os.path.join(directory, random.choice(files))
    return file_path, True

# Routes
@app.route('/analytics-action', methods=['POST'])
def analytics_action():                                                
    """Handle analytics actions with image and video uploads."""
    try:
        if 'image' not in request.files or 'video' not in request.files:
            return jsonify({'status': 'error', 'message': 'Image or video file not provided'}), 400

        image_file = request.files['image']
        video_file = request.files['video']

        if image_file.filename == '' or video_file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected files'}), 400

        image_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
        video_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')

        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)

        image_path = os.path.join(image_dir, secure_filename(image_file.filename))
        video_path = os.path.join(video_dir, secure_filename(video_file.filename))

        image_file.save(image_path)
        video_file.save(video_path)

        user_id = request.form.get('user_id', 'default_user')  # Default user_id if not provided

        new_action = Analytics(
            log_image=image_path,
            log_video=video_path,
            create_date=str(datetime.now()),
            message=generate_random_message(),
            camera_id=generate_random_camera(),
            camera_location="Location A",
            action=request.form.get('action_text', 'Default Action'),
            status="Action Received",
            user_id=user_id  # Include user_id
        )
        db.session.add(new_action)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Action added successfully',
            'log_image': image_path.replace('\\', '/'),
            'log_video': video_path.replace('\\', '/')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/analytics-insertinto', methods=['POST'])
def analytics_insertinto():
    """Insert analytics data from predefined directories."""
    try:
        image_dir = r"D:/Projects_ITech/ai.cam_github_repositories/AnalyticsDashboardAPI/api/benchmarkdata/var/www/html/logs/images" ### change path of images folder to your actual path  ##############
        video_dir = r"D:/Projects_ITech/ai.cam_github_repositories/AnalyticsDashboardAPI/api/benchmarkdata/var/www/html/logs/videos" ### change path of videos folder to your actual path  ##############

        log_image, image_uploaded = fileupload(image_dir)
        log_video, video_uploaded = fileupload(video_dir)

        if not (image_uploaded and video_uploaded):
            return jsonify({'status': 'error', 'message': 'Files not uploaded'}), 404

        user_id = request.form.get('user_id', 'testuser_02')  # Default user_id if not provided

        new_record = Analytics(
            log_image=log_image,
            log_video=log_video,
            create_date=str(datetime.now()),
            message=generate_random_message(),
            camera_id=generate_random_camera(),
            camera_location="Location B",
            action="New Action",
            status="Active",
            user_id=user_id  # Include user_id
        )
        db.session.add(new_record)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Record inserted successfully',
            'log_image': log_image.replace('\\', '/'),
            'log_video': log_video.replace('\\', '/')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/analytics-search', methods=['POST'])
def analytics_search():
    """Search analytics records based on parameters."""
    try:
        data = request.get_json()
        token = data.get('token', app.config['JWT_SECRET_KEY'])

        if token != app.config['JWT_SECRET_KEY']:
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401

        # Get search parameters from the request
        message = data.get('message')
        camera_id = data.get('camera_id')
        action = data.get('action')
        status = data.get('status')
        user_id = data.get('user_id')  # Get user_id from the request

        # Start the query
        query = Analytics.query

        # Filter based on provided search parameters
        if message:
            query = query.filter(Analytics.message.like(f"%{message}%"))
        if camera_id:
            query = query.filter(Analytics.camera_id.like(f"%{camera_id}%"))
        if action:
            query = query.filter(Analytics.action.like(f"%{action}%"))
        if status:
            query = query.filter(Analytics.status.like(f"%{status}%"))
        if user_id:  # Add filter for user_id
            query = query.filter(Analytics.user_id == user_id)

        # Get the search results
        search_results = query.all()

        # Return the search results
        response_data = [
            {
                'log_image': item.log_image.replace('\\', '/'),
                'log_video': item.log_video.replace('\\', '/'),
                'create_date': item.create_date,
                'message': item.message,
                'camera_id': item.camera_id,
                'camera_location': item.camera_location,
                'action': item.action,
                'status': item.status,
                'user_id': item.user_id  # Include user_id in the response
            }
            for item in search_results
        ]

        return jsonify({
            'status': 'success',
            'data': response_data
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/analytics-report', methods=['POST'])
def analytics_report():
    """Generate a report of analytics data within a date range and save as a PDF."""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Fetch analytics data within the date range
        report_data = Analytics.query.filter(Analytics.create_date.between(start_date, end_date)).all()

        # Directory to save the PDF
        pdf_dir = r"D:/Projects_ITech/ai.cam_github_repositories/AnalyticsDashboardAPI/api/benchmarkdata/uploads" ### change path of pdfs folder to your actual path  ##############
        os.makedirs(pdf_dir, exist_ok=True)

        # Generate PDF file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(pdf_dir, f"analytics_report_{timestamp}.pdf")

        # Create the PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Analytics Report")
        c.drawString(100, 730, f"Date Range: {start_date} to {end_date}")
        c.drawString(100, 710, "Generated On: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Table headers
        y_position = 680
        c.drawString(50, y_position, "ID")
        c.drawString(100, y_position, "User ID")
        c.drawString(200, y_position, "Message")
        c.drawString(300, y_position, "Date")
        c.drawString(450, y_position, "Camera Location")
        c.drawString(550, y_position, "Status")

        # Table rows
        y_position -= 20
        for item in report_data:
            if y_position < 50:  # Start a new page if the content exceeds
                c.showPage()
                y_position = 750

            c.drawString(50, y_position, str(item.analytics_id))
            c.drawString(100, y_position, item.user_id)
            c.drawString(200, y_position, item.message[:30])  # Truncate message for space
            c.drawString(280, y_position, item.create_date)
            c.drawString(450, y_position, item.camera_location)
            c.drawString(550, y_position, item.status)
            y_position -= 20

        c.save()

        return jsonify({
            'status': 'success',
            'message': 'Report generated successfully.',
            'pdf_path': pdf_path
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/analytics-viewall', methods=['POST'])
def analytics_viewall():
    """View all analytics records with optional filtering."""
    try:
        data = request.get_json()
        token = data.get('token', app.config['JWT_SECRET_KEY'])
        if token != app.config['JWT_SECRET_KEY']:
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401

        row_count = data.get('row_count', 10)
        analytics_id = data.get('analytics_id')

        query = Analytics.query
        if analytics_id:
            query = query.filter(Analytics.analytics_id == analytics_id)

        results = query.limit(row_count).all()

        response_data = [
            {
                'log_image': item.log_image.replace('\\', '/'),
                'log_video': item.log_video.replace('\\', '/'),
                'create_date': item.create_date,
                'message': item.message,
                'camera_id': item.camera_id,
                'camera_location': item.camera_location,
                'action': item.action,
                'status': item.status,
                'user_id':item.user_id
            }
            for item in results
        ]

        return jsonify({
            'status': 'success',
            'data': response_data
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/analytics-delete', methods=['POST'])
def analytics_delete():
    """Delete a specific analytics record by ID."""
    try:
        data = request.get_json()
        analytics_id = data.get('analytics_id')

        record = Analytics.query.get(analytics_id)
        if record:
            db.session.delete(record)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Record deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Record not found'}), 400

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/analytics-delete-all', methods=['POST'])
def analytics_delete_all():
    """Delete all analytics records."""
    try:
        Analytics.query.delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'All records deleted successfully'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/fileupload', methods=['POST'])
def handle_file_upload():
    """Handle file upload."""
    try:
        # Log all files sent in the request
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file part'}), 400

        file = request.files['file']

        # If no file is selected
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400

        # Check if the file is allowed
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        return jsonify({
            'status': 'success',
            'message': f'File uploaded successfully: {filename}',
            'file_path': file_path.replace('\\', '/')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



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
