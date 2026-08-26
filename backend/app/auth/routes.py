from flask import Blueprint, request, jsonify
# Importing the shared database extension established by the team lead
from app.extensions import db 
from app.auth.service import register_user, authenticate_user, get_patient_profile, update_patient_profile
# Correctly importing the Flask decorator we just built in deps.py
from app.auth.deps import get_current_user 

# Create a standard Flask Blueprint instead of FastAPI's APIRouter
auth_bp = Blueprint('auth_patient', __name__)

@auth_bp.route("/auth/register", methods=["POST"])
def register():
    payload = request.get_json()
    result = register_user(db.session, payload)
    return jsonify({"success": True, "data": result, "message": "Registration successful."}), 201

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    payload = request.get_json()
    result = authenticate_user(db.session, payload)
    return jsonify({"success": True, "data": result, "message": "Login successful."}), 200

@auth_bp.route("/patients/me", methods=["GET"])
@get_current_user # Using the exact name assigned to M5
def get_profile(current_user):
    result = get_patient_profile(db.session, current_user["user_id"])
    return jsonify({"success": True, "data": result})

@auth_bp.route("/patients/me", methods=["PATCH"])
@get_current_user
def update_profile(current_user):
    payload = request.get_json()
    result = update_patient_profile(db.session, current_user["user_id"], payload)
    return jsonify({"success": True, "data": result})