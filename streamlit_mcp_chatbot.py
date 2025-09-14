# app.py
import streamlit as st
import requests
import docker
from dotenv import load_dotenv
import json
import os

# Load environment variables from .env file
load_dotenv()
obsidian_api_key = os.getenv("OBSIDIAN_API_KEY")
obsidian_api_url = os.getenv("OBSIDIAN_API_http_URL")

# --- Page Configuration ---
st.set_page_config(
    page_title="MCP Chatbot",
    page_icon="💬",
    layout="wide"
)

# --- Session State Initialization ---
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Helper Functions ---
def get_docker_client():
    """Initializes and returns a Docker client."""
    try:
        # Connect to the local Docker daemon
        client = docker.from_env()
        return client
    except Exception as e:
        st.error(f"Error connecting to Docker: {e}")
        return None

# --- Obsidian MCP Commands ---
# The functions below now use the correct API endpoints for the Obsidian MCP server.

def list_files_in_vault():
    """
    Lists all files and directories in the root of the Obsidian vault.
    
    Returns:
        str: A formatted list of files or an error message.
    """
    OBSIDIAN_API_URL = f"{obsidian_api_url}/vault/"
    headers = {"Authorization": f"Bearer {obsidian_api_key}"}
    
    try:
        response = requests.get(OBSIDIAN_API_URL, headers=headers, verify=False)
        response.raise_for_status()
        files = response.json().get("files", [])
        
        if not files:
            return "No files found in the Obsidian vault."
        
        file_list = "### Obsidian Files\n"
        for file in files:
            file_list += f"- `{file}`\n"
        return file_list
    except requests.exceptions.RequestException as e:
        return f"Error listing files from Obsidian: {e}"

def list_files_in_dir(directory):
    """
    Lists all files and directories in a specific Obsidian directory.
    
    Args:
        directory (str): The path to the directory within the Obsidian vault.
    
    Returns:
        str: A formatted list of files or an error message.
    """
    OBSIDIAN_API_URL = f"{obsidian_api_url}/list_files_in_dir"
    headers = {"Authorization": f"Bearer {obsidian_api_key}"}
    
    try:
        response = requests.post(
            OBSIDIAN_API_URL, 
            headers=headers, 
            json={"directory": directory},
            verify=False
        )
        response.raise_for_status()
        files = response.json().get("files", [])
        
        if not files:
            return f"No files found in directory `{directory}`."
        
        file_list = f"### Files in `{directory}`\n"
        for file in files:
            file_list += f"- `{file}`\n"
        return file_list
    except requests.exceptions.RequestException as e:
        return f"Error listing files in directory from Obsidian: {e}"

def get_file_contents(filepath):
    """
    Returns the content of a single file in your vault.
    
    Args:
        filepath (str): The path to the file within the Obsidian vault.
    
    Returns:
        str: The content of the file or an error message.
    """
    OBSIDIAN_API_URL = f"{obsidian_api_url}/get_file_contents"
    headers = {"Authorization": f"Bearer {obsidian_api_key}"}
    
    try:
        response = requests.post(
            OBSIDIAN_API_URL, 
            headers=headers, 
            json={"filepath": filepath},
            verify=False
        )
        response.raise_for_status()
        return response.json().get("content", "File content not found.")
    except requests.exceptions.RequestException as e:
        return f"Error reading file from Obsidian: {e}"

def append_content(filepath, content):
    """
    Appends content to a new or existing file in the vault.
    
    Args:
        filepath (str): The path to the file within the Obsidian vault.
        content (str): The content to append to the file.
        
    Returns:
        str: A success or error message.
    """
    OBSIDIAN_API_URL = f"{obsidian_api_url}/append_content"
    headers = {"Authorization": f"Bearer {obsidian_api_key}"}
    
    try:
        response = requests.post(
            OBSIDIAN_API_URL, 
            headers=headers, 
            json={"filepath": filepath, "content": content},
            verify=False
        )
        response.raise_for_status()
        return "Content successfully appended."
    except requests.exceptions.RequestException as e:
        return f"Error appending content to Obsidian: {e}"

