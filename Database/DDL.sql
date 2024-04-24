CREATE SCHEMA IF NOT EXISTS `db_asset_hub` ;
USE `db_asset_hub` ;

CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_passwd` (
  `username` VARCHAR(45) NOT NULL,
  `hash` VARCHAR(200) NOT NULL,
  `enabled` TINYINT NOT NULL,
  PRIMARY KEY (`username`));

CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_ambiente` (
  `ambiente` VARCHAR(45) NOT NULL,
  `description` VARCHAR(45) NULL,
  PRIMARY KEY (`ambiente`));

CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_orgs` (
  `organization` VARCHAR(45) NOT NULL,
  `description` VARCHAR(45) NULL,
  PRIMARY KEY (`organization`));


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_hardware` (
  `hardware` VARCHAR(45) NOT NULL,
  `description` VARCHAR(45) NULL,
  PRIMARY KEY (`hardware`));


CREATE TABLE IF NOT EXISTS `db_asset_hub`.`tb_host` (
  `id` VARCHAR(45) NOT NULL,
  `hostname` VARCHAR(45) NOT NULL,
  `data` JSON NOT NULL,
  `description` VARCHAR(400) NULL,
  `tb_ambiente_ambiente` VARCHAR(45) NOT NULL,
  `tb_orgs_organization` VARCHAR(45) NOT NULL,
  `tb_hardware_hardware` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id`, `tb_ambiente_ambiente`, `tb_orgs_organization`, `tb_hardware_hardware`),
  INDEX `fk_tb_host_tb_ambiente1_idx` (`tb_ambiente_ambiente` ASC) VISIBLE,
  INDEX `fk_tb_host_tb_orgs1_idx` (`tb_orgs_organization` ASC) VISIBLE,
  INDEX `fk_tb_host_tb_hardware1_idx` (`tb_hardware_hardware` ASC) VISIBLE,
  CONSTRAINT `fk_tb_host_tb_ambiente1`
    FOREIGN KEY (`tb_ambiente_ambiente`)
    REFERENCES `db_asset_hub`.`tb_ambiente` (`ambiente`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_tb_host_tb_orgs1`
    FOREIGN KEY (`tb_orgs_organization`)
    REFERENCES `db_asset_hub`.`tb_orgs` (`organization`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_tb_host_tb_hardware1`
    FOREIGN KEY (`tb_hardware_hardware`)
    REFERENCES `db_asset_hub`.`tb_hardware` (`hardware`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
