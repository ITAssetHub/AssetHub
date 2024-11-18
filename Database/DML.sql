USE `db_asset_hub`;

INSERT INTO tb_passwd (username, user_hash, enabled) values ('admin', 'cbae5c1e505b8b0fcaf02b41546cd80df824532af0c97bfc0732a35463c45ea5', 1);

INSERT INTO tb_host_list (id, hosts) VALUES (1, '[]');

INSERT INTO tb_dashboard (id, cpu_mean_history, memory_mean_history) VALUES (1, '[]', '[]');