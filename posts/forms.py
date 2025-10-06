from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 2, 
                    "placeholder": "Add a comment...", 
                    "maxlength": 1000,
                    "class": "form-control form-control-sm",
                }
            )
        }