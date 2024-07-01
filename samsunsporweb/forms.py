from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Başlık", validators=[DataRequired()])
    subtitle = StringField("Alt Başlık", validators=[DataRequired()])
    img_url = StringField("Fotoğraf Linki", validators=[DataRequired(), URL()])
    body = CKEditorField("İçerik", validators=[DataRequired()])
    submit = SubmitField("Gönder")

class CreateComment(FlaskForm):
    comment=CKEditorField("Yorum", validators=[DataRequired()])
    submit = SubmitField("Yorum Gönder")
