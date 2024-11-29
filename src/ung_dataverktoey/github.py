import os
import subprocess

def initialize_local_repo():
    """
    Initialiserer det lokale prosjektet som et Git-repository hvis det ikke allerede er initialisert.
    """
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"])
    else:
        print("Repository is already initialized.")

def add_files_to_repo():
    """
    Legger til filer i det lokale repository.
    """
    subprocess.run(["git", "add", "."])

def commit_files(commit_message: str):
    """
    Gjør en commit av de stagede filene.

    Parameters
    ----------
    commit_message : str
        Commit-meldingen.
    """
    subprocess.run(["git", "commit", "-m", commit_message])

def add_remote_repo(remote_url: str):
    """
    Legger til en fjern-repository URL.

    Parameters
    ----------
    remote_url : str
        URL til fjern-repository.
    """
    subprocess.run(["git", "remote", "add", "origin", remote_url])

def push_to_github():
    """
    Pusher endringene til GitHub.
    """
    subprocess.run(["git", "push", "-f", "origin", "master"])

if __name__ == "__main__":
    remote_url = input("Enter the remote repository URL: ")
    
    initialize_local_repo()
    add_files_to_repo()
    commit_files("initial commit")
    add_remote_repo(remote_url)
    push_to_github()