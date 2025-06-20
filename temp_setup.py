
from setuptools import setup, find_packages

setup(
    name="field_services_app",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=4.2.0",
        "djangorestframework>=3.14.0",
        "django-cors-headers>=4.0.0",
        "drf-yasg>=1.21.5",
    ],
    author="Field Services App Team",
    author_email="contact@example.com",
    description="A comprehensive field services management application",
)
