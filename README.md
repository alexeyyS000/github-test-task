GitHub Repository Viewer is a Django application with GitHub authentication (OAuth2).
After logging in (.../users/login), users can view their repositories, including their description, number of stars, forks, and language.
Each time they log in, their data is automatically synced with the GitHub API to ensure the information stays up-to-date.
The application also displays the user's GitHub avatar and allows them to securely log out.