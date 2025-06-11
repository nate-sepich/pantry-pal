FROM public.ecr.aws/lambda/python:3.12

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure .env file is included
COPY .env .env

# Set the CMD to your Lambda handler
CMD ["app.lambda_handler"]
