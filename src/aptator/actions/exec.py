import subprocess


def exec_command(command):
    """Execute a shell command.
    
    Raises:
        subprocess.CalledProcessError: If the command exits with a non-zero status code.
    """
    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
