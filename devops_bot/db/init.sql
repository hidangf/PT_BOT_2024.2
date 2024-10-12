SELECT 'CREATE DATABASE replaceDB_DATABASE' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'replaceDB_DATABASE')\gexec
CREATE USER replaceDB_REPL_USER WITH REPLICATION ENCRYPTED PASSWORD 'replaceDB_REPL_PASSWORD';
\c replaceDB_DATABASE;
CREATE TABLE emails(
    id INT PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);
CREATE TABLE phones(
    id INT PRIMARY KEY,
    phone_number VARCHAR(255) NOT NULL
);
INSERT INTO emails(id, email) VALUES(1, 'first@fun.com');
INSERT INTO emails(id, email) VALUES(2, 'second@fun.com');
INSERT INTO emails(id, email) VALUES(3, 'third@rofl.com');
INSERT INTO phones(id, phone_number) VALUES(1, '89911231223');
INSERT INTO phones(id, phone_number) VALUES(2, '89001234566');
INSERT INTO phones(id, phone_number) VALUES(3, '89113334455');
