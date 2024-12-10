FROM python:3.12.6

# Create a non-root user and group named 'none-root-shahdin'
RUN groupadd -r none-root-shahdin && useradd -r -g none-root-shahdin none-root-shahdin

# Set the working directory
WORKDIR /code

# Copy requirements file and install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /code/

# Change ownership of the code directory to the non-root user 'none-root-shahdin'
RUN chown -R none-root-shahdin:none-root-shahdin /code

# Switch to the non-root user
USER none-root-shahdin

# Command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]