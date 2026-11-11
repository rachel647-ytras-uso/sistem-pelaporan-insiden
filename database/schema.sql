CREATE DATABASE IF NOT EXISTS sistem_insiden
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE sistem_insiden;

CREATE TABLE users (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  username        VARCHAR(50)  NOT NULL UNIQUE,
  password_hash   VARCHAR(255) NOT NULL,
  role            ENUM('user','admin','superadmin') NOT NULL DEFAULT 'user',
  is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
  failed_attempts INT          NOT NULL DEFAULT 0,
  locked_until    DATETIME     NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE laporan (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT          NOT NULL,
  judul          VARCHAR(150) NOT NULL,
  deskripsi      TEXT         NOT NULL,
  kategori       ENUM('phishing','malware','akses_ilegal','kebocoran_data','lainnya') NOT NULL,
  tingkat        ENUM('rendah','sedang','tinggi','kritis') NOT NULL,
  status         ENUM('baru','diproses','selesai') NOT NULL DEFAULT 'baru',
  catatan_admin  TEXT         NULL,
  ditangani_oleh INT          NULL,
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)        REFERENCES users(id),
  FOREIGN KEY (ditangani_oleh) REFERENCES users(id)
);

CREATE TABLE log_aktivitas (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT          NULL,
  username   VARCHAR(50)  NULL,
  aksi       VARCHAR(50)  NOT NULL,
  detail     VARCHAR(255) NULL,
  ip_address VARCHAR(45)  NULL,
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);