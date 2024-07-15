import uuid

def random_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"profile_pics/{filename}"