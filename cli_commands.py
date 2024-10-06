import os
from dotenv import load_dotenv, set_key
import requests
import click
from flask import current_app
from tabulate import tabulate


load_dotenv()

BASE_URL = 'http://localhost:5000/api/v1'
TOKEN = os.getenv('TOKEN')

@click.group()
def cli():
    """Main CLI group."""
    pass


def set_token(new_token):
    """Store the authentication token."""
    global token
    token = new_token


def get_headers():
    """Get the headers with the authentication token."""
    TOKEN = os.getenv('TOKEN') 
    headers = {'Authorization': f'Bearer {TOKEN}'} if TOKEN else {}
    return headers


# Authentication commands
@cli.group()
def auth():
    """Authentication commands."""
    pass


@auth.command('login')
def login():
    """Login command."""
    global TOKEN
    email = click.prompt("Email")
    password = click.prompt("Password", hide_input=True)
    response = requests.post(f'{BASE_URL}/auth/login', json={'email': email, 'password': password})
    
    if response.ok:
        TOKEN = response.json().get('access_token') # Store the token for further use
        set_key('.env', 'TOKEN', TOKEN)
        click.echo(TOKEN)
    else:
        click.echo(f"Login failed: {response.json()}")


@auth.command('signup')
def signup():
    """Signup command."""
    email = click.prompt("Email")
    username = click.prompt("Username")
    phone_number = click.prompt("Phone number")
    password = click.prompt("Password", hide_input=True)
    response = requests.post(f'{BASE_URL}/auth/signup', json={
        'email': email, 'username': username, 'password': password, 'phone_number': phone_number
    })
    click.echo(response.json())


@auth.command('verify')
def verify_account():
    """Account verification command."""
    verification_code = click.prompt("Verification Code")
    email = click.prompt("Email")
    response = requests.post(f'{BASE_URL}/auth/validate-code', json={'code': verification_code, 'email': email})
    click.echo(response.json())


@auth.command('forget')
def forget_password():
    """Forget password command."""
    email = click.prompt("Email")
    response = requests.post(f'{BASE_URL}/auth/password-reset', json={'email': email})
    click.echo(response.json())


@auth.command('reset')
def reset_password():
    """Reset password command."""
    email = click.prompt("Email")
    token = click.prompt("Token")
    new_password = click.prompt("New Password", hide_input=True)
    confirm_password = click.prompt("Confirm New Password", hide_input=True)
    response = requests.post(f'{BASE_URL}/auth/password-reset/verify', json={
        'email': email, 'token': token, 'new_password': new_password, 'confirm_password': confirm_password
    })
    click.echo(response.json())


# Community commands
@cli.group()
def community():
    """Community commands."""
    pass


@community.command('create')
def create_community():
    """Create a community."""
    name = click.prompt("Community Name")
    description = click.prompt("Description")

    response = requests.post(f'{BASE_URL}/communities', json={'name': name, 'description': description}, headers=get_headers())
    click.echo(response.json())


@community.command('list')
def list_communities():
    """List all communities."""
    response = requests.get(f'{BASE_URL}/communities', headers=get_headers())
    data = response.json().get('data', [])

    if not data:
        click.echo("No communities found.")
        return

    # Prepare data for table display
    table_data = []
    for community in data:
        table_data.append([community['communityId'], community['name'], community['description'], community['createdAt']])

    # Use tabulate to display the data in a clean table format
    headers = ['ID', 'Name', 'Description', 'Created At']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))


@community.command('join')
def join_community():
    """Join a community."""
    community_id = click.prompt("Community ID")
    response = requests.post(f'{BASE_URL}/communities/user-community/{community_id}', headers=get_headers())
    click.echo(response.json())

@community.command('get')
def get_community_by_id():
    community_id = click.prompt("Community ID")
    response = requests.get(f'{BASE_URL}/communities/{community_id}', headers=get_headers())
    # click.echo(response.json())
    data = response.json().get('data', {})

    if not data:
        click.echo("No communities found.")
        return

    # Prepare data for table display
    table_data = []
    table_data.append([data['communityId'], data['name'], data['description'], data['createdAt']])

    # Use tabulate to display the data in a clean table format
    headers = ['ID', 'Name', 'Description', 'Created At']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

@community.command('delete')
def delete_community():
    community_id = click.prompt("Community ID")
    response = requests.delete(f'{BASE_URL}/communities/{community_id}', headers=get_headers())
    click.echo(response.json())

@community.command('update')
def update_community():
    community_id = click.prompt("Community ID")
    name = click.prompt("New Community Name")
    description = click.prompt("New Description")
    response = requests.put(f'{BASE_URL}/communities/{community_id}', json={'name': name, 'description': description}, headers=get_headers())
    click.echo(response.json())

@community.command('leave')
def leave_community():
    community_id = click.prompt("Community ID")
    response = requests.delete(f'{BASE_URL}/communities/user-community/{community_id}', headers=get_headers())
    click.echo(response.json())

@community.command('joinedList')
def get_joined_communities():
    response = requests.get(f'{BASE_URL}/communities/user-community/0', headers=get_headers())
    data = response.json().get('data', [])

    if not data:
        click.echo("No communities found.")
        return

    # Prepare data for table display
    table_data = []
    for community in data:
        table_data.append([community['communityId'], community['name'], community['description'], community['joinedDate']])

    # Use tabulate to display the data in a clean table format
    headers = ['ID', 'Name', 'Description', 'joinedDate']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))



