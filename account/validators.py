from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class ChatUsernameValidator(RegexValidator):
    regex = r"^[a-zA-Z][a-zA-Z0-9_]+\Z"
    message = ("Enter a valid username. This value may contain only letters, numbers, _ characters, "
               "and start with letter.")
