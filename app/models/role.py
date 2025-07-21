from mongoengine import Document, StringField, ListField

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
            }
        ]

        for role_data in default_roles:
            if not cls.objects(name=role_data['name']).first():
                cls(**role_data).save()
                print(f"Created role: {role_data['name']}")
