from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

class ReferralCodeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.referring_user = User.objects.create_user(
            username="referrer",
            email="referrer@example.com",
            password="testpassword",
            referral_code="REF12345"
        )

    def test_user_registration_with_referral_code(self):
        response = self.client.post('/api/accounts/register/', {
            'username': 'new_user',
            'email': 'new_user@example.com',
            'password1': 'password123',
            'password2': 'password123',
            'referred_by': 'REF12345'
        })

        self.assertEqual(response.status_code, 201)
        new_user = User.objects.get(username='new_user')
        self.assertEqual(new_user.referred_by, self.referring_user)
        self.referring_user.refresh_from_db()
        self.assertEqual(self.referring_user.profile.points, 10)  # Example points added

    def test_user_registration_without_referral_code(self):
        response = self.client.post('/api/accounts/register/', {
            'username': 'new_user2',
            'email': 'new_user2@example.com',
            'password1': 'password123',
            'password2': 'password123',
        })

        self.assertEqual(response.status_code, 201)
        new_user = User.objects.get(username='new_user2')
        self.assertIsNone(new_user.referred_by)
    def test_get_referral_code_for_logged_in_user(self):
        self.client.force_authenticate(user=self.referring_user)
        response = self.client.get('/api/accounts/referral-code/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['referral_code'], 'REF12345')    
# Create your tests here.
