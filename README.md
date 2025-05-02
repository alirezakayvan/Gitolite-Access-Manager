# Gitolite Access Manager
This project provides a complete solution for managing access to Gitolite repositories using a centralized database and automation tools.

It includes:

    A PHP-based Web UI for managing user access to Git repositories, branches, and tags

    A Python script that reads access data from the database and updates Gitolite's configuration (via cron job)

    A modular structure designed for future integration with Docker and CI/CD environments

The goal is to simplify and centralize Git permission management for teams and organizations, especially in environments using Gitolite as an internal Git server
