"""
API Blueprint

This module contains the API endpoints for the EP-Simulator application.
"""
from flask import Blueprint
from flask_restful import Api

# Create API blueprint
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Import resources to add routes
from . import resources  # noqa: F401
