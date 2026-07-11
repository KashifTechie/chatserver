import uuid

from django.test import SimpleTestCase

from chat.serializers.blocks import BlockCreateRequestSerializer


class BlockSerializerTests(SimpleTestCase):
    def test_create_request_serializer_requires_user(self):
        serializer = BlockCreateRequestSerializer(data={"reason": "spam"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("user", serializer.errors)

    def test_create_request_serializer_accepts_valid_payload(self):
        user_id = uuid.uuid4()
        serializer = BlockCreateRequestSerializer(
            data={"user": str(user_id), "reason": "spam"}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], user_id)
        self.assertEqual(serializer.validated_data["reason"], "spam")
