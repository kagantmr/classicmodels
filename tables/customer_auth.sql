CREATE TABLE customer_auth (
    customerNumber INT PRIMARY KEY,
    hashedPassword VARCHAR(255) NOT NULL,
    CONSTRAINT fk_customer_auth_num
        FOREIGN KEY (customerNumber)
        REFERENCES customers(customerNumber)
        ON DELETE CASCADE
);