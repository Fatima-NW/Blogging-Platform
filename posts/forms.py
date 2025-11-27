"""
Forms for the posts app

Includes:
- PostForm
- CommentForm
"""

from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    """ Form for creating and editing posts """
    class Meta:
        model = Post
        fields = ["title", "content"]

class CommentForm(forms.ModelForm):
    """ Form for submitting comments under a posts """
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3, 
                    "placeholder": "Add a comment", 
                    "maxlength": 2000,
                    "class": "form-control form-control-sm",
                }
            )
        }