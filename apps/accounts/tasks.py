from celery import shared_task
from PIL import Image
import io
from django.core.files.base import ContentFile
import os


@shared_task
def optimize_profile_image(profile_id):
    from .models import Profile

    try:
        profile = Profile.objects.get(id=profile_id)
        if not profile.profile_picture:
            return "No image to optimize"

        # Open the image
        img = Image.open(profile.profile_picture.path)

        # Resize to standard size (e.g., 500x500 px)
        img.thumbnail((500, 500))

        # Get the file extension
        file_name, file_ext = os.path.splitext(profile.profile_picture.name)

        # Save as optimized JPEG
        buffer = io.BytesIO()
        img.convert('RGB').save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        # Update the image file
        profile.profile_picture.save(
            f"{file_name}_optimized.jpg",
            ContentFile(buffer.read()),
            save=False
        )
        profile.save()

        return f"Image optimized: {profile.profile_picture.url}"

    except Profile.DoesNotExist:
        return f"Profile with ID {profile_id} not found"
    except Exception as e:
        return f"Error optimizing image: {str(e)}"