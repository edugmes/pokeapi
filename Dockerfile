FROM python:3.8 as base

# 'builder' stage used only to generate compiling packages and pip dependencies
FROM base as builder

# Use PROD="True" to swap local for production pip requirements
ARG PROD

# Build-essential for compiling stuff
# Clean up /lists after packages installation to reduce image size
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install updates
RUN pip install --upgrade pip && mkdir /install

COPY requirements/* /tmp/

# automatically swaps development and production requirements based on PROD variable
RUN pip install --no-cache-dir --target /install -r /tmp/`if [ "$PROD" = "True" ]; then echo production; else echo local; fi`.txt \
    && rm -rf /tmp/

# 'release_image' stage copies only packages used by the application (drops compiling stuff)
FROM python:3.8-slim as release_image

# Update image packages and lists clean up
RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

# Copy previous stage installed/compiled packages
COPY --from=builder /install /usr/local

# Python variables settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/usr/local:$PATH \
    PYTHONPATH=/usr/local:$PYTHONPATH

# Create miscfiles dir (for general purpose) and add a different user than root
RUN mkdir /usr/src/miscfiles && useradd -U app_user && chown -R app_user:app_user /usr/src

# Change working directory and current user
WORKDIR /usr/src/
USER app_user:app_user

# Copy project files to final image
COPY --chown=app_user:app_user ./project .

# Clean up requirements list folder
RUN rm -f requirements/*