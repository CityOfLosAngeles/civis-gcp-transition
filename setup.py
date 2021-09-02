from setuptools import find_packages, setup

setup(
    name='common_utils',
    packages=find_packages(),
    version='0.1.0',
    description='Transition Civis jobs to Google Cloud Platform',
    author='City of Los Angeles',
    license='Apache',
    package_dir={"common_utils": "common_utils"},
    include_package_data=True,
    install_requires=["sendgrid", "arcgis"],
)