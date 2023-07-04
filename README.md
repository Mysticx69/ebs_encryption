 <h1>Documentation</h1>

 <h2>Sommaire</h2>

- [1. EBS Unencrypted Infos](#1-ebs-unencrypted-infos)
- [2. Encrypt EBS volumes](#2-encrypt-ebs-volumes)
- [3. Using Pipenv for Dependency Management](#3-using-pipenv-for-dependency-management)
  - [3.1. Installation](#31-installation)
  - [3.2. Setting Up Your Project](#32-setting-up-your-project)
  - [3.3. Activating the Virtual Environment](#33-activating-the-virtual-environment)
  - [3.4. Running Python Scripts](#34-running-python-scripts)
  - [3.5. Managing Dependencies](#35-managing-dependencies)
  - [3.6. Exiting the Virtual Environment](#36-exiting-the-virtual-environment)


> Please set-up the requirements first !

## 1. EBS Unencrypted Infos

Link for the doc: [Gather Unencrypted EBS Infos](./gather_infos.md)

## 2. Encrypt EBS volumes

Link for the doc: [Encrypt Instances Volumes](./encrypt_ebs.md)


## 3. Using Pipenv for Dependency Management

This project uses Pipenv, a tool that aims to bring the best of all packaging worlds to the Python world. It harnesses Pipfile, pip, and virtualenv into one single command.

### 3.1. Installation

If you haven't installed Pipenv yet, you can do so by running:

```bash
pip install pipenv
```

### 3.2. Setting Up Your Project

Once Pipenv is installed, you can set up the project's environment and install all the necessary dependencies by navigating to the project's directory and running:

```bash
pipenv install
```

This command does two things:

1. If a `Pipfile` is present, `pipenv install` will create a new virtual environment (if one doesn't already exist) and then install the packages specified in the `Pipfile`.

2. If a `Pipfile.lock` is present, it will also be considered, and the dependencies will be installed as specified in the `Pipfile.lock` file, ensuring that the installed packages and their versions are consistent across different environments.

### 3.3. Activating the Virtual Environment

After the installation is complete, you can activate the Pipenv shell by running:

```bash
pipenv shell
```

This will spawn a new shell subprocess, which can be deactivated by using the `exit` command.

### 3.4. Running Python Scripts

Once the Pipenv shell is activated, you can run the Python scripts using the Python command followed by the script name:

```bash
python script_name.py
```

Remember to replace `script_name.py` with the name of the script you want to run.

### 3.5. Managing Dependencies

To install a new package and add it to `Pipfile`, you can use the `pipenv install` command followed by the package name:

```bash
pipenv install package_name
```

Remember to replace `package_name` with the name of the package you want to install.

To remove a package and remove it from `Pipfile`, you can use the `pipenv uninstall` command followed by the package name:

```bash
pipenv uninstall package_name
```

Remember to replace `package_name` with the name of the package you want to uninstall.

### 3.6. Exiting the Virtual Environment

When you're done working on your project, you can exit the virtual environment by simply typing:

```bash
exit
```

This will return you to your normal command prompt.
