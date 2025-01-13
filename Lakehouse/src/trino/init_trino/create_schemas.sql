create schema if not exists minio.silver with (location = 's3a://silver/');
create schema if not exists minio.gold with (location = 's3a://gold/');