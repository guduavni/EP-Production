"""
Base Model Module

This module contains the base document class and custom query set for all models.
"""
from datetime import datetime
from bson import ObjectId
from mongoengine import Document, DateTimeField, StringField, BooleanField
from mongoengine.base import BaseField
from mongoengine.queryset import QuerySet
from mongoengine.queryset.manager import queryset_manager

# Import the database instance from extensions
from app.extensions import db

class BaseQuerySet(QuerySet):
    """Custom QuerySet with additional methods."""
    
    def to_dict(self):
        """Convert query results to a list of dictionaries."""
        return [obj.to_dict() for obj in self]
    
    def paginate(self, page=1, per_page=10):
        """Paginate the queryset.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            
        Returns:
            Paginated query results
        """
        return self.skip((page - 1) * per_page).limit(per_page)


class BaseDocument(Document):
    """
    Base document with common fields and methods.
    """
    meta = {
        'abstract': True,  # Make this an abstract base class
        'allow_inheritance': True,  # Allow inheritance
        'queryset_class': BaseQuerySet
    }
    
    # Common fields
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField()
    updated_by = StringField()
    is_deleted = BooleanField(default=False)
    deleted_at = DateTimeField()
    
    def save(self, *args, **kwargs):
        """
        Override save to update timestamps and handle soft delete.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            The saved document
        """
        now = datetime.utcnow()
        
        if not self.id:
            self.created_at = now
            if hasattr(self, 'created_by') and not self.created_by and hasattr(self, 'current_user_id'):
                self.created_by = self.current_user_id
        
        self.updated_at = now
        if hasattr(self, 'updated_by') and hasattr(self, 'current_user_id'):
            self.updated_by = self.current_user_id
        
        # Handle soft delete
        if hasattr(self, 'is_deleted') and self.is_deleted and not hasattr(self, 'deleted_at'):
            self.deleted_at = now
        
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Override delete to implement soft delete.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if hasattr(self, 'is_deleted'):
            self.is_deleted = True
            self.deleted_at = datetime.utcnow()
            if hasattr(self, 'updated_by') and hasattr(self, 'current_user_id'):
                self.updated_by = self.current_user_id
            self.save()
        else:
            super().delete(*args, **kwargs)
    
    def hard_delete(self, *args, **kwargs):
        """
        Permanently delete the document.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().delete(*args, **kwargs)
    
    def to_dict(self, exclude=None):
        """
        Convert document to dictionary.
        
        Args:
            exclude: List of fields to exclude from the result
            
        Returns:
            dict: Dictionary representation of the document
        """
        exclude = exclude or []
        data = self.to_mongo().to_dict()
        
        # Convert ObjectId to string
        if '_id' in data:
            data['id'] = str(data.pop('_id'))
        
        # Convert datetime objects to ISO format strings
        for field_name, field_value in data.items():
            if isinstance(field_value, datetime):
                data[field_name] = field_value.isoformat()
            elif isinstance(field_value, ObjectId):
                data[field_name] = str(field_value)
        
        # Exclude specified fields
        for field in exclude:
            if field in data:
                del data[field]
        
        return data
    
    @classmethod
    def get_by_id(cls, id):
        """
        Get document by ID.
        
        Args:
            id: Document ID (string or ObjectId)
            
        Returns:
            Document or None if not found
        """
        try:
            return cls.objects.get(id=id, is_deleted__ne=True)
        except (cls.DoesNotExist, cls.MultipleObjectsReturned):
            return None
    
    @classmethod
    def get_all(cls, include_deleted=False):
        """
        Get all documents, optionally including deleted ones.
        
        Args:
            include_deleted: Whether to include soft-deleted documents
            
        Returns:
            QuerySet of documents
        """
        query = {}
        if not include_deleted and hasattr(cls, 'is_deleted'):
            query['is_deleted__ne'] = True
        return cls.objects(**query)
    
    def __str__(self):
        """String representation of the document."""
        return f"<{self.__class__.__name__} {str(self.id)}>"
    
    def __repr__(self):
        """Official string representation of the document."""
        return f"<{self.__class__.__name__} id={str(self.id)}>"
