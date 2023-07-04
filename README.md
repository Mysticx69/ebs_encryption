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
- [4. Using pre-commit for Automated Checks](#4-using-pre-commit-for-automated-checks)
  - [4.1. Installation](#41-installation)
  - [4.2. Setting Up pre-commit for the Project](#42-setting-up-pre-commit-for-the-project)
  - [4.3. Running pre-commit](#43-running-pre-commit)
  - [4.4. Updating pre-commit](#44-updating-pre-commit)
  - [4.5. Uninstalling pre-commit](#45-uninstalling-pre-commit)
- [5. Pre-commit Configuration](#5-pre-commit-configuration)
  - [5.1. pre-commit-hooks](#51-pre-commit-hooks)
  - [5.2. pygrep-hooks](#52-pygrep-hooks)
  - [5.3. reorder\_python\_imports](#53-reorder_python_imports)
  - [5.4. pydocstyle](#54-pydocstyle)
  - [5.5. black](#55-black)


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


## 4. Using pre-commit for Automated Checks

This project uses pre-commit, a framework for managing and maintaining multi-language pre-commit hooks. Pre-commit can be used to manage the hooks that are run before every commit, helping to catch issues before they are submitted for code review.

### 4.1. Installation

If you haven't installed pre-commit yet, you can do so by running:

```bash
pip install pre-commit
```

### 4.2. Setting Up pre-commit for the Project

Once pre-commit is installed, you can set it up for the project by navigating to the project's directory and running:

```bash
pre-commit install
```

This command will install the pre-commit script in your `.git/hooks/` directory. This script will be run before every commit to check your code using the tools configured in the `.pre-commit-config.yaml` file.

### 4.3. Running pre-commit

After the installation is complete, pre-commit will run automatically on `git commit`. If any of the checks fail, the commit will be aborted.

You can manually run all pre-commit hooks on all files with:

```bash
pre-commit run --all-files
```

Or you can run individual hooks on all staged files like this:

```bash
pre-commit run <hook_id>
```

Remember to replace `<hook_id>` with the id of the hook you want to run.

### 4.4. Updating pre-commit

To upgrade to the latest versions of the hooks, run:

```bash
pre-commit autoupdate
```

This will update the versions of the hooks to the latest ones specified in the `.pre-commit-config.yaml` file.

### 4.5. Uninstalling pre-commit

If you want to uninstall pre-commit from your git hooks, you can do so by running:

```bash
pre-commit uninstall
```

This will remove the pre-commit script from your `.git/hooks/` directory.

Sure, here's how you can document the pre-commit configuration for your project:

## 5. Pre-commit Configuration

This project uses the following pre-commit hooks:

### 5.1. pre-commit-hooks

A collection of common pre-commit checks by the pre-commit project itself.

- `trailing-whitespace`: This hook trims trailing whitespace.
- `end-of-file-fixer`: This hook ensures that a file is either empty, or ends with one newline.
- `check-added-large-files`: This hook prevents giant files from being committed. The maximum file size is set to 1000KB.
- `check-ast`: This hook checks python ast (abstract syntax tree) for syntax errors.
- `fix-encoding-pragma`: This hook adds `coding: utf-8` to the top of python files.

### 5.2. pygrep-hooks

A collection of hooks based on python's `re` module.

- `python-use-type-annotations`: This hook enforces the use of Python 3 type annotations.

### 5.3. reorder_python_imports

A hook for automatically reordering python imports.

- `reorder-python-imports`: This hook reorders python imports in a way that complies with PEP8.

### 5.4. pydocstyle

A static analysis tool for checking compliance with Python docstring conventions.

- `pydocstyle`: This hook checks your Python docstrings against some of the conventions in PEP 257.

### 5.5. black

The uncompromising Python code formatter.

- `black`: This hook keeps your Python code formatted consistently according to the Black code style.

The specific versions of these hooks are defined in the `.pre-commit-config.yaml` file in the root of the repository.

To use these hooks, make sure you have pre-commit installed (see the [Using pre-commit for Automated Checks](#using-pre-commit-for-automated-checks) section), then run `pre-commit install` in your local repository. The hooks will then be run automatically each time you commit.
