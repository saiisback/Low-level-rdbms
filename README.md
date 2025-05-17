# MascotDB - A Lightweight RDBMS with Vector Capabilities

MascotDB is a lightweight relational database management system built from scratch in Python, featuring both traditional relational table operations and vector embedding storage/search capabilities. This project demonstrates the fundamentals of database systems while providing a clean, modern interface.

![MascotDB](/homepage.png)

## Features

- **Dual-Database Model**: Supports both relational tables and vector embeddings in a single system
- **Full CRUD Operations**: Create, read, update, and delete data with a SQL-like syntax
- **Vector Search**: Store and search vectors using cosine similarity
- **Modern Web Interface**: Clean terminal-inspired UI built with Next.js and React
- **REST API**: Simple HTTP API for integrating with any application
- **Persistent Storage**: Data is saved to disk in JSON format
- **Cross-Platform**: Works on macOS, Linux, and Windows

## Getting Started

### Prerequisites

- Python 3.10+ with NumPy
- Node.js 18+ with npm/yarn

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/mascotdb.git
cd mascotdb
```

2. Set up the backend:

```bash
cd backend
pip install fastapi uvicorn numpy
```

3. Set up the frontend:

```bash
cd ../frontend
npm install
# or
yarn
```

### Running the Application

1. Start the backend server:

```bash
cd backend
uvicorn server:app --reload
```

2. In a new terminal, start the frontend:

```bash
cd frontend
npm run dev
# or
yarn dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage Examples

### Database Operations

```sql
-- Create a new database
CREATE DATABASE mydb

-- Use a database
USE DATABASE mydb

-- List all databases
SHOW DATABASES

-- Delete a database
DROP DATABASE mydb
```

### Relational Table Operations

```sql
-- Create a table
CREATE TABLE users (id, name, email)

-- Insert data
INSERT INTO users VALUES (1, "John Doe", "john@example.com")

-- Query data
SELECT * FROM users

-- Delete a table
DROP TABLE users
```

### Vector Operations

```sql
-- Create a vector table
CREATE VECTOR TABLE embeddings DIMENSION 3

-- Insert a vector with metadata
INSERT VECTOR INTO embeddings VALUES [0.1, 0.2, 0.3] WITH METADATA {"text": "example"}

-- Search for similar vectors
VECTOR SEARCH embeddings QUERY [0.1, 0.2, 0.3] TOP 5
```

## Architecture

MascotDB consists of three main components:

1. **Storage Engine**: Handles data persistence using a simple file-based approach with JSON serialization
2. **Query Engine**: Processes SQL-like commands and performs database operations
3. **API Layer**: Exposes database functionality through a REST API and frontend UI

### Database Structure

- Each database is stored as a directory
- Relational tables are saved as `.rel.db` files
- Vector tables are saved as `.vec.db` files
- All data is stored in JSON format for easy inspection and debugging

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Implementation Details

MascotDB is built as a learning tool for understanding database concepts:

- **Relational Model**: Simple implementation of tables with columns and rows
- **Vector Embeddings**: Storage and retrieval of high-dimensional vectors with similarity search
- **In-Memory Operations**: Fast queries with persistence to disk
- **Simple Query Language**: SQL-inspired syntax for ease of use

The system deliberately avoids complexity found in production databases (transactions, indexes, etc.) to maintain readability and focus on core concepts.

## Roadmap

- [ ] Add support for complex queries with JOINs
- [ ] Implement basic indexing for faster lookups
- [ ] Add transaction support
- [ ] Support for more advanced vector operations (clustering, etc.)
- [ ] Add authentication and multi-user capabilities

## Contact

If you have any questions, feel free to reach out!


