
CREATE DATABASE IF NOT EXISTS `db_asset_hub` ;
USE `db_asset_hub` ;

CREATE USER 'asset_hub_db_user'@'%' IDENTIFIED BY 'AssetHubDB2024';
GRANT ALL PRIVILEGES ON `db_asset_hub`.* TO 'asset_hub_db_user'@'%';


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_ambiente` (
  `ambiente` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL DEFAULT NULL,
  PRIMARY KEY (`ambiente`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;



CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_hardware` (
  `hardware` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL DEFAULT NULL,
  PRIMARY KEY (`hardware`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;



CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_orgs` (
  `organization` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL DEFAULT NULL,
  PRIMARY KEY (`organization`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_site` (
  `site` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL DEFAULT NULL,
  PRIMARY KEY (`site`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_host` (
  `uuid` VARCHAR(45) NOT NULL,
  `hostname` VARCHAR(45) NULL DEFAULT NULL,
  `data` JSON NOT NULL,
  `last_report_date` DATETIME NOT NULL,
  `description` VARCHAR(240) NULL DEFAULT NULL,
  `tb_ambiente_ambiente` VARCHAR(45) NULL DEFAULT NULL,
  `tb_orgs_organization` VARCHAR(45) NULL DEFAULT NULL,
  `tb_hardware_hardware` VARCHAR(45) NULL DEFAULT NULL,
  `tb_site_site` VARCHAR(45) NULL DEFAULT NULL,
  `os_name` VARCHAR(50) NULL DEFAULT NULL,
  `os_pretty_name` VARCHAR(100) NULL DEFAULT NULL,
  `os_release` VARCHAR(10) NULL DEFAULT NULL,
  `kernel_release` VARCHAR(50) NULL DEFAULT NULL,
  `os_type` VARCHAR(8) NULL DEFAULT NULL,
  `architecture` VARCHAR(10) NULL DEFAULT NULL,
  `boot_time` DATETIME NULL DEFAULT NULL,
  `total_bytes_sent` VARCHAR(20) NULL DEFAULT NULL,
  `total_bytes_recv` VARCHAR(25) NULL,
  `disk_total_read` VARCHAR(45) NULL,
  `disk_total_write` VARCHAR(45) NULL,
  PRIMARY KEY (`uuid`),
  INDEX `fk_tb_host_tb_ambiente1_idx` (`tb_ambiente_ambiente` ASC) VISIBLE,
  INDEX `fk_tb_host_tb_orgs1_idx` (`tb_orgs_organization` ASC) VISIBLE,
  INDEX `fk_tb_host_tb_hardware1_idx` (`tb_hardware_hardware` ASC) VISIBLE,
  INDEX `fk_tb_host_tb_site1_idx` (`tb_site_site` ASC) VISIBLE,
  CONSTRAINT `fk_tb_host_tb_ambiente1`
    FOREIGN KEY (`tb_ambiente_ambiente`)
    REFERENCES `db_asset_hub`.`tb_ambiente` (`ambiente`),
  CONSTRAINT `fk_tb_host_tb_hardware1`
    FOREIGN KEY (`tb_hardware_hardware`)
    REFERENCES `db_asset_hub`.`tb_hardware` (`hardware`),
  CONSTRAINT `fk_tb_host_tb_orgs1`
    FOREIGN KEY (`tb_orgs_organization`)
    REFERENCES `db_asset_hub`.`tb_orgs` (`organization`),
  CONSTRAINT `fk_tb_host_tb_site1`
    FOREIGN KEY (`tb_site_site`)
    REFERENCES `db_asset_hub`.`tb_site` (`site`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_passwd` (
  `username` VARCHAR(25) NOT NULL,
  `name` VARCHAR(100) NULL DEFAULT NULL,
  `user_hash` VARCHAR(200) NOT NULL,
  `enabled` TINYINT NOT NULL,
  PRIMARY KEY (`username`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_cpu` (
  `physical_cores` SMALLINT NULL,
  `logical_cores` SMALLINT NULL,
  `minFrequency` VARCHAR(45) NULL,
  `max_frequency` VARCHAR(45) NULL,
  `current_frequency` VARCHAR(45) NULL,
  `total_cpu_usage_percent` DECIMAL(5,2) NULL,
  `tb_host_uuid` VARCHAR(45) NOT NULL,
  INDEX `fk_tb_cpu_tb_host1_idx` (`tb_host_uuid` ASC) VISIBLE,
  PRIMARY KEY (`tb_host_uuid`),
  CONSTRAINT `fk_tb_cpu_tb_host1`
    FOREIGN KEY (`tb_host_uuid`)
    REFERENCES `db_asset_hub`.`tb_host` (`uuid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_memory` (
  `total_memory` VARCHAR(45) NULL,
  `free_memory` VARCHAR(45) NULL,
  `used_memory` VARCHAR(45) NULL,
  `memory_usage_percent` DECIMAL(5,2) NULL,
  `tb_host_uuid` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`tb_host_uuid`),
  CONSTRAINT `fk_tb_memory_tb_host1`
    FOREIGN KEY (`tb_host_uuid`)
    REFERENCES `db_asset_hub`.`tb_host` (`uuid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_swap` (
  `total_swap` VARCHAR(20) NULL,
  `free_swap` VARCHAR(20) NULL,
  `used_swap` VARCHAR(20) NULL,
  `swap_usage_percent` DECIMAL(5,2) NULL,
  `tb_host_uuid` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`tb_host_uuid`),
  CONSTRAINT `fk_tb_swap_tb_host1`
    FOREIGN KEY (`tb_host_uuid`)
    REFERENCES `db_asset_hub`.`tb_host` (`uuid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_disk_partition` (
  `disk_id` INT NOT NULL AUTO_INCREMENT,
  `device` VARCHAR(45) NULL,
  `mountpoint` VARCHAR(45) NULL,
  `filesystem` VARCHAR(15) NULL,
  `disk_total_size` VARCHAR(20) NULL,
  `disk_used_size` VARCHAR(20) NULL,
  `disk_usage_percent` VARCHAR(45) NULL,
  `disk_free_size` VARCHAR(20) NULL,
  `tb_host_uuid` VARCHAR(45) NOT NULL,
  `disk_usage_percent` DECIMAL(5,2) NULL,
  PRIMARY KEY (`disk_id`),
  INDEX `fk_tb_disk_partition_tb_host1_idx` (`tb_host_uuid` ASC) VISIBLE,
  CONSTRAINT `fk_tb_disk_partition_tb_host1`
    FOREIGN KEY (`tb_host_uuid`)
    REFERENCES `db_asset_hub`.`tb_host` (`uuid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_network_interface` (
  `id_network_interface` INT NOT NULL AUTO_INCREMENT,
  `family` VARCHAR(45) NULL,
  `address` VARCHAR(45) NULL,
  `netmask` VARCHAR(45) NULL,
  `broadcast` VARCHAR(45) NULL,
  `tb_host_uuid` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_network_interface`),
  INDEX `fk_tb_network_interface_tb_host1_idx` (`tb_host_uuid` ASC) VISIBLE,
  CONSTRAINT `fk_tb_network_interface_tb_host1`
    FOREIGN KEY (`tb_host_uuid`)
    REFERENCES `db_asset_hub`.`tb_host` (`uuid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;
