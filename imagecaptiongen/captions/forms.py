from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed
from wtforms.fields import MultipleFileField
from wtforms import StringField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, ValidationError



class PredictForm(FlaskForm):
    image_pred = MultipleFileField('Select Images', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    url_image = StringField('Image URL')
    model = SelectMultipleField('Models', choices=[('blip', 'BLIP (Recommended)'), ('git', 'GIT ')],
                                option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
    submit = SubmitField('Predict')

    def validate_model(self, model):
        if not model.data:
            raise ValidationError('At least one model must be selected.')
        valid_models = ['blip', 'git']
        invalid_models = set(model.data) - set(valid_models)
        if invalid_models:
            raise ValidationError(f'Select appropriate model(s). Invalid model(s): {", ".join(invalid_models)}')

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        if not self.image_pred.data and not self.url_image.data:
            msg = 'Either an image or a URL must be provided.'
            self.image_pred.errors.append(msg)
            self.url_image.errors.append(msg)
            return False
        return True

class UpdateCaptionForm(FlaskForm):
    caption = StringField('Caption', validators=[DataRequired(), Length(min=2, max=200)])
    submit = SubmitField('Update Caption')