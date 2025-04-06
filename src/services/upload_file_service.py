import cloudinary
import cloudinary.uploader


class UploadFileService:
    """
    Service for handling file uploads to Cloudinary.

    This service provides functionality to upload files to Cloudinary storage
    and generate accessible URLs for the uploaded resources.
    """

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """
        Initialize the UploadFileService with Cloudinary credentials.

        Args:
            cloud_name: Cloudinary cloud name for the account.
            api_key: Cloudinary API key for authentication.
            api_secret: Cloudinary API secret for authentication.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username: str) -> str:
        """
        Upload a file to Cloudinary and return its accessible URL.

        Args:
            file: The file object to upload (expected to have a .file attribute).
            username: Username to use in the file's public ID for organization.

        Returns:
            str: A URL to access the uploaded file with specified transformations.

        Note:
            - The file is uploaded with overwrite=True, so existing files with
              the same public_id will be replaced.
            - The generated URL includes transformations for 250x250 crop fill.
            - Files are organized under 'RestApp/{username}' in Cloudinary.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
