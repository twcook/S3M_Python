# Tutorials

See the *S3Model Introduction Tutorial* in the [User Guide](https://s3model.com/userguide/docs/index.html) for an easy to follow and very informative introduction to S3Model.

## Examples

- Create a directory for testing the *Examples*:

  ```
  mkdir S3MPythonExamples
  ```

- Change to the directory:

  ```
  cd S3MPythonExamples
  ```

- Create a virtual environment. Here we are using [Anaconda](https://www.anaconda.com/products/individual).:

  ```
  conda create -n S3MPythonExamples python pip
  ```

- Activate the environment:

  ```
  conda activate S3MPythonExamples
  ```

- Install S3MPython:

  ```
  pip install S3MPython
  ```

- Now you must follow the instructions for **Project Integration**.

See the {ref}`Initialization and Configuration documentation <init>` for the next steps.

### Additional Tutorials

- **DataModel01.py** creates a full data model like the one from the [Introduction tutorial](https://s3model.com/userguide/docs/Setup.html).
- **DataModel02.py** creates a data model example for an [IoT device](https://internetofthingsagenda.techtarget.com/definition/IoT-device). Specifically a ??????

### Remove Example Environment

Use these commands:

```
conda deactivate
conda remove --name S3MPythonExamples --all
```
