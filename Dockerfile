version: "1"
projects:
- name: My project
  environments:
  - name: Production
    # This section defines your Python application
    services:
      - type: web
        name: my-python-app
        env: python
        # This updated command installs the compiler needed for lru-dict
        buildCommand: "apt-get update && apt-get install -y build-essential && pip install -r requirements.txt"
        startCommand: "gunicorn my_app:app" # Replace with your actual start command (e.g., 'python main.py')
        envVars:
          - key: DATABASE_URL
            fromDatabase:
              name: airdrop-db
              property: connectionString
    
    # This is the database you already have defined
    databases:
    - name: airdrop-db
      databaseName: airdrop_db
      user: airdrop_db_user
      plan: free
      region: oregon
      ipAllowList:
      - source: 0.0.0.0/0
        description: everywhere
      postgresMajorVersion: "18"
