# Project Exhibition 2

A system that collects posts from Reddit, cleans them, analyzes emotions using AI, and displays the results on a dashboard.

## How It Works

The project has **4 independent services** that work together:

1. **Ingestion Service** - Fetches raw posts from Reddit
2. **Cleaning Service** - Cleans and processes the posts
3. **Analysis Service** - Uses AI to detect emotions in posts
4. **Dashboard Service** - Shows the data on a website

All services share a **PostgreSQL database** to store and retrieve data.

## Folder Structure

```
projectExhibition2/
│
├── frontend/       → The website/dashboard
├── ingestion/      → Gets posts from Reddit API
├── cleaning/       → Cleans and processes posts
├── model/          → AI analysis (emotion detection)
├── database/       → Database setup and tables
└── README.md       → This file
```


## Database Tables

- **raw_posts** - Original posts from Reddit
- **cleaned_posts** - Cleaned versions of the posts
- **enriched_posts** - Posts with emotion analysis added

## Getting Started

Each folder has its own setup instructions. Start with the database folder first, then run each service.

## Note

The database here is going to be a centralized database. So please design and build your servers according to the database, refrain making changes in the database schemas.

We would integrate the each module via servers, hence please use the following ports for the server.

- **Frontend** - ```port=8000```
- **Ingestion** - ```port=7000```
- **Cleaning** - ```port=6000```
- **Database** - ```port=5432```
- **model** - ```port=4000```