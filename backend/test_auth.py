import unittest
from backend import auth

class TestAuth(unittest.TestCase):
    def test_password_hashing(self):
        password = "secretpassword"
        hashed = auth.get_password_hash(password)
        self.assertTrue(auth.verify_password(password, hashed))
        self.assertFalse(auth.verify_password("wrongpassword", hashed))

    def test_jwt_generation(self):
        data = {"sub": "test@example.com"}
        token = auth.create_access_token(data)
        self.assertIsInstance(token, str)
        print(f"Generated Token: {token}")

if __name__ == '__main__':
    unittest.main()
