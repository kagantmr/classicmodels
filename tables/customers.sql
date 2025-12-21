/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS `customers`;
DROP TABLE IF EXISTS `locations`;

-- Create the Locations Table (3NF)
CREATE TABLE `locations` (
  `locationID` int(11) NOT NULL AUTO_INCREMENT,
  `city` varchar(50) NOT NULL,
  `state` varchar(50) DEFAULT NULL,
  `postalCode` varchar(15) DEFAULT NULL,
  `country` varchar(50) NOT NULL,
  PRIMARY KEY (`locationID`),
  UNIQUE KEY `unique_geo` (`city`, `state`, `postalCode`, `country`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Create the Normalized Customers Table
CREATE TABLE `customers` (
  `customerNumber` int(11) NOT NULL,
  `customerName` varchar(50) NOT NULL,
  `contactLastName` varchar(50) NOT NULL,
  `contactFirstName` varchar(50) NOT NULL,
  `phone` varchar(50) NOT NULL,
  `addressLine1` varchar(50) NOT NULL,
  `addressLine2` varchar(50) DEFAULT NULL,
  `locationID` int(11) DEFAULT NULL,
  `salesRepEmployeeNumber` int(11) DEFAULT NULL,
  `creditLimit` double DEFAULT NULL,
  PRIMARY KEY (`customerNumber`),
  KEY `salesRepEmployeeNumber` (`salesRepEmployeeNumber`),
  KEY `fk_customer_location` (`locationID`),
  CONSTRAINT `customers_ibfk_1` FOREIGN KEY (`salesRepEmployeeNumber`) 
  REFERENCES `employees` (`employeeNumber`) ON DELETE SET NULL,
  CONSTRAINT `customers_ibfk_2` FOREIGN KEY (`locationID`) 
  REFERENCES `locations` (`locationID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `locations` WRITE;
INSERT INTO `locations` (`locationID`, `city`, `state`, `postalCode`, `country`) VALUES 
(1,'Nantes',NULL,'44000','France'), (2,'Las Vegas','NV','83030','USA'), (3,'Melbourne','Victoria','3004','Australia'),
(4,'Stavern',NULL,'4110','Norway'), (5,'San Rafael','CA','97562','USA'), (6,'Warszawa',NULL,'01-012','Poland'),
(7,'Frankfurt',NULL,'60528','Germany'), (8,'San Francisco','CA','94217','USA'), (9,'NYC','NY','10022','USA'),
(10,'Madrid',NULL,'28034','Spain'), (11,'Luleå',NULL,'S-958 22','Sweden'), (12,'Kobenhavn',NULL,'1734','Denmark'),
(13,'Lyon',NULL,'69004','France'), (14,'Singapore',NULL,'079903','Singapore'), (15,'Allentown','PA','70267','USA'),
(16,'Burlingame','CA','94217','USA'), (17,'Singapore',NULL,'069045','Singapore'), (18,'Bergen',NULL,'N 5804','Norway'),
(19,'New Haven','CT','97823','USA'), (20,'Lisboa',NULL,'1756','Portugal'), (21,'Lille',NULL,'59000','France'),
(22,'Paris',NULL,'75012','France'), (23,'Cambridge','MA','51247','USA'), (24,'Bridgewater','CT','97562','USA'),
(25,'Kita-ku','Osaka',' 530-0003','Japan'), (26,'Helsinki',NULL,'21240','Finland'), (27,'Manchester',NULL,'EC2 5NT','UK'),
(28,'Dublin',NULL,'2','Ireland'), (29,'Brickhaven','MA','58339','USA'), (30,'Liverpool',NULL,'WX1 6LT','UK'),
(31,'Vancouver','BC','V3F 2K1','Canada'), (32,'Pasadena','CA','90003','USA'), (33,'Singapore',NULL,'038988','Singapore'),
(34,'Strasbourg',NULL,'67000','France'), (35,'Central Hong Kong',NULL,NULL,'Hong Kong'), (36,'Barcelona',NULL,'08022','Spain'),
(37,'Glendale','CA','92561','USA'), (38,'Cunewalde',NULL,'01307','Germany'), (39,'Århus',NULL,'8200','Denmark'),
(40,'Montréal','Québec','H1J 1C3','Canada'), (41,'Madrid',NULL,'28001','Spain'), (42,'San Diego','CA','91217','USA'),
(43,'Cowes','Isle of Wight','PO31 7PJ','UK'), (44,'Toulouse',NULL,'31000','France'), (45,'Torino',NULL,'10100','Italy'),
(46,'Paris',NULL,'75508','France'), (47,'Versailles',NULL,'78000','France'), (48,'Köln',NULL,'50739','Germany'),
(49,'Tsawassen','BC','T2F 8M4','Canada'), (50,'München',NULL,'80805','Germany'), (51,'North Sydney','NSW','2060','Australia'),
(52,'Bergamo',NULL,'24100','Italy'), (53,'Chatswood','NSW','2067','Australia'), (54,'Fribourg',NULL,'1700','Switzerland'),
(55,'Genève',NULL,'1203','Switzerland'), (56,'Oslo',NULL,'N 0106','Norway'), (57,'Amsterdam',NULL,'1043 GR','Netherlands'),
(58,'Berlin',NULL,'12209','Germany'), (59,'Oulu',NULL,'90110','Finland'), (60,'Bruxelles',NULL,'B-1180','Belgium'),
(61,'White Plains','NY','24067','USA'), (62,'New Bedford','MA','50553','USA'), (63,'Auckland',NULL,NULL,'New Zealand'),
(64,'London',NULL,'WX3 6FW','UK'), (65,'Newark','NJ','94019','USA'), (66,'South Brisbane','Queensland','4101','Australia'),
(67,'Espoo',NULL,'FIN-02271','Finland'), (68,'Brandenburg',NULL,'14776','Germany'), (69,'Philadelphia','PA','71270','USA'),
(70,'Madrid',NULL,'28023','Spain'), (71,'Los Angeles','CA','91003','USA'), (72,'Cork','Co. Cork',NULL,'Ireland'),
(73,'Marseille',NULL,'13008','France'), (74,'Reims',NULL,'51100','France'), (75,'Hatfield','Pretoria','0028','South Africa'),
(76,'Münster',NULL,'44087','Germany'), (77,'Boston','MA','51003','USA'), (78,'Nashua','NH','62005','USA'),
(79,'Lisboa',NULL,'1675','Portugal'), (80,'Bern',NULL,'3012','Switzerland'), (81,'Charleroi',NULL,'B-6000','Belgium'),
(82,'Salzburg',NULL,'5020','Austria'), (83,'Makati City',NULL,'1227 MM','Philippines'), (84,'Reggio Emilia',NULL,'42100','Italy'),
(85,'Minato-ku','Tokyo','106-0032','Japan'), (86,'Paris',NULL,'75016','France'), (87,'Stuttgart',NULL,'70563','Germany'),
(88,'Wellington',NULL,NULL,'New Zealand'), (89,'Munich',NULL,'80686','Germany'), (90,'Leipzig',NULL,'04179','Germany'),
(91,'Glendale','CT','97561','USA'), (92,'Bräcke',NULL,'S-844 67','Sweden'), (93,'San Jose','CA','94217','USA'),
(94,'Graz',NULL,'8010','Austria'), (95,'Aachen',NULL,'52066','Germany'), (96,'Glen Waverly','Victoria','3150','Australia'),
(97,'Milan',NULL,NULL,'Italy'), (98,'Burbank','CA','94019','USA'), (99,'Mannheim',NULL,'68306','Germany'),
(100,'Saint Petersburg',NULL,'196143','Russia'), (101,'Herzlia',NULL,'47625','Israel'), (102,'Sevilla',NULL,'41101','Spain'),
(103,'Brisbane','CA','94217','USA'), (104,'London',NULL,'WA1 1DP','UK');
UNLOCK TABLES;

LOCK TABLES `customers` WRITE;
INSERT INTO `customers` VALUES 
(103,'Atelier graphique','Schmitt','Carine ','40.32.2555','54, rue Royale',NULL,1,1370,21000),(112,'Signal Gift Stores','King','Jean','7025551838','8489 Strong St.',NULL,2,1166,71800),
(114,'Australian Collectors, Co.','Ferguson','Peter','03 9520 4555','636 St Kilda Road','Level 3',3,1611,117300),(119,'La Rochelle Gifts','Labrune','Janine ','40.67.8555','67, rue des Cinquante Otages',NULL,1,1370,118200),
(121,'Baane Mini Imports','Bergulfsen','Jonas ','07-98 9555','Erling Skakkes gate 78',NULL,4,1504,81700),(124,'Mini Gifts Distributors Ltd.','Nelson','Susan','4155551450','5677 Strong St.',NULL,5,1165,210500),
(125,'Havel & Zbyszek Co','Piestrzeniewicz','Zbyszek ','(26) 642-7555','ul. Filtrowa 68',NULL,6,NULL,0),(128,'Blauer See Auto, Co.','Keitel','Roland','+49 69 66 90 2555','Lyonerstr. 34',NULL,7,1504,59700),
(129,'Mini Wheels Co.','Murphy','Julie','6505555787','5557 North Pendale Street',NULL,8,1165,64600),(131,'Land of Toys Inc.','Lee','Kwai','2125557818','897 Long Airport Avenue',NULL,9,1323,114900),
(141,'Euro+ Shopping Channel','Freyre','Diego ','(91) 555 94 44','C/ Moralzarzal, 86',NULL,10,1370,227600),(144,'Volvo Model Replicas, Co','Berglund','Christina ','0921-12 3555','Berguvsvägen  8',NULL,11,1504,53100),
(145,'Danish Wholesale Imports','Petersen','Jytte ','31 12 3555','Vinbæltet 34',NULL,12,1401,83400),(146,'Saveley & Henriot, Co.','Saveley','Mary ','78.32.5555','2, rue du Commerce',NULL,13,1337,123900),
(148,'Dragon Souveniers, Ltd.','Natividad','Eric','+65 221 7555','Bronz Sok.','Bronz Apt. 3/6 Tesvikiye',14,1621,103800),(151,'Muscle Machine Inc','Young','Jeff','2125557413','4092 Furth Circle','Suite 400',9,1286,138500),
(157,'Diecast Classics Inc.','Leong','Kelvin','2155551555','7586 Pompton St.',NULL,15,1216,100600),(161,'Technics Stores Inc.','Hashimoto','Juri','6505556809','9408 Furth Circle',NULL,16,1165,84600),
(166,'Handji Gifts& Co','Victorino','Wendy','+65 224 1555','106 Linden Road Sandown','2nd Floor',17,1612,97900),(167,'Herkku Gifts','Oeztan','Veysel','+47 2267 3215','Brehmen St. 121','PR 334 Sentrum',18,1504,96800),
(168,'American Souvenirs Inc','Franco','Keith','2035557845','149 Spinnaker Dr.','Suite 101',19,1286,0),(169,'Porto Imports Co.','de Castro','Isabel ','(1) 356-5555','Estrada da saúde n. 58',NULL,20,NULL,0),
(171,'Daedalus Designs Imports','Rancé','Martine ','20.16.1555','184, chaussée de Tournai',NULL,21,1370,82900),(172,'La Corne D\'abondance, Co.','Bertrand','Marie','(1) 42.34.2555','265, boulevard Charonne',NULL,22,1337,84300),
(173,'Cambridge Collectables Co.','Tseng','Jerry','6175555555','4658 Baden Av.',NULL,23,1188,43400),(175,'Gift Depot Inc.','King','Julie','2035552570','25593 South Bay Ln.',NULL,24,1323,84300),
(177,'Osaka Souveniers Co.','Kentary','Mory','+81 06 6342 5555','1-6-20 Dojima',NULL,25,1621,81200),(181,'Vitachrome Inc.','Frick','Michael','2125551500','2678 Kingston Rd.','Suite 101',9,1286,76400),
(186,'Toys of Finland, Co.','Karttunen','Matti','90-224 8555','Keskuskatu 45',NULL,26,1501,96500),(187,'AV Stores, Co.','Ashworth','Rachel','(171) 555-1555','Fauntleroy Circus',NULL,27,1501,136800),
(189,'Clover Collections, Co.','Cassidy','Dean','+353 1862 1555','25 Maiden Lane','Floor No. 4',28,1504,69400),(198,'Auto-Moto Classics Inc.','Taylor','Leslie','6175558428','16780 Pompton St.',NULL,29,1216,23000),
(201,'UK Collectables, Ltd.','Devon','Elizabeth','(171) 555-2282','12, Berkeley Gardens Blvd',NULL,30,1501,92700),(202,'Canadian Gift Exchange Network','Tamuri','Yoshi ','(604) 555-3392','1900 Oak St.',NULL,31,1323,90300),
(204,'Online Mini Collectables','Barajas','Miguel','6175557555','7635 Spinnaker Dr.',NULL,29,1188,68700),(205,'Toys4GrownUps.com','Young','Julie','6265557265','78934 Hillside Dr.',NULL,32,1166,90700),
(206,'Asian Shopping Network, Co','Walker','Brydey','+612 9411 1555','Suntec Tower Three','8 Temasek',33,NULL,0),(209,'Mini Caravy','Citeaux','Frédérique ','88.60.1555','24, place Kléber',NULL,34,1370,53800),
(211,'King Kong Collectables, Co.','Gao','Mike','+852 2251 1555','Bank of China Tower','1 Garden Road',35,1621,58600),(216,'Enaco Distributors','Saavedra','Eduardo ','(93) 203 4555','Rambla de Cataluña, 23',NULL,36,1702,60300),
(219,'Boards & Toys Co.','Young','Mary','3105552373','4097 Douglas Av.',NULL,37,1166,11000),(223,'Natürlich Autos','Kloss','Horst ','0372-555188','Taucherstraße 10',NULL,38,NULL,0),
(227,'Heintze Collectables','Ibsen','Palle','86 21 3555','Smagsloget 45',NULL,39,1401,120800),(233,'Québec Home Shopping Network','Fresnière','Jean ','(514) 555-8054','43 rue St. Laurent',NULL,40,1286,48700),
(237,'ANG Resellers','Camino','Alejandra ','(91) 745 6555','Gran Vía, 1',NULL,41,NULL,0),(239,'Collectable Mini Designs Co.','Thompson','Valarie','7605558146','361 Furth Circle',NULL,42,1166,105000),
(240,'giftsbymail.co.uk','Bennett','Helen ','(198) 555-8888','Garden House','Crowther Way 23',43,1501,93900),(242,'Alpha Cognac','Roulet','Annette ','61.77.6555','1 rue Alsace-Lorraine',NULL,44,1370,61100),
(247,'Messner Shopping Network','Messner','Renate ','069-0555984','Magazinweg 7',NULL,7,NULL,0),(249,'Amica Models & Co.','Accorti','Paolo ','011-4988555','Via Monte Bianco 34',NULL,45,1401,113000),
(250,'Lyon Souveniers','Da Silva','Daniel','+33 1 46 62 7555','27 rue du Colonel Pierre Avia',NULL,46,1337,68100),(256,'Auto Associés & Cie.','Tonini','Daniel ','30.59.8555','67, avenue de l\'Europe',NULL,47,1370,77900),
(259,'Toms Spezialitäten, Ltd','Pfalzheim','Henriette ','0221-5554327','Mehrheimerstr. 369',NULL,48,1504,120400),(260,'Royal Canadian Collectables, Ltd.','Lincoln','Elizabeth ','(604) 555-4555','23 Tsawassen Blvd.',NULL,49,1323,89600),
(273,'Franken Gifts, Co','Franken','Peter ','089-0877555','Berliner Platz 43',NULL,50,NULL,0),(276,'Anna\'s Decorations, Ltd','O\'Hara','Anna','02 9936 8555','201 Miller Street','Level 15',51,1611,107800),
(278,'Rovelli Gifts','Rovelli','Giovanni ','035-640555','Via Ludovico il Moro 22',NULL,52,1401,119600),(282,'Souveniers And Things Co.','Huxley','Adrian','+61 2 9495 8555','Monitor Money Building','815 Pacific Hwy',53,1611,93300),
(286,'Marta\'s Replicas Co.','Hernandez','Marta','6175558555','39323 Spinnaker Dr.',NULL,23,1216,123700),(293,'BG&E Collectables','Harrison','Ed','+41 26 425 50 01','Rte des Arsenaux 41 ',NULL,54,NULL,0),
(298,'Vida Sport, Ltd','Holz','Mihael','0897-034555','Grenzacherweg 237',NULL,55,1702,141300),(299,'Norway Gifts By Mail, Co.','Klaeboe','Jan','+47 2212 1555','Drammensveien 126A','PB 211 Sentrum',56,1504,95100),
(303,'Schuyler Imports','Schuyler','Bradley','+31 20 491 9555','Kingsfordweg 151',NULL,57,NULL,0),(307,'Der Hund Imports','Andersen','Mel','030-0074555','Obere Str. 57',NULL,58,NULL,0),
(311,'Oulu Toy Supplies, Inc.','Koskitalo','Pirkko','981-443655','Torikatu 38',NULL,59,1501,90500),(314,'Petit Auto','Dewey','Catherine ','(02) 5554 67','Rue Joseph-Bens 532',NULL,60,1401,79900),
(319,'Mini Classics','Frick','Steve','9145554562','3758 North Pendale Street',NULL,61,1323,102700),(320,'Mini Creations Ltd.','Huang','Wing','5085559555','4575 Hillside Dr.',NULL,62,1188,94500),
(321,'Corporate Gift Ideas Co.','Brown','Julie','6505551386','7734 Strong St.',NULL,8,1165,105000),(323,'Down Under Souveniers, Inc','Graham','Mike','+64 9 312 5555','162-164 Grafton Road','Level 2',63,1612,88000),
(324,'Stylish Desk Decors, Co.','Brown','Ann ','(171) 555-0297','35 King George',NULL,64,1501,77000),(328,'Tekni Collectables Inc.','Brown','William','2015559350','7476 Moss Rd.',NULL,65,1323,43000),
(333,'Australian Gift Network, Co','Calaghan','Ben','61-7-3844-6555','31 Duncan St. West End',NULL,66,1611,51600),(334,'Suominen Souveniers','Suominen','Kalle','+358 9 8045 555','Software Engineering Center','SEC Oy',67,1501,98800),
(335,'Cramer Spezialitäten, Ltd','Cramer','Philip ','0555-09555','Maubelstr. 90',NULL,68,NULL,0),(339,'Classic Gift Ideas, Inc','Cervantes','Francisca','2155554695','782 First Street',NULL,69,1188,81100),
(344,'CAF Imports','Fernandez','Jesus','+34 913 728 555','Merchants House','27-30 Merchant\'s Quay',70,1702,59600),(347,'Men \'R\' US Retailers, Ltd.','Chandler','Brian','2155554369','6047 Douglas Av.',NULL,71,1166,57700),
(348,'Asian Treasures, Inc.','McKenna','Patricia ','2967 555','8 Johnstown Road',NULL,72,NULL,0),(350,'Marseille Mini Autos','Lebihan','Laurence ','91.24.4555','12, rue des Bouchers',NULL,73,1337,65000),
(353,'Reims Collectables','Henriot','Paul ','26.47.1555','59 rue de l\'Abbaye',NULL,74,1337,81100),(356,'SAR Distributors, Co','Kuger','Armand','+27 21 550 3555','1250 Pretorius Street',NULL,75,NULL,0),
(357,'GiftsForHim.com','MacKinlay','Wales','64-9-3763555','199 Great North Road',NULL,63,1612,77700),(361,'Kommission Auto','Josephs','Karin','0251-555259','Luisenstr. 48',NULL,76,NULL,0),
(362,'Gifts4AllAges.com','Yoshido','Juri','6175559555','8616 Spinnaker Dr.',NULL,77,1216,41900),(363,'Online Diecast Creations Co.','Young','Dorothy','6035558647','2304 Long Airport Avenue',NULL,78,1216,114200),
(369,'Lisboa Souveniers, Inc','Rodriguez','Lino ','(1) 354-2555','Jardim das rosas n. 32',NULL,79,NULL,0),(376,'Precious Collectables','Urs','Braun','0452-076555','Hauptstr. 29',NULL,80,1702,0),
(379,'Collectables For Less Inc.','Nelson','Allen','6175558555','7825 Douglas Av.',NULL,29,1188,70700),(381,'Royale Belge','Cartrain','Pascale ','(071) 23 67 2555','Boulevard Tirou, 255',NULL,81,1401,23500),
(382,'Salzburg Collectables','Pipps','Georg ','6562-9555','Geislweg 14',NULL,82,1401,71700),(385,'Cruz & Sons Co.','Cruz','Arnold','+63 2 555 3587','15 McCallum Street','NatWest Center #13-03',83,1621,81500),
(386,'L\'ordine Souveniers','Moroni','Maurizio ','0522-556555','Strada Provinciale 124',NULL,84,1401,121400),(398,'Tokyo Collectables, Ltd','Shimamura','Akiko','+81 3 3584 0555','2-2-8 Roppongi',NULL,85,1621,94400),
(406,'Auto Canal+ Petit','Perrier','Dominique','(1) 47.55.6555','25, rue Lauriston',NULL,86,1337,95000),(409,'Stuttgart Collectable Exchange','Müller','Rita ','0711-555361','Adenauerallee 900',NULL,87,NULL,0),
(412,'Extreme Desk Decorations, Ltd','McRoy','Sarah','04 499 9555','101 Lambton Quay','Level 11',88,1612,86800),(415,'Bavarian Collectables Imports, Co.','Donnermeyer','Michael',' +49 89 61 08 9555','Hansastr. 15',NULL,89,1504,77000),
(424,'Classic Legends Inc.','Hernandez','Maria','2125558493','5905 Pompton St.','Suite 750',9,1286,67500),(443,'Feuer Online Stores, Inc','Feuer','Alexander ','0342-555176','Heerstr. 22',NULL,90,NULL,0),
(447,'Gift Ideas Corp.','Lewis','Dan','2035554407','2440 Pompton St.',NULL,91,1323,49700),(448,'Scandinavian Gift Ideas','Larsson','Martha','0695-34 6555','Åkergatan 24',NULL,92,1504,116400),
(450,'The Sharp Gifts Warehouse','Frick','Sue','4085553659','3086 Ingle Ln.',NULL,93,1165,77600),(452,'Mini Auto Werke','Mendel','Roland ','7675-3555','Kirchgasse 6',NULL,94,1401,45300),
(455,'Super Scale Inc.','Murphy','Leslie','2035559545','567 North Pendale Street',NULL,19,1286,95400),(456,'Microscale Inc.','Choi','Yu','2125551957','5290 North Pendale Street','Suite 200',9,1286,39800),
(458,'Corrida Auto Replicas, Ltd','Sommer','Martín ','(91) 555 22 82','C/ Araquil, 67',NULL,70,1702,104600),(459,'Warburg Exchange','Ottlieb','Sven ','0241-039123','Walserweg 21',NULL,95,NULL,0),
(462,'FunGiftIdeas.com','Benitez','Violeta','5085552555','1785 First Street',NULL,62,1216,85800),(465,'Anton Designs, Ltd.','Anton','Carmen','+34 913 728555','c/ Gobelas, 19-1 Urb. La Florida',NULL,70,NULL,0),
(471,'Australian Collectables, Ltd','Clenahan','Sean','61-9-3844-6555','7 Allen Street',NULL,96,1611,60300),(473,'Frau da Collezione','Ricotti','Franco','+39 022515555','20093 Cologno Monzese','Alessandro Volta 16',97,1401,34800),
(475,'West Coast Collectables Co.','Thompson','Steve','3105553722','3675 Furth Circle',NULL,98,1166,55400),(477,'Mit Vergnügen & Co.','Moos','Hanna ','0621-08555','Forsterstr. 57',NULL,99,NULL,0),
(480,'Kremlin Collectables, Co.','Semenov','Alexander ','+7 812 293 0521','2 Pobedy Square',NULL,100,NULL,0),(481,'Raanan Stores, Inc','Altagar,G M','Raanan','+ 972 9 959 8555','3 Hagalim Blv.',NULL,101,NULL,0),
(484,'Iberia Gift Imports, Corp.','Roel','José Pedro ','(95) 555 82 82','C/ Romero, 33',NULL,102,1702,65700),(486,'Motor Mint Distributors Inc.','Salazar','Rosa','2155559857','11328 Douglas Av.',NULL,69,1323,72600),
(487,'Signal Collectibles Ltd.','Taylor','Sue','4155554312','2793 Furth Circle',NULL,103,1165,60300),(489,'Double Decker Gift Stores, Ltd','Smith','Thomas ','(171) 555-7555','120 Hanover Sq.',NULL,104,1501,43300),
(495,'Diecast Collectables','Franco','Valarie','6175552555','6251 Ingle Ln.',NULL,77,1188,85100),(496,'Kelly\'s Gift Shop','Snowden','Tony','+64 9 5555500','Arenales 1938 3\'A\'',NULL,63,1612,110000);
UNLOCK TABLES;