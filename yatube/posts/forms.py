from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        help_texts = {
            'text': "Текст нового поста",
            'group': "Группа, к которой будет относиться пост"
        }
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta():
        model = Comment
        fields = ('text',)
