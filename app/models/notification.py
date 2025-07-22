"""
Notification Model

This module defines the Notification model for the application.
"""
from datetime import datetime
from mongoengine import (
    Document, StringField, LazyReferenceField, DateTimeField, 
    BooleanField, IntField, CASCADE
)

# Import base document
from .base import BaseDocument

# Import the database instance from extensions
from app.extensions import db

class Notification(BaseDocument):
    """
    Notification model for user notifications.
    
    Attributes:
        user (User): The user who will receive the notification
        title (str): The title of the notification
        message (str): The content of the notification
        notification_type (str): The type of notification (e.g., 'info', 'success', 'warning', 'error')
        icon (str): Optional icon to display with the notification
        is_read (bool): Whether the notification has been read
        action_url (str): Optional URL for the notification action
        action_label (str): Optional label for the action button
        priority (int): Notification priority (1=low, 2=normal, 3=high)
    """
    # Notification types
    TYPE_INFO = 'info'
    TYPE_SUCCESS = 'success'
    TYPE_WARNING = 'warning'
    TYPE_ERROR = 'error'
    
    # Priority levels
    PRIORITY_LOW = 1
    PRIORITY_NORMAL = 2
    PRIORITY_HIGH = 3
    
    # Fields - using string reference to avoid circular imports
    user = LazyReferenceField('user.User', required=True, reverse_delete_rule=CASCADE, passthrough=True)
    title = StringField(required=True, max_length=200)
    message = StringField(required=True)
    notification_type = StringField(choices=[
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        (TYPE_ERROR, 'Error')
    ], default=TYPE_INFO)
    icon = StringField()
    is_read = BooleanField(default=False)
    action_url = StringField()
    action_label = StringField(max_length=50)
    priority = IntField(default=PRIORITY_NORMAL, min_value=1, max_value=3)
    read_at = DateTimeField()
    
    # Meta options - using a dictionary to avoid class-level execution issues
    meta = {
        'collection': 'notifications',
        'indexes': [
            # Single field indexes
            'user',
            'is_read',
            'notification_type',
            'priority',
            'created_at',
            'read_at',
            
            # Compound indexes
            [('user', 1), ('is_read', 1)],
            [('user', 1), ('created_at', -1)],
            [('created_at', -1)],  # For sorting by creation date
            
            # TTL index for auto-expiring notifications after 30 days
            {'fields': ['created_at'], 'expireAfterSeconds': 60 * 60 * 24 * 30}
        ],
        'ordering': ['-created_at']
    }
    
    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
        self.save()
    
    def to_dict(self):
        """Convert the notification to a dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'icon': self.icon,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'action_label': self.action_label,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_notification(
        cls, 
        user, 
        title, 
        message, 
        notification_type=TYPE_INFO, 
        icon=None, 
        action_url=None, 
        action_label=None, 
        priority=PRIORITY_NORMAL
    ):
        """
        Create a new notification.
        
        Args:
            user: User to receive the notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            icon: Optional icon
            action_url: Optional URL for action
            action_label: Optional action button label
            priority: Notification priority
            
        Returns:
            The created notification
        """
        notification = cls(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            icon=icon,
            action_url=action_url,
            action_label=action_label,
            priority=priority
        )
        notification.save()
        return notification
    
    @classmethod
    def get_unread_count(cls, user):
        """
        Get the number of unread notifications for a user.
        
        Args:
            user: User to get unread count for
            
        Returns:
            Number of unread notifications
        """
        return cls.objects(user=user, is_read=False).count()
    
    @classmethod
    def get_recent_notifications(cls, user, limit=10):
        """
        Get recent notifications for a user.
        
        Args:
            user: User to get notifications for
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        return cls.objects(user=user).order_by('-created_at').limit(limit)
