DROP TABLE IF EXISTS `employee_reports`;

CREATE TABLE IF NOT EXISTS `employee_reports` (
  `reportId` int(11) NOT NULL AUTO_INCREMENT,
  `employeeNumber` int(11) NOT NULL,
  `reportContent` text NOT NULL,
  `reportDate` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reportId`),
  KEY `employeeNumber` (`employeeNumber`),
  CONSTRAINT `employee_reports_ibfk_1` FOREIGN KEY (`employeeNumber`) REFERENCES `employees` (`employeeNumber`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
