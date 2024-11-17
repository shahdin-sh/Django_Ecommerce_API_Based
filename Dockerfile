FROM python:3.12.6

# Create a non-root user and group
RUN groupadd -r shahdin && useradd -r -g shahdin shahdin

# Set the working directory
WORKDIR /code

# Copy requirements file and install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /code/

# Change ownership of the code directory to the non-root user
RUN chown -R shahdin:shahdin /code

# Switch to the non-root user
USER shahdin

# Command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]