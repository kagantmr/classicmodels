CREATE TABLE employee_auth (
    employeeNumber INT PRIMARY KEY,
    hashedPassword VARCHAR(255) NOT NULL,
    CONSTRAINT fk_employee_auth_num
        FOREIGN KEY (employeeNumber)
        REFERENCES employees(employeeNumber)
        ON DELETE CASCADE
);