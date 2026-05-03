from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_wtf.file import FileField, FileAllowed


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 80)])
    password = PasswordField('密码', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 80)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    real_name = StringField('真实姓名', validators=[Optional(), Length(0, 50)])
    phone = StringField('联系电话', validators=[Optional(), Length(0, 20)])


class LostItemForm(FlaskForm):
    title = StringField('物品名称', validators=[DataRequired(), Length(1, 200)])
    description = TextAreaField('详细描述', validators=[Optional()])
    category_id = SelectField('物品类别', coerce=int, validators=[DataRequired()])
    location = StringField('丢失地点', validators=[Optional(), Length(0, 200)])
    lost_time = DateTimeLocalField('丢失时间', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    image = FileField('物品图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片文件')
    ])
    contact_info = StringField('联系方式', validators=[Optional(), Length(0, 200)])


class FoundItemForm(FlaskForm):
    title = StringField('物品名称', validators=[DataRequired(), Length(1, 200)])
    description = TextAreaField('详细描述', validators=[Optional()])
    category_id = SelectField('物品类别', coerce=int, validators=[DataRequired()])
    location = StringField('拾获地点', validators=[Optional(), Length(0, 200)])
    found_time = DateTimeLocalField('拾获时间', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    image = FileField('物品图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片文件')
    ])
    contact_info = StringField('联系方式', validators=[Optional(), Length(0, 200)])
