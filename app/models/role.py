"""
Role Model

This module defines the Role model for role-based access control.
"""
from mongoengine import Document, StringField, ListField
from flask import current_app

class Role(Document):
    """
    User roles for access control
    """
    name = StringField(required=True, unique=True)
    description = StringField()
    permissions = ListField(StringField())

    meta = {
        'collection': 'roles',
        'indexes': [
            'name'
        ]
    }

    def __str__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name):
        """Get role by name"""
        return cls.objects(name=name).first()

    @classmethod
    def ensure_roles_exist(cls):
        """Ensure that default roles exist in the database"""
        default_roles = [
            {
                'name': 'admin',
                'description': 'Administrator with full access',
                'permissions': ['admin']
            },
            {
                'name': 'user',
                'description': 'Regular user with basic access',
                'permissions': ['basic']
            },
            {
                'name': 'examiner',
                'description': 'Examiner with access to conduct tests',
                'permissions': ['conduct_tests', 'view_reports']
            },
            {
                'name': 'candidate',
                'description': 'Candidate taking tests',
                'permissions': ['take_tests']
            }
        ]

        for role_data in default_roles:
            if not cls.objects(name=role_data['name']).first():
                cls(**role_data).save()
                current_app.logger.info(f'Created role: {role_data["name"]}')

# Register the model after it's defined
from . import registry
registry.register('Role', Role)

# Export the model
__all__ = ['Role']

# Ensure that default roles exist in the database
def setup_roles():
    Role.ensure_roles_exist()
