from django.test import SimpleTestCase
from django.core.exceptions import ValidationError

from ..validators import ChatUsernameValidator


class TestChatUsernameValidator(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = ChatUsernameValidator()

    def test_valid_username(self):
        username = 'Qwertyuiop_asdfghjklzxcvNmDQOWZ173XCBVNMSDOIFD'
        self.validator(username)

    def test_invalid_username_with_dash(self):
        username = 'Qwertyuiop_asdfghjklzxcvNmDQOWZXC-BV173NMSDOIFD'
        with self.assertRaises(ValidationError):
            self.validator(username)

    def test_invalid_username_with_cyrillic(self):
        username = 'Qwertyuiop_asdfghjklzxcvNmDQOWZXC173BVNMSDOIFDЩ'
        with self.assertRaises(ValidationError):
            self.validator(username)

    def test_invalid_username_with_space(self):
        username = 'Qwertyuiop_asdfghjklzxcvNmDQOWZX C173BVNMSDOIFD'
        with self.assertRaises(ValidationError):
            self.validator(username)

    def test_invalid_username_with_symbols(self):
        username = 'Qwertyuiop_asdfghjklzxc?!:vNmDQOWZXC-BVNMSDOIFD'
        with self.assertRaises(ValidationError):
            self.validator(username)
