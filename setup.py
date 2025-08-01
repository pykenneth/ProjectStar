from setuptools import setup, find_packages

# Static version definition
VERSION = '0.1'

setup(
    name="field_services_app",
    version="0.1",  # Using static version
    packages=find_packages(),
    include_package_data=True,  # Include non-python files from MANIFEST.in
    install_requires=[
        "Django==4.2.0",
        "djangorestframework==3.14.0",
        "django-cors-headers==4.0.0",
        "psycopg2-binary==2.9.6",
        "Pillow==9.5.0",
        "celery==5.2.7",
        "redis==4.5.4",
        "djangorestframework-simplejwt==5.2.2",
        "django-allauth==0.54.0",
        "django-mptt==0.14.0",
        "drf-yasg==1.21.5",
        "twilio==8.0.0",
        "geopy==2.3.0",
        "folium==0.14.0",
        "python-dotenv==1.0.0",
        "django-filter==23.1",
        "django-crispy-forms==2.0",
        "django-storages==1.13.2",
        "boto3==1.26.115",
        "gunicorn==20.1.0",
        "whitenoise==6.4.0",
        "django-phonenumber-field==8.1.0",
        "phonenumbers==8.13.31",
    ],
    author="Field Services App Team",
    author_email="contact@example.com",
    description="A comprehensive field services management application",
    keywords="field service, project management, work orders",
    url="https://github.com/yourusername/field_services_app",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/field_services_app/issues",
        "Documentation": "https://github.com/yourusername/field_services_app/wiki",
        "Source Code": "https://github.com/yourusername/field_services_app",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
