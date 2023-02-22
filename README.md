# S3MPython

S3MPython is a Python library for creating S3Model data models.


# Examples & Training

For S3Model training courses, see the [S3Model](https://s3model.com) website.

There is a repository called S3MPython_examples meant to be your first experience with S3MPython.

# Examples Installation

- Clone the [S3MPython_examples](https://github.com/twcook/S3M_Python_Training_examples.git) repository.
- See the [README.md](https://github.com/twcook/S3M_Python_Training_examples) file for instructions on how to install and run the examples.

# S3MPython Installation

Create a virtual environment for S3MPython. Suggestion: use the name S3MPython.

```pip install s3mpython```

See the **Project Integration** section of the [documentation](https://s3model.com/S3MPython/) for the next steps.


# Developing S3MPython

- Clone the master [repository](https://github.com/s3model/S3MPython)

- Change to the new S3MPython directory.
- Build the virtual environment using dev_requirements.txt. Suggestion: use the name S3MPython_dev.
- Create a new branch for your changes.
- Build and install your development branch into your S3MPython environment.

```
python3 setup.py sdist bdist_wheel

pip install e .
```
