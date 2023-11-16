https://cloud.google.com/functions/docs/create-deploy-http-python


## Development
Add a .env.yaml file with the following content:

    OPENAI_API_KEY: YOUR_KEY


To develop locally, first run:
    
    export OPENAI_API_KEY=YOUR_KEY

... then run `functions-framework --target analyze --debug` and then test on http://127.0.0.1:8080/

## Deployment
Run `./bin/deploy.sh`

https://us-central1-genlabhackathon.cloudfunctions.net/analyze
