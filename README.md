Okay, here's a comprehensive `README.md` file for the project, incorporating the details from your provided code, Dockerfile, and docker-compose file:

# FastAPI File Conversion API

This project provides a REST API built with FastAPI for converting various document formats, such as DOCX to HTML, DOCX to PDF, PDF to DOCX, and PDF to HTML. It leverages LibreOffice for document conversions and uses Redis for logging. Additionally, it includes an implementation of Spire.Doc for DOCX to HTML conversion.

## Features

-   **DOCX to HTML Conversion:** Converts DOCX files to HTML using LibreOffice and Spire.Doc.
-   **DOCX to PDF Conversion:** Converts DOCX files to PDF using LibreOffice.
-   **PDF to DOCX Conversion:** Converts PDF files to DOCX using LibreOffice.
-   **PDF to HTML Conversion:** Converts PDF files to HTML via an intermediate DOCX using LibreOffice.
-   **API Versioning:** Uses API versioning using FastAPI Routers
-   **Redis Logging:** Stores application logs in Redis for monitoring and analysis.
-   **CORS Support:** Enables Cross-Origin Resource Sharing (CORS) for frontend accessibility.
-   **Dockerized Deployment:** Easily deployable using Docker and Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed:

-   **Docker:** For containerization.
-   **Docker Compose:** For orchestrating the Docker environment.
-   **Python 3.11+:** For development and testing outside of Docker (optional).

## Setup Instructions

### 1. Clone the Repository

Clone the project from GitHub:

```bash
git clone https://github.com/Okramjimmy/docx-conversion.git
cd docx-conversion
```


### 2. Build and Run using Docker Compose (Recommended)

   *   Navigate to the root of the project where `docker-compose.yml` file is located.
    ```bash
   sudo  docker-compose up -d --build
    ```
     This command builds the Docker image and starts the service in detached mode. This will download Ubuntu 22.04 image, install all dependencies and run the program.

### 3. Run Locally (Optional)

 If you want to run the API locally (without docker):

   *  **Create a virtual environment:**

        ```bash
        python3.11 -m venv venv
        source venv/bin/activate  # For Linux/macOS
        # venv\Scripts\activate     # For Windows
        ```
   *   **Install Python Dependencies**:
        ```bash
        pip3.11 install -r requirements.txt
        ```
    *   **Set up Redis**:
        * Make sure that the `redis` is running in the host or as a docker container. If you choose to run in docker container, follow the command:
            ```bash
            docker run -d -p 6379:6379 --name my-redis redis:latest
            ```
    *   **Run the FastAPI app:**

        ```bash
        uvicorn main:app --host 0.0.0.0 --port 7002 --reload
        ```
        The API should now be running at `http://0.0.0.0:7002`.

## API Endpoints

### Version 1 Endpoints

These endpoints are available at `/api/v1/convert/`.

-   **GET `/`**: Base route to check the service is live, returns a welcome message for v1.

-   **POST `/docx2html/`**: Upload a DOCX file to convert it to a ZIP file containing the HTML and embedded image files.
     -   Input: `file` (file) in form data.
     -   Output: ZIP file containing the converted HTML and image files.

-   **POST `/docx2pdf/`**: Upload a DOCX file to convert it to a PDF file.
    -   Input: `file` (file) in form data.
    -   Output: PDF file.

-   **POST `/pdf2docx/`**: Upload a PDF file to convert it to a DOCX file.
    -   Input: `file` (file) in form data.
    -   Output: DOCX file.

-   **POST `/pdf2html/`**: Upload a PDF file to convert it to an HTML file (via intermediate DOCX).
    -   Input: `file` (file) in form data.
    -   Output: HTML file.

### Version 2 Endpoints
These endpoints are available at `/api/v2/convert/`.

-   **GET `/`**: Base route to check the service is live, returns a welcome message for v2.

-   **POST `/upload-docx/`**: Upload a DOCX file and convert it to an HTML file using Spire.Doc.
   -  Input: `file` (file) in form data.
   -  Output: HTML file.

### Logging Endpoint

-   **GET `/logs`**: Get last 50 application logs from Redis in a JSON format.

## Environment Variables

The following environment variables are used:

*   The redis client uses `host` and `port` to connect to the redis instance. These are defined directly inside the `main.py` file.

## File Structure

-   `main.py`: FastAPI application code with routing.
-   `requirements.txt`: Lists the project's dependencies.
-   `Dockerfile`: Used to build the Docker image.
-   `docker-compose.yaml`: Defines the services for the Docker environment.
-   `supervisord.conf`: Configuration file for Supervisor process manager.

## Dependencies

The application uses the following python packages

*   `fastapi`: For building the API
*   `uvicorn`: For starting the server
*   `python-multipart`: Required by FastAPI for handling file uploads
*   `redis`: For logging to redis server
*   `spire.doc`: For document conversion

## Testing

You can test the API using `curl` commands or any HTTP client like Postman. Below are some examples:

### Uploading DOCX and converting to HTML
```bash
curl -X POST -F "file=@path/to/your/document.docx" http://0.0.0.0:7002/api/v1/convert/docx2html/
```

### Uploading DOCX and converting to PDF
```bash
curl -X POST -F "file=@path/to/your/document.docx" http://0.0.0.0:7002/api/v1/convert/docx2pdf/
```

### Uploading PDF and converting to DOCX
```bash
curl -X POST -F "file=@path/to/your/document.pdf" http://0.0.0.0:7002/api/v1/convert/pdf2docx/
```

### Uploading PDF and converting to HTML
```bash
curl -X POST -F "file=@path/to/your/document.pdf" http://0.0.0.0:7002/api/v1/convert/pdf2html/
```

### Uploading DOCX and converting to HTML with Spire.Doc
```bash
curl -X POST -F "file=@path/to/your/document.docx" http://0.0.0.0:7002/api/v2/convert/upload-docx/
```
### Fetching Logs:
```bash
curl http://0.0.0.0:7002/logs
```
## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the Okram Jimmy License.


**Key Points in this README:**

*   **Comprehensive Overview:** It provides a clear description of the project, its features, and how to get it up and running.
*   **Docker Instructions:** It prioritizes Docker as the recommended method for running the API, with clear instructions.
*   **Local Setup:** It also provides instructions for a local setup if you want to run it outside of docker container.
*   **API Endpoint Details:** Describes each API endpoint in a structured and organized way, including the base route for each version.
*   **Logging Mentioned:** Explains how logs are stored in Redis and how to access them.
*   **Clear Testing Instructions:** Includes specific `curl` examples to help users test the various endpoints.
*   **File Structure:** Gives a brief overview of the project structure.
*   **Dependencies:** Lists the important project dependencies.
*   **Contributing and License:** Standard sections for open-source projects.


