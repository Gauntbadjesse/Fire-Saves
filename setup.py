from setuptools import setup, find_packages

setup(
    name='Fire Saves',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'opencv-python',
        'sounddevice',
        'mss',
        'numpy',
        'pillow',
        'requests',
        'tkinter',
        'keyboard',
        'scipy'
    ],  # Add any other required packages
    include_package_data=True,
    description='Your project description',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Gauntbadjesse/Fire-Saves',
    author='Jesse',
    author_email='your_email@example.com',
    license='MIT',  # Replace with your license type if applicable
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'console_scripts': [
            'your_project_name=main:main',  # Adjust the entry point
        ],
    },
)
