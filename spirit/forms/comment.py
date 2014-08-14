#-*- coding: utf-8 -*-

import hashlib
import os

from markdown import Markdown

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.image import Image

from spirit.models.comment import Comment
from spirit.models.topic import Topic
from spirit import utils


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['comment', ]

    def __init__(self, user=None, topic=None, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.user = user
        self.topic = topic
        self.mentions = None  # {username: User, }
        self.fields['comment'].widget.attrs['placeholder'] = _("Write comment...")

    def _get_comment_html(self):
        markdown = Markdown(output_formats='html5',
                            safe_mode='escape',
                            extensions=settings.ST_MARKDOWN_EXT)
        markdown.mentions = {}
        comment_html = markdown.convert(self.cleaned_data['comment'])
        self.mentions = markdown.mentions
        return comment_html

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.user = self.user
            self.instance.topic = self.topic

        self.instance.comment_html = self._get_comment_html()
        return super(CommentForm, self).save(commit)


class CommentMoveForm(forms.Form):

    topic = forms.ModelChoiceField(queryset=Topic.objects.all(), widget=forms.TextInput)

    def __init__(self, topic, *args, **kwargs):
        super(CommentMoveForm, self).__init__(*args, **kwargs)
        self.fields['comments'] = forms.ModelMultipleChoiceField(queryset=Comment.objects.filter(topic=topic),
                                                                 widget=forms.CheckboxSelectMultiple)

    def save(self):
        comments = self.cleaned_data['comments']
        comments_list = list(comments)
        topic = self.cleaned_data['topic']
        comments.update(topic=topic)

        # Update topic in comment instance
        for c in comments_list:
            c.topic = topic

        return comments_list


class CommentImageForm(forms.Form):

    image = forms.ImageField()

    def __init__(self, user=None, *args, **kwargs):
        super(CommentImageForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_image(self):
        image = self.cleaned_data["image"]
        image.format = Image.open(image).format.lower()
        image.seek(0)

        if image.format not in settings.ST_ALLOWED_UPLOAD_IMAGE_FORMAT:
            raise forms.ValidationError(_("Unsupported file format. Supported formats are %s."
                                          % ", ".join(settings.ST_ALLOWED_UPLOAD_IMAGE_FORMAT)))

        return image

    def save(self):
        image = self.cleaned_data["image"]
        hash = hashlib.md5(image.read()).hexdigest()
        image.name = u"".join((hash, ".", image.format))
        upload_to = os.path.join('spirit', 'images', str(self.user.pk))
        image.url = os.path.join(settings.MEDIA_URL, upload_to, image.name).replace("\\", "/")
        media_path = os.path.join(settings.MEDIA_ROOT, upload_to)
        utils.mkdir_p(media_path)

        with open(os.path.join(media_path, image.name), "wb") as fh:
            image.seek(0)
            fh.write(image.read())
            image.close()

        return image