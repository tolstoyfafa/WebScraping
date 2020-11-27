# how to launch database
run mysql docker image:
```bash
 docker run --rm --name=mysql1 -p 3307:3306 -v my-datavolume:/var/lib/mysql -d mysql/mysql-server

```
```bash
docker logs mysql| grep GENERATED
```

```bash
docker exec -it mysql1 mysql -uscrap -p
```
```bash
ALTER USER 'root'@'localhost' IDENTIFIED BY 'secret';
```
CREATE USER 'scrap'@'172.17.0.1' IDENTIFIED BY 'secret';

connect scrap

 GRANT ALL PRIVILEGES ON scrap  TO 'scrap'@'172.17.0.1';
docker exec -it mysql1 mysql -uscrap -h 172.17.0.1 --port 3307 -p
