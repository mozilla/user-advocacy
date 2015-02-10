DROP TABLE weekly_telemetry_stats; 
DROP TABLE telemetry_measures; 
DROP TABLE telemetry_screens; 


CREATE TABLE IF NOT EXISTS telemetry_screens (
  id                      INT          NOT NULL AUTO_INCREMENT,
  name                    VARCHAR(200) NOT NULL,
  file                    VARCHAR(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`name`)
) ENGINE=InnoDB;  


CREATE TABLE IF NOT EXISTS telemetry_measures (
  id                      INT          NOT NULL AUTO_INCREMENT,
  name                    VARCHAR(200) NOT NULL,
  `table`                 VARCHAR(200),
  category                VARCHAR(200),
  description             TEXT,
  screen_id               INT,
  x                       INT,
  y                       INT,
  width                   INT,
  height                  INT,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`screen_id`)  
    REFERENCES telemetry_screens(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  UNIQUE KEY `unique_stat` (`name`)
) ENGINE=InnoDB; 

REPLACE INTO telemetry_measures ( name ) VALUES () ;  

# inferred_version is calculated from release_info
CREATE TABLE IF NOT EXISTS weekly_telemetry_stats (
  id                      INT  NOT NULL AUTO_INCREMENT,
  inferred_version        INT  NOT NULL, 
  week                    DATE NOT NULL,
  os                      ENUM('windows','mac','linux'),
  measure_id              INT,
  measure_name            VARCHAR(200),
  measure_value           VARCHAR(200),
  users                   INT DEFAULT 0,
  potential_users         INT DEFAULT 0,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`measure_id`)  
    REFERENCES telemetry_measures(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  UNIQUE KEY `unique_stat` (`inferred_version`,`week`,`os`,`measure_name`, `measure_value`)
) ENGINE=InnoDB;  