# Lambda container image for stock dashboard API
FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY docker/requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy function code
COPY src/lambda/ ${LAMBDA_TASK_ROOT}/

# Set the handler
CMD ["handler.main"]
