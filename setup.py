from setuptools import setup, find_packages
from pathlib import Path

# 读取README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='diss-king',
    version='0.1.0',
    author='DissKing Team',
    author_email='dissking@example.com',
    description='The AI that fights dirty so you don\'t have to',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourname/diss-king',
    packages=find_packages(),
    package_data={
        'diss_king': ['data/*.json', 'prompts/*.txt'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Chat',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
    keywords='argument fight trash-talk ai chat nlp',
    project_urls={
        'Bug Reports': 'https://github.com/yourname/diss-king/issues',
        'Source': 'https://github.com/yourname/diss-king',
    },
)
