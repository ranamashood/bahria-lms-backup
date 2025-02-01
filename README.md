## Purpose

To backup all the data from your Bahria University LMS account as you will have no control over your data after the graduation.

## Usage

### VENV (Optional)

If you prefer to use virtual environment then follow the steps below.

Create a virtual environment using following command

```bash
python -m venv .venv
```

Copy the command for your specific environment from the [documentation](https://docs.python.org/3/library/venv.html#how-venvs-work).

For example, for me it was

```bash
source .venv/bin/activate.fish
```

### Install Packages

```bash
pip install -r requirements.txt
```

### Starting the script

```bash
python main.py
```

It will then ask for a session cookie. You can use any of the following methods to get that cookie.

#### Manual

Open Bahria LMS, open the console in the browser and then copy and paste the following text into the console.

```js
document.cookie.split("=")[1];
```

#### Automatic (Chrome Extension)

You can install my [extension](https://github.com/ranamashood/bahria-tools) to get the session cookie.