# You can continue similarly for other community commands like get_by_id, delete, etc.

# Post commands
@cli.group()
def post():
    """Post commands."""
    pass

# Post commands
@cli.command('post')
def post_commands():
    """Post commands."""
    action = click.prompt("Choose action (create, getbyid, list, update, delete, like, unlike)", type=str)
    
    if action == 'create':
        create_post()
    elif action == 'getbyid':
        get_post_by_id()
    elif action == 'list':
        list_posts_by_community_id()
    elif action == 'update':
        update_post()
    elif action == 'delete':
        delete_post()
    elif action == 'like':
        like_post()
    elif action == 'unlike':
        unlike_post()
    else:
        click.echo("Invalid command.")

def create_post():
    community_id = click.prompt("Community ID")
    content = click.prompt("Content")
    image_path = click.prompt("Image file path", type=click.Path(exists=True))

    # Ensure the file exists and is an image
    if not os.path.isfile(image_path):
        click.echo("File not found.")
        return

    # Open the image file for upload
    with open(image_path, 'rb') as image_file:
        # Prepare the form data
        files = {
            'image': image_file,  # Attach the image file
        }
        data = {
            'content': content,  # Text content
        }

        # Send the request as multipart/form-data
        response = requests.post(f'{BASE_URL}/communities/{community_id}/post', data=data, files=files, headers=get_headers())

        # Output the response
        click.echo(response.json())

def get_post_by_id():
    post_id = click.prompt("Post ID")
    response = requests.get(f'{BASE_URL}/communities/post/{post_id}', headers=get_headers())
    data = response.json()

    if not data:
        click.echo("No communities found.")
        return

    # Prepare data for table display
    table_data = []
    table_data.append([data['postId'], data['content'], data['createdAt'], data['likes'], data['imageUrl'], data['userId'], data['communityId']])

    # Use tabulate to display the data in a clean table format
    headers = ['ID', 'Content', 'CreatedAt', 'Likes', 'ImageUrl', 'UserId', 'CommunityId']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

def list_posts_by_community_id():
    community_id = click.prompt("Community ID")
    response = requests.get(f'{BASE_URL}/communities/{community_id}/post', headers=get_headers())
    data = response.json().get('data', [])

    if not data:
        click.echo("No communities found.")
        return

    table_data = []
    for community in data:
        table_data.append([community['postId'], community['content'], community['createdAt'], community['likes'], community['imageUrl'], community['userId'], community['communityId']])

    # Use tabulate to display the data in a clean table format
    headers = ['ID', 'Content', 'CreatedAt', 'Likes', 'ImageUrl', 'UserId', 'CommunityId']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

def update_post():
    post_id = click.prompt("Post ID")
    content = click.prompt("New Content")
    response = requests.put(f'{BASE_URL}/communities/post/{post_id}', json={'content': content}, headers=get_headers())
    click.echo(response.json())

def delete_post():
    post_id = click.prompt("Post ID")
    response = requests.delete(f'{BASE_URL}/communities/post/{post_id}', headers=get_headers())
    click.echo(response.json())

def like_post():
    post_id = click.prompt("Post ID")
    response = requests.post(f'{BASE_URL}/communities/post/{post_id}/like', headers=get_headers())
    click.echo(response.json())

def unlike_post():
    post_id = click.prompt("Post ID")
    response = requests.delete(f'{BASE_URL}/communities/post/{post_id}/like', headers=get_headers())
    click.echo(response.json())

# Comment commands
@cli.command('comment')
def comment_commands():
    """Comment commands."""
    action = click.prompt("Choose action (create, getbyid, update, delete)", type=str)
    
    if action == 'create':
        create_comment()
    elif action == 'getbyid':
        get_comments_by_post_id()
    elif action == 'update':
        update_comment()
    elif action == 'delete':
        delete_comment()
    else:
        click.echo("Invalid command.")

def create_comment():
    post_id = click.prompt("Post ID")
    content = click.prompt("Content")
    response = requests.post(f'{BASE_URL}/communities/post/{post_id}/comment', json={'content': content}, headers=get_headers())
    click.echo(response.json())

def get_comments_by_post_id():
    post_id = click.prompt("Post ID")
    response = requests.get(f'{BASE_URL}/communities/post/{post_id}/comment', headers=get_headers())
    data = response.json().get('data', [])

    if not data:
        click.echo("No communities found.")
        return

    table_data = []
    for community in data:
        table_data.append([community['commentId'], community['content'], community['createdAt'], community['postId'], community['userId']])

    # Use tabulate to display the data in a clean table format
    headers = ['ID', 'Content', 'CreatedAt', 'PostId', 'UserId']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

def update_comment():
    comment_id = click.prompt("Comment ID")
    content = click.prompt("New Content")
    response = requests.put(f'{BASE_URL}/communities/post/comment/{comment_id}', json={'content': content}, headers=get_headers())
    click.echo(response.json())

def delete_comment():
    comment_id = click.prompt("Comment ID")
    response = requests.delete(f'{BASE_URL}/communities/post/comment/{comment_id}', headers=get_headers())
    click.echo(response.json())


# Register the CLI with the Flask app
def register_cli(app):
    app.cli.add_command(cli)


if __name__ == "__main__":
    cli()
