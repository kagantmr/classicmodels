DROP TABLE IF EXISTS offices;

-- Unnormalized Version (Violates 1NF)
-- CREATE TABLE offices (
--    officeCode      VARCHAR(10)    NOT NULL,
--    phone           VARCHAR(50)    NOT NULL,
--    full_address    VARCHAR(255)   NOT NULL,  -- e.g. "100 Market St, CA, USA, 94080"
--    territory       VARCHAR(10)    NOT NULL,
--    PRIMARY KEY (officeCode)
-- );

-- Normalized (3NF)
CREATE TABLE offices (
  officeCode    VARCHAR(10)    NOT NULL,
  city          VARCHAR(50)    NOT NULL,
  phone         VARCHAR(50)    NOT NULL,
  addressLine1  VARCHAR(50)    NOT NULL,
  addressLine2  VARCHAR(50)    DEFAULT NULL,
  `state`       VARCHAR(50)    DEFAULT NULL,
  country       VARCHAR(50)    NOT NULL,
  postalCode    VARCHAR(15)    NOT NULL,
  territory     VARCHAR(10)    NOT NULL,
  PRIMARY KEY (officeCode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


LOCK TABLES `offices` WRITE;
/*!40000 ALTER TABLE `offices` DISABLE KEYS */;
INSERT INTO `offices` VALUES ('1','San Francisco','+1 650 219 4782','100 Market Street','Suite 300','CA','USA','94080','NA'),('2','Boston','+1 215 837 0825','1550 Court Place','Suite 102','MA','USA','02107','NA'),('3','NYC','+1 212 555 3000','523 East 53rd Street','apt. 5A','NY','USA','10022','NA'),('4','Paris','+33 14 723 4404','43 Rue Jouffroy D\'abbans',NULL,NULL,'France','75017','EMEA'),('5','Tokyo','+81 33 224 5000','4-1 Kioicho',NULL,'Chiyoda-Ku','Japan','102-8578','Japan'),('6','Sydney','+61 2 9264 2451','5-11 Wentworth Avenue','Floor #2',NULL,'Australia','NSW 2010','APAC'),('7','London','+44 20 7877 2041','25 Old Broad Street','Level 7',NULL,'UK','EC2N 1HN','EMEA');
/*!40000 ALTER TABLE `offices` ENABLE KEYS */;
UNLOCK TABLES;