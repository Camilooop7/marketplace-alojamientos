from django.contrib.auth.password_validation import UserAttributeSimilarityValidator
from django.core.exceptions import ValidationError


class ValidacionSimilitudContrasena(UserAttributeSimilarityValidator):
    def get_error_message(self):
        return 'La contraseña es demasiado similar a la de %(verbose_name)s.'


class ValidacionComplejidadContrasena:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                'La contraseña es demasiado corta. Debe contener por lo menos 8 caracteres.',
                code='longitud_invalida')
        if len(password) > 64:
            raise ValidationError(
                'La contraseña no puede tener más de 64 caracteres.',
                code='longitud_invalida')
        if not any(caracter.isupper() for caracter in password):
            raise ValidationError(
                'La contraseña debe contener al menos una letra mayúscula.',
                code='sin_mayuscula')
        if not any(caracter.islower() for caracter in password):
            raise ValidationError(
                'La contraseña debe contener al menos una letra minúscula.',
                code='sin_minuscula')
        if not any(caracter.isdigit() for caracter in password):
            raise ValidationError(
                'La contraseña debe contener al menos un número.',
                code='sin_numero')
        if not any(not caracter.isalnum() and not caracter.isspace() for caracter in password):
            raise ValidationError(
                'La contraseña debe contener al menos un símbolo, por ejemplo # $ % &.',
                code='sin_simbolo')

    def get_help_text(self):
        return 'Entre 8 y 64 caracteres con mayúsculas, minúsculas, números y un símbolo.'