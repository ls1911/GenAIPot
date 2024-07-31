from setuptools import setup, find_packages

setup(
    name='GenAIPot',
    version='0.1.0',
    description='The first Generative A.I Honeypot',
    author='Nuceon Cyber',
    author_email='contact@nucleon.sh',
    url='https://github.com/ls1911/GenAIPot',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'genaipot=src.main:main',  # Adjust the entry point if necessary
        ],
    },
    install_requires=[
        'twisted',
        'halo',
        'openai',
        'art',
	'matplotlib',
	'openai',
	'pandas',
	'prophet'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNUv3 License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