def patch_content(filepath, patch_type, patch_target, new_content):
    """
    Inserts content into an existing note relative to a heading, block reference, or frontmatter field.

    Args:
        filepath (str): The path to the file within the Obsidian vault.
        patch_type (str): The type of patch to apply (e.g., 'heading', 'block', 'frontmatter').
        patch_target (str): The specific target for the patch (e.g., a heading name, block ID, or frontmatter key).
        new_content (str): The content to insert.

    Returns:
        str: A success or error message.
    """
    OBSIDIAN_API_URL = f"{obsidian_api_url}/patch_content"
    headers = {"Authorization": f"Bearer {obsidian_api_key}"}

    payload = {
        "filepath": filepath,
        "patch": {
            "type": patch_type,
            "target": patch_target,
            "content": new_content
        }
    }

    try:
        response = requests.post(
            OBSIDIAN_API_URL,
            headers=headers,
            json=payload,
            verify=False
        )
        response.raise_for_status()
        return "Content successfully patched."
    except requests.exceptions.RequestException as e:
        return f"Error patching content to Obsidian: {e}"

def search_obsidian_vault(query):
    """
    Searches for documents matching a specified text query.
    
    Args:
        query (str): The text query to search for.
        
    Returns:
        str: A formatted list of matching files or an error message.
    """
    OBSIDIAN_API_URL = f"{obsidian_api_url}/search"
    headers = {"Authorization": f"Bearer {obsidian_api_key}"}
    
    try:
        response = requests.post(
            OBSIDIAN_API_URL, 
            headers=headers, 
            json={"query": query},
            verify=False
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        
        if not results:
            return f"No results found for query `{query}`."
        
        result_list = f"### Search Results for `{query}`\n"
        for result in results:
            result_list += f"- `{result}`\n"
        return result_list
    except requests.exceptions.RequestException as e:
        return f"Error searching Obsidian vault: {e}"

def delete_obsidian_file(filepath):
    """
    Deletes a file or directory from the Obsidian vault.
    
    Args:
        filepath (str): The path to the file or directory to delete.
    
    Returns:
        str: A success or error message.
    """
    OBSIDIAN_API_URL = f"{obsidian_api_url}/delete_file"
    headers = {"Authorization": f"Bearer {obsidian_api_key}"}
    
    try:
        response = requests.post(
            OBSIDIAN_API_URL, 
            headers=headers, 
            json={"filepath": filepath},
            verify=False
        )
        response.raise_for_status()
        return f"File `{filepath}` successfully deleted."
    except requests.exceptions.RequestException as e:
        return f"Error deleting file from Obsidian: {e}"

# --- Docker MCP Commands (Working Example) ---

def list_docker_images():
    """Lists all Docker images."""
    client = get_docker_client()
    if not client:
        return "Failed to connect to Docker."
    try:
        images = client.images.list()
        if not images:
            return "No Docker images found."
        
        image_list = "### Docker Images\n"
        for image in images:
            image_list += f"- **ID:** `{image.short_id}`\n"
            image_list += f"  - **Tags:** `{', '.join(image.tags)}`\n"
        return image_list
    except Exception as e:
        return f"Error listing images: {e}"

def list_docker_containers():
    """Lists all running Docker containers."""
    client = get_docker_client()
    if not client:
        return "Failed to connect to Docker."
    try:
        containers = client.containers.list()
        if not containers:
            return "No running containers found."
        
        container_list = "### Running Docker Containers\n"
        for container in containers:
            container_list += f"- **Name:** `{container.name}`\n"
            container_list += f"  - **ID:** `{container.short_id}`\n"
            container_list += f"  - **Image:** `{container.image.tags[0] if container.image.tags else 'N/A'}`\n"
            container_list += f"  - **Status:** `{container.status}`\n"
        return container_list
    except Exception as e:
        return f"Error listing containers: {e}"

def create_docker_container(image_name):
    """
    Creates and runs a new Docker container from a specified image.
    
    Args:
        image_name (str): The name of the Docker image to use.
        
    Returns:
        str: A success or error message.
    """
    client = get_docker_client()
    if not client:
        return "Failed to connect to Docker."
        
    try:
        st.session_state.messages.append({"role": "assistant", "content": f"Creating container from image `{image_name}`..."})
        st.session_state.rerun = True # To update the UI immediately
        
        # Check if the image exists, and pull it if not
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            st.session_state.messages.append({"role": "assistant", "content": f"Image `{image_name}` not found locally. Pulling from Docker Hub..."})
            client.images.pull(image_name)

        container = client.containers.run(image_name, detach=True)
        return f"Container `{container.name}` successfully created and started from `{image_name}`. ID: `{container.short_id}`"
    except docker.errors.ImageNotFound:
        return f"Error: Image `{image_name}` not found on Docker Hub."
    except Exception as e:
        return f"Error creating container: {e}"

# --- Chatbot UI and Logic ---

st.title("MCP Chatbot")
st.markdown("Enter a command to interact with your Obsidian and Docker servers. Use `/help` for a list of available commands.")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Enter a command..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process assistant response
    response_content = ""
    command = prompt.strip().lower()
    
    if command.startswith("/help"):
        response_content = (
            "### Available Commands:\n"
            "- `/help`: Show this help message.\n"
            "- `/obsidian_list_all`: List all files and directories in the root of the Obsidian vault.\n"
            "- `/obsidian_list_dir [directory]`: List files and directories in a specific Obsidian directory.\n"
            "- `/obsidian_get_content [filepath]`: Read a file from the Obsidian vault.\n"
            "- `/obsidian_append [filepath] [content]`: Append content to an Obsidian file.\n"
            "- `/obsidian_patch [filepath] [patch_type] [patch_target] [new_content]`: Patch content to an Obsidian file.\n"
            "- `/obsidian_search [query]`: Search for text in the Obsidian vault.\n"
            "- `/obsidian_delete [filepath]`: Delete a file or directory from the Obsidian vault.\n"
            "- `/docker_list_images`: List all Docker images.\n"
            "- `/docker_list_containers`: List all running Docker containers.\n"
            "- `/docker_create [image_name]`: Create and run a container from an image."
        )
    elif command.startswith("/obsidian_list_all"):
        response_content = list_files_in_vault()
    elif command.startswith("/obsidian_list_dir "):
        directory = command.split("/obsidian_list_dir ", 1)[1].strip()
        response_content = list_files_in_dir(directory)
    elif command.startswith("/obsidian_get_content "):
        filepath = command.split("/obsidian_get_content ", 1)[1].strip()
        response_content = get_file_contents(filepath)
    elif command.startswith("/obsidian_append "):
        try:
            parts = command.split("/obsidian_append ", 1)[1].strip().split(" ", 1)
            filepath = parts[0]
            content = parts[1]
            response_content = append_content(filepath, content)
        except IndexError:
            response_content = "Invalid command format. Usage: `/obsidian_append [filepath] [content]`"
    elif command.startswith("/obsidian_patch "):
        try:
            parts = command.split("/obsidian_patch ", 1)[1].strip().split(" ", 3)
            filepath = parts[0]
            patch_type = parts[1]
            patch_target = parts[2]
            new_content = parts[3]
            response_content = patch_content(filepath, patch_type, patch_target, new_content)
        except IndexError:
            response_content = "Invalid command format. Usage: `/obsidian_patch [filepath] [patch_type] [patch_target] [new_content]`"
    elif command.startswith("/obsidian_search "):
        query = command.split("/obsidian_search ", 1)[1].strip()
        response_content = search_obsidian_vault(query)
    elif command.startswith("/obsidian_delete "):
        filepath = command.split("/obsidian_delete ", 1)[1].strip()
        response_content = delete_obsidian_file(filepath)
    elif command.startswith("/docker_list_images"):
        response_content = list_docker_images()
    elif command.startswith("/docker_list_containers"):
        response_content = list_docker_containers()
    elif command.startswith("/docker_create "):
        image_name = command.split("/docker_create ", 1)[1].strip()
        response_content = create_docker_container(image_name)
    else:
        response_content = "I don't understand that command. Please type `/help` for a list of commands."

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(response_content)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_content})
