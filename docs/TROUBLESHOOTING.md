# Troubleshooting

## MCP health fails
- Verify `MCP_API_KEY` in `.env`
- Check `uvicorn` process and port `MCP_PORT`

## Database connection fails
- Validate `DATABASE_URL`
- Check postgres is ready: `pg_isready`

## Empty query result
- Confirm seed/sample data exists in target tables
- Check permission filters and confidentiality scope
