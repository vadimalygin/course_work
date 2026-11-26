"""
Course Management App Configuration.

This app manages algebra course lessons and steps.
"""
from django.apps import AppConfig


class CourseManagementConfig(AppConfig):
    """Configuration class for Course Management App."""
    
    name = 'course_management'
    verbose_name = 'Course Management'
