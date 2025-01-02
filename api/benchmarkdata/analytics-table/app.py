from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///analytics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1000 * 1000  # 500 MB
app.config['UPLOAD_FOLDER'] = 'AnalyticsDashboardAPI/api/benchmarkdata/var/www/html/logs/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['CORS_HEADER'] = 'application/json'
app.config['SECURE_TOKEN'] = 'your_secure_token'  # Replace with a strong secure token

db = SQLAlchemy(app)

# Database model
class Analytics(db.Model):
    analytics_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    log_image = db.Column(db.String(255))
    log_video = db.Column(db.String(255))
    create_date = db.Column(db.String(50))
    message = db.Column(db.String(255))
    camera_id = db.Column(db.String(50))
    camera_location = db.Column(db.String(255))
    action = db.Column(db.String(255))
    status = db.Column(db.String(50))
    user_id = db.Column(db.String(50), nullable=False)  # user_id added

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
    """Select a random file from a directory."""
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
        image_dir = r"AnalyticsDashboardAPI/api/benchmarkdata/var/www/html/logs/images"
        video_dir = r"AnalyticsDashboardAPI/api/benchmarkdata/var/www/html/logs/videos"

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
        token = data.get('token', app.config['SECURE_TOKEN'])

        if token != app.config['SECURE_TOKEN']:
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
    """Generate a report of analytics data within a date range."""
    try:
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

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/analytics-viewall', methods=['POST'])
def analytics_viewall():
    """View all analytics records with optional filtering."""
    try:
        data = request.get_json()
        token = data.get('token', app.config['SECURE_TOKEN'])
        if token != app.config['SECURE_TOKEN']:
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
                'status': item.status
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


if __name__ == '__main__':
    app.run(debug=True)
