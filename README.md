# revenue-leakage-agent

Agent to detect revenue leakage

## How to run the project

0. Add a .env file in the root directory with the following variables:
```
OPENAI_API_KEY=your-api-key-here
```
1. Run `make build` to build the Docker images
2. Run `make up` to start the services
3. Open http://localhost:3000 in your browser to see the frontend
4. Stop it with `make stop`

### Duration to implement the project
110 minutes

Tools used: Cursor, Sonnet 4.5
