-- MySQL Script
-- dom 28 abr 2024 16:08:37

CREATE DATABASE IF NOT EXISTS `db_asset_hub` ;
USE `db_asset_hub` ;

CREATE USER 'asset_hub_db_user'@'%' IDENTIFIED BY 'AssetHubDB2024';
GRANT ALL PRIVILEGES ON `db_asset_hub`.* TO 'asset_hub_db_user'@'%';


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_passwd` (
  `username` VARCHAR(25) NOT NULL,
  `name` VARCHAR(100) NULL,
  `user_hash` VARCHAR(200) NOT NULL,
  `enabled` TINYINT NOT NULL,
  PRIMARY KEY (`username`));


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_ambiente` (
  `ambiente` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL,
  PRIMARY KEY (`ambiente`));

CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_orgs` (
  `organization` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL,
  PRIMARY KEY (`organization`));

CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_hardware` (
  `hardware` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL,
  PRIMARY KEY (`hardware`));

CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_site` (
  `site` VARCHAR(45) NOT NULL,
  `description` VARCHAR(240) NULL,
  PRIMARY KEY (`site`));

CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_host` (
  `hostname` VARCHAR(45) NOT NULL,
  `data` JSON NOT NULL,
  `description` VARCHAR(240) NULL,
  `tb_ambiente_ambiente` VARCHAR(45) NULL,
  `tb_orgs_organization` VARCHAR(45) NULL,
  `tb_hardware_hardware` VARCHAR(45) NULL,
  `tb_site_site` VARCHAR(45) NULL,
  `old_data1` JSON NULL,
  `old_data2` JSON NULL,
  `old_data3` JSON NULL,
  `old_data4` JSON NULL,
  INDEX `fk_tb_host_tb_ambiente1_idx` (`tb_ambiente_ambiente` ASC) VISIBLE,
  INDEX `fk_tb_host_tb_orgs1_idx` (`tb_orgs_organization` ASC) VISIBLE,
  INDEX `fk_tb_host_tb_hardware1_idx` (`tb_hardware_hardware` ASC) VISIBLE,
  PRIMARY KEY (`hostname`),
  INDEX `fk_tb_host_tb_site1_idx` (`tb_site_site` ASC) VISIBLE,
  CONSTRAINT `fk_tb_host_tb_ambiente1`
    FOREIGN KEY (`tb_ambiente_ambiente`)
    REFERENCES `db_asset_hub`.`tb_ambiente` (`ambiente`),
  CONSTRAINT `fk_tb_host_tb_orgs1`
    FOREIGN KEY (`tb_orgs_organization`)
    REFERENCES `db_asset_hub`.`tb_orgs` (`organization`),
  CONSTRAINT `fk_tb_host_tb_hardware1`
    FOREIGN KEY (`tb_hardware_hardware`)
    REFERENCES `db_asset_hub`.`tb_hardware` (`hardware`),
  CONSTRAINT `fk_tb_host_tb_site1`
    FOREIGN KEY (`tb_site_site`)
    REFERENCES `db_asset_hub`.`tb_site` (`site`));
