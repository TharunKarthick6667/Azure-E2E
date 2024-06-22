import streamlit as st
from azure.storage.blob import BlobServiceClient, BlobClient
from auth import get_auth_url, get_token_from_code, get_user_groups

# Azure Blob Storage details
blob_connection_string = 'DefaultEndpointsProtocol=https;AccountName=20320mdsplacement0025;AccountKey=wIWrRFbdwqN9FVHCux3GQPk+y5QczAJlVP07a9KSsPJCNhd1aT835hkpGYLBpL2yjDXHbGyeG1Tk+AStHEUxUw==;EndpointSuffix=core.windows.net'
placements_container_name = 'placements-2024'
archive_container_name = 'archive'
reject_container_name = 'reject'

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
placements_container_client = blob_service_client.get_container_client(placements_container_name)
archive_container_client = blob_service_client.get_container_client(archive_container_name)
reject_container_client = blob_service_client.get_container_client(reject_container_name)

# Define group names
upload_group = "UploadGroup"
list_files_group = "ListFilesGroup"

# Function to move file to archive container
def move_to_archive(file_name):
    blob_client = placements_container_client.get_blob_client(file_name)
    archive_blob_client = archive_container_client.get_blob_client(file_name)

    # Copy blob from placements-2024 container to archive container
    copy_blob(archive_blob_client, blob_client)

    st.success(f"File '{file_name}' moved to 'archive' container successfully!")

# Function to move file to reject container
def move_to_reject(file_name):
    blob_client = placements_container_client.get_blob_client(file_name)
    reject_blob_client = reject_container_client.get_blob_client(file_name)

    # Copy blob from placements-2024 container to reject container
    copy_blob(reject_blob_client, blob_client)

    st.success(f"File '{file_name}' moved to 'reject' container successfully!")

# Helper function to copy blob
def copy_blob(destination_blob_client, source_blob_client):
    # Start the copy operation
    copy_status = destination_blob_client.start_copy_from_url(source_blob_client.url)
    while copy_status['copy_status'] == 'pending':
        copy_status = destination_blob_client.get_blob_properties().copy

    # Ensure copy is complete
    if copy_status['copy_status'] == 'success':
        # Delete the original blob after copying
        source_blob_client.delete_blob()
    else:
        st.error("Failed to copy blob")

# Main function to define Streamlit UI and functionality
def main():
    st.title("File Upload and Approval System")

    if "auth_code" not in st.session_state:
        st.session_state.auth_code = st.experimental_get_query_params().get('code')

    if st.session_state.auth_code:
        token_result = get_token_from_code(st.session_state.auth_code)
        st.session_state.access_token = token_result['access_token']
        user_groups = get_user_groups(st.session_state.access_token)
        st.session_state.user_groups = [group['displayName'] for group in user_groups['value']]
    else:
        st.write(f"Please [login]({get_auth_url()}) to continue.")
        return

    # Sidebar navigation menu
    st.sidebar.title("Navigation")
    if upload_group in st.session_state.user_groups:
        page = st.sidebar.radio("Go to", ["Upload File"])
    elif list_files_group in st.session_state.user_groups:
        page = st.sidebar.radio("Go to", ["List Files"])
    else:
        st.sidebar.write("You do not have access to any pages.")
        return

    if page == "Upload File":
        st.header("Upload File")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])

        if uploaded_file is not None:
            blob_client = placements_container_client.get_blob_client(uploaded_file.name)
            blob_client.upload_blob(uploaded_file)
            st.success("File uploaded successfully!")
            st.sidebar.success("File uploaded successfully!")

    elif page == "List Files":
        st.header("List Files in Azure Blob Storage")
        blobs = placements_container_client.list_blobs()
        blob_names = [blob.name for blob in blobs]

        if len(blob_names) > 0:
            st.write("### Uploaded Files:")
    
            selected_file = st.selectbox("Select file to process", blob_names)

            if selected_file:
                action = st.selectbox("Select Action", ["Approve", "Reject"])

                if action == "Approve" and st.button("Move to Archive"):
                    move_to_archive(selected_file)
                elif action == "Reject" and st.button("Move to Reject"):
                    move_to_reject(selected_file)

        else:
            st.write("No files uploaded yet.")

if __name__ == "__main__":
    main()
