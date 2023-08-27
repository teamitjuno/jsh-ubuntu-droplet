from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model


def handle_avatar_upload(user, avatar_file):
    User = get_user_model()
    # Open the image file and resize it
    img = Image.open(avatar_file)
    img = img.resize((150, 150))

    # Save the resized image to a BytesIO object
    bio = BytesIO()
    img.save(bio, "JPEG")

    # Get the UserProfile for this user, or create a new one if it doesn't exist
    profile = User.objects.get(id=user.id)

    # Save the binary image data to the avatar field
    profile.avatar.save("avatar.jpg", ContentFile(bio.getvalue()))  # type:ignore
    profile.save()  # type:ignore
