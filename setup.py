import setuptools
import pkgutil

setuptools.setup(
    name="kahana-mturk-tools",
    version="0.0.1",
    author="Connor Keane",
    author_email="ckeane1@sas.upenn.edu",
    description="Tools for creating and post processing mturk experiments made with jsPsych and hosted with PsiTurk",
    packages = setuptools.find_packages(),
    python_requires='>=3.8',
)
