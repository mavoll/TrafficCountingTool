# TrafficCountingTool
Tool to draw lines into images and count objects crossing those lines (using Python and Tkinter; depending on former generated tracking results)

Description of our Data Analytics Pipeline used in our research project.

Steps:

* Install and configure a SMACK cluster (but actually without Mesos)
* Run the cluster 
* Create Apache Cassandra keyspaces
* Deploy SparkPipeline
* Start SparkPipeline apps (ongoing)
* Check Apache Zeppelin notebooks (ongoing)

## General architecture

* [Lambda architecture as data processing architecture](http://lambda-architecture.net/)
* [SMACK stack as the basis framework (**S**park, **M**esos, **A**kka, **C**assandra, **K**afka)](https://jaxenter.de/next-generation-big-data-mit-smack-48060)  

### Please note:
* Apache Mesos (the **M** in "SMACK") is not used and not considered in this project!
* Apache Zeppelin is used to provide notebooks! 

## Install and configure a SMACK stack

You need at least 3 cluster nodes (on-demand or on-premise). Docker containers available too as well as DC/OS. We are using 4 V-Server (provided by our University) and an Cassandra replication factor of 3 to be able to handle at least 1 server down. Read/write consistancy is set to QUORUM and replication strategy is the *SimpleStrategy* (see [How are consistent read and write operations handled?](https://docs.datastax.com/en/cassandra/3.0/cassandra/dml/dmlAboutDataConsistency.html) and [Data distribution and replication](https://docs.datastax.com/en/cassandra/2.1/cassandra/architecture/architectureDataDistributeAbout_c.html)).   
Choose one master node for Spark master as well as to run Apache Zeppelin on (this server may have a public ip to access Apache Zeppelin notebooks from outside).

For hardware choices first see:

* [Spark recommendations](https://spark.apache.org/docs/0.9.0/hardware-provisioning.html)
* [Cassandra recommendations](http://cassandra.apache.org/doc/latest/operating/hardware.html)

### Prerequisites and used versions

* Ubuntu 16.04 LTS
* Scala 2.11
* Java 8
* Apache2
* Maven 3.5.0
* SBT
* wget
* Git
* Cassandra 3.11
* cqlsh 5.0.1
* Spark 2.2.0 built for Hadoop 2.7.3* 
* spark-streaming_2.11 2.2.0
* spark-cassandra-connector_2.11 2.0.5
* Kafka 2.11-0.11.0.1
* spark-streaming-kafka-0-8_2.11 2.2.0
* akka-stream-kafka_2.11 0.17
* akka-stream_2.11 2.5.6
* akka-actor_2.11 2.5.6
* akka-http_2.11 10.0.10
* Zeppelin 0.7.3 
* npm
* nodejs-legacy
* libfontconfig
* twitter4j-core 4.0
* twitter4j-stream 4.0.6
* json4s-native_2.11 3.5.3
* json4s-jackson_2.11 3.5.3

### Apache Cassandra

#### Install Apache 2 (on all node)

`sudo apt-get install apache2`  
`sudo ufw allow 'Apache Full'`  
`sudo ufw allow 8080`  
`sudo ufw allow 8081`  
`sudo service apache2 start`

#### Install Cassandra (on all node)

`echo "deb http://www.apache.org/dist/cassandra/debian 311x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list`  
`curl https://www.apache.org/dist/cassandra/KEYS | sudo apt-key add -`  
`sudo apt-get update`  
`sudo apt-get install cassandra`  
`sudo service cassandra start`  
`nodetool status`

Configuration files is */etc/cassandra/cassandra.yaml*. Check following:

```
cluster_name: TestCluster
seed_provider - seeds: "<ip_node_1>,<ip_node_2>"
listen_address: <local_ip>
rpc_address: <local_ip>
```

Configuration files is */etc/cassandra/cassandra-env.sh*. Add following:

```
JVM_OPTS="$JVM_OPTS -Djava.library.path=$CASSANDRA_HOME/lib/sigar-bin"
JVM_OPTS="$JVM_OPTS $MX4J_ADDRESS"
JVM_OPTS="$JVM_OPTS $MX4J_PORT"
JVM_OPTS="$JVM_OPTS $JVM_EXTRA_OPTS"
```
The default location of log and data directories is */var/log/cassandra/* and */var/lib/cassandra*.
Start-up options (heap size, etc) can be configured in */etc/default/cassandra*.

Open ports:

`sudo ufw allow 9142`  
`sudo ufw allow 9160`  
`sudo ufw allow 9042`  
`sudo ufw allow 7199`  
`sudo ufw allow 7001`  
`sudo ufw allow 7000`

#### Add auth and user

Enable PasswordAuthenticator
```
in */etc/cassandra/cassandra.yaml* change/uncomment:

authenticator: PasswordAuthenticator
authorizer: AllowAllAuthorizer

sudo systemctl stop cassandra.service
sudo systemctl start cassandra.service

test default superuser:
cqlsh -u cassandra -p cassandra <ip> <port>
```

Increase replicaton factor of system_auth (important, otherwise you lose access to the cluster with just one node down!):
```
cqlsh -u cassandra -p cassandra <ip> <port>;
ALTER KEYSPACE "system_auth" WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 4 };
exit;
#nodetool repair system_auth
nodetool repair -full

#Wait until repair completes on a node, then move to the next node.
sudo systemctl stop cassandra.service
sudo systemctl start cassandra.service
```

Create super user and change standard password
```
cqlsh -u cassandra -p cassandra <ip> <port>
CREATE ROLE newuser WITH PASSWORD = 'newpasswd' AND SUPERUSER = true AND LOGIN = true;
#GRANT ALL PERMISSIONS ON ALL KEYSPACES TO ecl; (not necessary because authorizer is AllowAllAuthorizer; change if you want ACL)
ALTER ROLE cassandra WITH PASSWORD = 'HZDLJSVBkihhdod87402$$$' AND SUPERUSER = false;
exit;

cqlsh -u newuser -p newpasswd <ip> <port>;
```
Do not forget to change username/password in:
* SparkPipeline application.conf
* Spark spark-defaults.conf
* Zeppelin Interpreter Settings "Cassandra" 

### Apache Spark

#### Download and install Spark (on all node)

`sudo wget http://d3kbcqa49mib13.cloudfront.net/spark-2.2.0-bin-hadoop2.7.tgz`  
`sudo tar zxf spark-2.2.0-bin-hadoop2.7.tgz`  
`sudo mv ~/spark-2.2.0-bin-hadoop2.7 /spark`

`PATH=$PATH:/spark/bin`  
`export PATH`  
`export SPARK_HOME=/spark`  
`export SPARK_LOG_DIR=/var/log/spark`  
`export SPARK_PID_DIR=${SPARK_HOME}/run`  
`export SPARK_MASTER_HOST=<ip>`  
`source /etc/environment`

`sudo adduser spark --system --home /spark/ --disabled-password`  
`sudo chown -R spark:root /spark`  
`sudo mkdir /var/log/spark`  
`sudo chown spark:root /var/log/spark`  
`sudo -u spark mkdir $SPARK_HOME/run`  
`sudo cp /spark/conf/spark-env.sh.template /spark/conf/spark-env.sh`  
`sudo cp /spark/conf/spark-defaults.conf.template /spark/conf/spark-defaults.conf`  
`sudo chown spark:root /spark/conf/spark-*`

Edit */spark/conf/spark-defaults.conf*:

```
spark.cassandra.connection.host     <ip>
spark.cassandra.auth.username 		<username>        
spark.cassandra.auth.password	 	<password>
```

Edit */spark/conf/spark-env.sh*:

```
SPARK_LOCAL_IP=     <local_node_ip>
SPARK_MASTER_HOST=  <master_ip>
```

#### Download and install Spark-Cassandra Connector (on all node)

`git clone https://github.com/datastax/spark-cassandra-connector.git`  
`cd spark-cassandra-connector`  
`sudo git checkout v2.0.5`  
`sudo sbt -Dscala-2.11=true assembly`  
`sudo find . -iname "*.jar" -type f -exec /bin/cp {} /spark/jars/ \;`  
`cd ~/spark-cassandra-connector/target/full/scala-2.11/`  
`sudo cp spark-cassandra-connector-assembly-2.0.5.jar /spark/jars/spark-cassandra-connector-assembly-2.0.5.jar`  

Check also:

* [How to Install and Configure Spark 2.0 to Connect With Cassandra 3.X](https://dzone.com/articles/step-by-step-guide-to-installing-and-configuring-s)
* [Setup Spark with Cassandra Connector](https://coderwall.com/p/o9bkjg/setup-spark-with-cassandra-connector)

#### Start/Stop spark master and slave nodes (on Spark master node)

Edit */spark/sbin/start-master-slave.sh* (here 1 master node and 4 worker nodes):

`"${SPARK_HOME}/sbin"/start-master.sh --host <spark_master_ip>`  
`"${SPARK_HOME}/sbin"/start-slave.sh --host <spark_master_ip> spark://<spark_master_ip>:7077`  
`"${SPARK_HOME}/sbin"/start-slave.sh --host <spark_worker_node_2_ip> spark://<spark_master_ip>:7077`  
`"${SPARK_HOME}/sbin"/start-slave.sh --host <spark_worker_node_3_ip> spark://<spark_master_ip>:7077`  
`"${SPARK_HOME}/sbin"/start-slave.sh --host <spark_worker_node_4_ip> spark://<spark_master_ip>:7077`

Create service:

`cd /etc/systemd/system`  
`sudo nano spark-master-slave.service`  
`sudo chmod -v 777 /etc/systemd/system/spark-master-slave.service`

spark-master-slave.service:

```
[Unit]
Description=Apache Spark master and Slave
After=network.target
After=systemd-user-sessions.service
After=network-online.target
 
[Service]
User=spark
Type=forking
ExecStart=/spark/sbin/start-master-slave.sh
ExecStop=/spark/sbin/stop-master-slave.sh
TimeoutSec=30
Restart= on-failure
RestartSec= 30
StartLimitInterval=350
StartLimitBurst=10
 
[Install]
WantedBy=multi-user.target
```
`sudo systemctl enable spark-master-slave.service`  
`sudo systemctl daemon-reload`

`sudo systemctl start spark-master-slave.service`  
`sudo systemctl stop spark-master-slave.service`

`sudo ufw allow 7077`  
`sudo ufw allow 8080`  
`sudo ufw allow 8081`

#### Test Spark and Cassandra connector (on spark master node)

`sudo /spark/bin/spark-shell --conf spark.cassandra.auth.username=<username> --conf spark.cassandra.auth.password=<password> --jars /spark/jars/spark-cassandra-connector-assembly-2.0.5.jar --master spark://<spark_master_ip>:7077`

```
sc.parallelize( 1 to 1000 ).sum()
```

`cqlsh -u user -p password <ip> <port>`

```
CREATE KEYSPACE test2 WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2 }; 
CREATE TABLE test2.kv(key text PRIMARY KEY, value int);
INSERT INTO test2.kv(key, value) VALUES ('key1', 1); INSERT INTO test2.kv(key, value) VALUES ('key2', 2);
```

`/spark/bin/spark-shell --conf spark.cassandra.auth.username=<username> --conf spark.cassandra.auth.password=<password> --jars /spark/jars/spark-cassandra-connector-assembly-2.0.5.jar --master spark://<spark_master_ip>:7077`

```
import com.datastax.spark.connector._
val rdd = sc.cassandraTable("test3", "fun")
println(rdd.count)
```

### Apache Kafka

#### Install Kafka (on all node)

`sudo wget http://apache.mirror.cdnetworks.com/kafka/0.11.0.1/kafka_2.11-0.11.0.1.tgz`  
`sudo tar -xzf kafka_2.11-0.11.0.1.tgz`  
`cd /kafka_2.11-0.11.0.1`

Create services for kafka and zookeeper (see below in chapter 'Create systemd services').

`sudo ufw allow 9092`  
`sudo ufw allow 2181`  
`sudo ufw allow 2888`  
`sudo ufw allow 3888`

Add in */kafka_2.11-0.11.0.1/config/server.properties*:

```
broker.id=3 resp. 1,2, or 4
delete.topic.enable=true
listeners=PLAINTEXT://<node_ip>:9092
zookeeper.connect=<node_ip_1>:2181,<node_ip_2>:2181,<node_ip_3>:2181,<node_ip_4>:2181
```

In folder */kafka_2.11-0.11.0.1/zookeeperdata* create a new file called *myid*. The myid file should contain the corresponding server number (the choosen *broker.id*), in ASCII (For ex: 1), as the only entry in it.

Add in */kafka_2.11-0.11.0.1/config/zookeeper.properties*:

```
dataDir=/kafka_2.11-0.11.0.1/zookeeperdata
# the port at which the clients will connect
clientPort=2181
# disable the per-ip limit on the number of connections since this is a non-production config
maxClientCnxns=0
server.1=<node_ip_1>:2888:3888
server.2=<node_ip_2>:2888:3888
server.3=<node_ip_3>:2888:3888
server.4=<node_ip_4>:2888:3888
initLimit=5
syncLimit=2
```

Add in */kafka_2.11-0.11.0.1/config/producer.properties*:

```
bootstrap.servers=<node_ip_1>:9092,<node_ip_2>:9092,<node_ip_3>:9092,<node_ip_4>:9092
```

Add in */kafka_2.11-0.11.0.1/config/consumer.properties*:

```
zookeeper.connect=<node_ip_1>:2181,<node_ip_2>:2181,<node_ip_3>:2181,<node_ip_4>:2181
```

Add in */kafka_2.11-0.11.0.1/config/connect-standalone.properties*:

```
plugin.path=/kafka_2.11-0.11.0.1/lib
bootstrap.servers=<node_ip_1>:9092,<node_ip_2>:9092,<node_ip_3>:9092,<node_ip_4>:9092
```

Download *spark-streaming-kafka-0-10_2.11-2.2.0.jar*, *org.apache.kafka:kafka_2.11:0.11.0.1*, *org.apache.kafka:kafka-clients:0.11.0.1*, *com.typesafe.akka:akka-stream-kafka_2.11:0.17*, *com.typesafe.akka:akka-stream_2.11:2.5.6*, *com.typesafe.akka:akka-actor_2.11:2.5.6*, *com.typesafe.akka:akka-http_2.11:10.0.10*, *org.datasyslab:geospark:1.0.1* and save to */spark/jars*.

`sudo systemctl start zookeeper.service`  
`sudo systemctl start kafka.service`

#### Test

`/kafka_2.11-0.11.0.1/bin/kafka-topics.sh --create --zookeeper <node_ip_1>:2181 --replication-factor 3 --partitions 1 --topic test`

`/kafka_2.11-0.11.0.1/bin/kafka-topics.sh --describe --zookeeper <node_ip_1>:2181 --topic my-replicated-topic`

#### Create SparkPipeline topics

```
/kafka_2.11-0.11.0.1/bin/kafka-topics.sh --create --zookeeper <node_ip_1>:2181 --replication-factor 3 --partitions 10 --topic tweets_hamburg
/kafka_2.11-0.11.0.1/bin/kafka-topics.sh --create --zookeeper <node_ip_1>:2181 --replication-factor 3 --partitions 10 --topic tweets_berlin
/kafka_2.11-0.11.0.1/bin/kafka-topics.sh --create --zookeeper <node_ip_1>:2181 --replication-factor 3 --partitions 10 --topic tweets_dresden
/kafka_2.11-0.11.0.1/bin/kafka-topics.sh --create --zookeeper <node_ip_1>:2181 --replication-factor 3 --partitions 10 --topic tweets_munich
```

### Apache Zeppelin (on one node)

`git clone https://github.com/apache/zeppelin.git`

`sudo npm install -g bower`

`cd /zeppelin/`  
`./dev/change_scala_version.sh 2.11`

Change in */zeppelin/zeppelin-zengine/src/main/java/org/apache/zeppelin/interpreter/InterpreterSetting.java*:
* -    setupPropertiesForSparkR(sparkProperties, javaProperties.getProperty("SPARK_HOME"));
* +    setupPropertiesForSparkR(sparkProperties, System.getenv("SPARK_HOME"));

`mvn clean`  
`mvn clean package -DskipTests -Pspark-2.2 -Phadoop-2.7 -Ppyspark -Psparkr -Pscala-2.11`

`mv /zeppelin/conf/zeppelin-env.sh.template /zeppelin/conf/zeppelin-env.sh`

Insert into */zeppelin/conf/zeppelin.env.sh*

```
export SPARK_HOME=/spark
export ZEPPELIN_PORT=4040 #8080 is used by Spark
export MASTER=spark://<spark_master_ip>:7077
export SPARK_SUBMIT_OPTIONS="--driver-class-path $(echo /spark/jars/*.jar |sed 's/ /:/g')"
export ZEPPELIN_SPARK_MAXRESULT=100000
export ZEPPELIN_INTERPRETER_OUTPUT_LIMIT=1024000 
```

Start Zeppelin:
`/zeppelin/bin/zeppelin-daemon.sh start`

Open Zeppelin GUI in browser:
`http://<apache_ip>:4040`

Add following properties to *Spark interpreter* in Zeppelin GUI:

```
spark.cassandra.connection.host     <spark_master_ip> (or one of your other Cassandra cluster nodes) 
zeppelin.spark.useHiveContext       <false>
```

Add following properties to *Spark dependencies* in Zeppelin GUI:

```
org.apache.spark:spark-streaming-kafka-0-10_2.11:2.2.0	
org.apache.kafka:kafka_2.11:0.11.0.1	
org.apache.kafka:kafka-clients:0.11.0.1
com.typesafe.akka:akka-stream-kafka_2.11:0.17	
com.typesafe.akka:akka-stream_2.11:2.5.6	
com.typesafe.akka:akka-actor_2.11:2.5.6	
com.typesafe.akka:akka-http_2.11:10.0.10	
org.datasyslab:geospark:1.0.1	
org.datasyslab:geospark-sql:1.0.1	
org.datasyslab:geospark-viz:1.0.1
```

Add following properties to *Cassandra interpreter* in Zeppelin GUI:

```
cassandra.credentials.password	<password>
cassandra.credentials.username	<username>
cassandra.hosts	                <spark_master_ip>
```

Create service:

`cd /etc/systemd/system`  
`sudo nano zeppelin.service`  
`sudo chmod -v 777 /etc/systemd/system/zeppelin.service`

zeppelin.service:

```
[Unit]
Description=zeppelin
After=network.target
After=systemd-user-sessions.service
After=network-online.target
 
[Service]
User=hcuadmin
Type=forking
ExecStart=/zeppelin/bin/zeppelin-daemon.sh start
ExecStop=/zeppelin/bin/zeppelin-daemon.sh stop
TimeoutSec=30
Restart= on-failure
RestartSec= 30
StartLimitInterval=350
StartLimitBurst=10
 
[Install]
WantedBy=multi-user.target
```
`sudo systemctl enable zeppelin.service`  
`sudo systemctl daemon-reload`

`sudo systemctl start zeppelin.service`  
`sudo systemctl stop zeppelin.service`

`sudo ufw allow 4040`

See below chapter 'Check Apache Zeppelin notebooks'.

### Create systemd services (on all node)

`cd /etc/systemd/system`  
`sudo nano servicename.service`  
`sudo chmod -v 777 /etc/systemd/system/servicename.service`

servicename.service:

```
[Unit]
Description=servicename
After=network.target
After=systemd-user-sessions.service
After=network-online.target
After=kafka.service
 
[Service]
User=hcuadmin
Type=simple
WorkingDirectory=/SparkPipeline
ExecStart=/usr/local/bin/mvn exec:java -Dexec.mainClass="de.smartsquare.spark.batch.servicename"
ExecStop=/bin/kill -9 $MAINPID

[Install]
WantedBy=multi-user.target
```

`sudo systemctl daemon-reload`  
`sudo reboot`  
`sudo systemctl start servicename.service`  
`sudo systemctl stop servicename.service`  
`sudo systemctl enable servicename.service`  
`sudo systemctl status servicename.service`

Create services for (make sure to have the right order by using "After"-statement):
* Zookeeper (ExecStart=/kafka_2.11-0.11.0.1/bin/zookeeper-server-start.sh /kafka_2.11-0.11.0.1/config/zookeeper.properties and ExecStop=/kafka_2.11-0.11.0.1/bin/zookeeper-server-stop.sh)
* Kafka (ExecStart=/kafka_2.11-0.11.0.1/bin/kafka-server-start.sh /kafka_2.11-0.11.0.1/config/server.properties and ExecStop=/kafka_2.11-0.11.0.1/bin/kafka-server-stop.sh)
* cassandrakafkaconsumer (ExecStart=/usr/local/bin/mvn exec:java -Dexec.mainClass="de.smartsquare.spark.kafka.consumer.CassandraKafkaConsumer")
* twitterstreamapp (ExecStart=/usr/local/bin/mvn exec:java -Dexec.mainClass="de.smartsquare.spark.kafka.producer.TwitterStreamApp")
* akkahttpserver (ExecStart=/usr/local/bin/mvn exec:java -Dexec.mainClass="de.smartsquare.spark.serving.AkkaHttpServer")

## Run cluster (start/stop/status) 

`sudo systemctl stop kafka.service`  
`sudo systemctl stop zookeeper.service`  
`sudo systemctl stop cassandra.service`  
`sudo systemctl stop zeppelin.service`  
`sudo systemctl stop cassandrakafkaconsumer.service`  
`sudo systemctl stop twitterstreamapp.service`  
`sudo systemctl stop akkahttpserver.service`

`sudo systemctl start cassandra.service`  
`sudo systemctl start zookeeper.service`  
`sudo systemctl start kafka.service`  
`sudo systemctl start zeppelin.service`  
`sudo systemctl start twitterstreamapp.service`  
`sudo systemctl start cassandrakafkaconsumer.service`  
`sudo systemctl start akkahttpserver.service`

## Create Apache Cassandra keyspaces

`sudo cqlsh -u cassandra -p cassandra 184.97.49.98 9042`

`CREATE KEYSPACE IF NOT EXISTS  master_dataset WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3 };`  
`USE master_dataset;`

### Types

`CREATE TYPE master_dataset.hashtags (
  end int,
  start int,
  text text
);
`

`CREATE TYPE master_dataset.media (
  displayURL text,
  end int,
  expandedURL text,
  start int,
  text text,
  url text,
  id bigint,
  mediaURL text,
  mediaURLHttps text,
  mediatype  text
);
`

`CREATE TYPE master_dataset.urls (
  displayURL text,
  end int,
  expandedURL text,
  start int,
  text text,
  url text
);
`

`CREATE TYPE master_dataset.user_mentions (
  end int,
  id bigint,
  name text,
  screenName text,
  start int,
  text text
);
`

`CREATE TYPE master_dataset.symbols (
  end int,
  start int,
  text text
);
`

`CREATE TYPE master_dataset.geolocation (
  longitude double,
  latitude double
);
` 

### Tables

We are just creating some exemplary tables here!  

#### tweets_hamburg

PRIMARY KEY ((year, month, day), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC)

`CREATE TABLE IF NOT EXISTS tweets_hamburg (
    year int, month int, day int, hour int, tweetId bigint, createdAt bigint, currentUserRetweetId bigint, favoriteCount bigint, 
    contributors list<bigint>, inReplyToScreenName text, 
    inReplyToStatusId bigint, inReplyToUserId bigint, lang text, 
    quotedStatusId bigint, quotedStatusCreatedAt bigint, quotedStatusUserId bigint, quotedStatusUserName text,    
    retweetedStatusId bigint, retweetedStatusCreatedAt bigint, retweetedStatusUserId bigint, retweetedStatusUserName text,
    retweetCount bigint, source text, 
    text text, withheldInCountries list<text>, isFavorited boolean,
    isPossiblySensitive boolean, isRetweet boolean, isRetweeted boolean,
    isRetweetedByMe boolean, isTruncated boolean, placeCountry text,
    placeStreetAddress text, placeName text, placeId text,
    placeFullName text, placeURL text, placeCountryCode text, 
    placeType text, placeBoundingBoxType text, placeGeometryType text,
    placeBoundingBoxCoordinates list<FROZEN<geolocation>>, placeGeometryCoordinates list<FROZEN<geolocation>>, geoLocationLatitude double,
    geoLocationLongitude double, userId bigint, userName text, 
    userLang text, userDescription text, userListedCount bigint, 
    userLocation text, userProfileImageURL text, userProfileImageURLHttps text, 
    userScreenName text, userTimeZone text, userURL text, 
    userURLEntityDisplayURL text, userURLEntityEnd bigint, userURLEntityExpandedURL text, 
    userURLEntityStart bigint, userURLEntityText text, userURLEntityURL text, 
    userUtcOffset bigint, userWithheldInCountries list<text>, userIsContributorsEnabled boolean, 
    userIsDefaultProfile boolean, userIsDefaultProfileImage boolean, userIsFollowRequestSent boolean, 
    userIsGeoEnabled boolean, userIsProtected boolean, userIsShowAllInlineMedia boolean, 
    userIsTranslator boolean, userIsVerified boolean, userFriendsCount bigint, 
    userFavouritesCount bigint, userFollowersCount bigint, userStatusesCount bigint, 
    userMentionEntities list<FROZEN<user_mentions>>, uRLEntities list<FROZEN<urls>>, hashtagEntities list<FROZEN<hashtags>>, 
    mediaEntities list<FROZEN<media>>, symbolEntities list<FROZEN<symbols>>, 
    PRIMARY KEY ((year, month, day), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC);
`

#### tweets_hamburg_located

PRIMARY KEY ((year, month, day), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC);

`CREATE TABLE IF NOT EXISTS tweets_hamburg_located (
    year int, month int, day int, hour int, tweetId bigint, createdAt bigint, currentUserRetweetId bigint, favoriteCount bigint, 
    contributors list<bigint>, inReplyToScreenName text, 
    inReplyToStatusId bigint, inReplyToUserId bigint, lang text, 
    quotedStatusId bigint, quotedStatusCreatedAt bigint, quotedStatusUserId bigint, quotedStatusUserName text,    
    retweetedStatusId bigint, retweetedStatusCreatedAt bigint, retweetedStatusUserId bigint, retweetedStatusUserName text,
    retweetCount bigint, source text, 
    text text, withheldInCountries list<text>, isFavorited boolean,
    isPossiblySensitive boolean, isRetweet boolean, isRetweeted boolean,
    isRetweetedByMe boolean, isTruncated boolean, placeCountry text,
    placeStreetAddress text, placeName text, placeId text,
    placeFullName text, placeURL text, placeCountryCode text, 
    placeType text, placeBoundingBoxType text, placeGeometryType text,
    placeBoundingBoxCoordinates list<FROZEN<geolocation>>, placeGeometryCoordinates list<FROZEN<geolocation>>, geoLocationLatitude double,
    geoLocationLongitude double, userId bigint, userName text, 
    userLang text, userDescription text, userListedCount bigint, 
    userLocation text, userProfileImageURL text, userProfileImageURLHttps text, 
    userScreenName text, userTimeZone text, userURL text, 
    userURLEntityDisplayURL text, userURLEntityEnd bigint, userURLEntityExpandedURL text, 
    userURLEntityStart bigint, userURLEntityText text, userURLEntityURL text, 
    userUtcOffset bigint, userWithheldInCountries list<text>, userIsContributorsEnabled boolean, 
    userIsDefaultProfile boolean, userIsDefaultProfileImage boolean, userIsFollowRequestSent boolean, 
    userIsGeoEnabled boolean, userIsProtected boolean, userIsShowAllInlineMedia boolean, 
    userIsTranslator boolean, userIsVerified boolean, userFriendsCount bigint, 
    userFavouritesCount bigint, userFollowersCount bigint, userStatusesCount bigint, 
    userMentionEntities list<FROZEN<user_mentions>>, uRLEntities list<FROZEN<urls>>, hashtagEntities list<FROZEN<hashtags>>, 
    mediaEntities list<FROZEN<media>>, symbolEntities list<FROZEN<symbols>>, 
    PRIMARY KEY ((year, month, day), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC);
`

#### tweets_hamburg_by_lang

PRIMARY KEY ((lang, year, month, day), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC)

`CREATE TABLE IF NOT EXISTS tweets_hamburg_by_lang (
    year int, month int, day int, hour int, tweetId bigint, createdAt bigint, currentUserRetweetId bigint, favoriteCount bigint, 
    contributors list<bigint>, inReplyToScreenName text, 
    inReplyToStatusId bigint, inReplyToUserId bigint, lang text, 
    quotedStatusId bigint, quotedStatusCreatedAt bigint, quotedStatusUserId bigint, quotedStatusUserName text,    
    retweetedStatusId bigint, retweetedStatusCreatedAt bigint, retweetedStatusUserId bigint, retweetedStatusUserName text,
    retweetCount bigint, source text, 
    text text, withheldInCountries list<text>, isFavorited boolean,
    isPossiblySensitive boolean, isRetweet boolean, isRetweeted boolean,
    isRetweetedByMe boolean, isTruncated boolean, placeCountry text,
    placeStreetAddress text, placeName text, placeId text,
    placeFullName text, placeURL text, placeCountryCode text, 
    placeType text, placeBoundingBoxType text, placeGeometryType text,
    placeBoundingBoxCoordinates list<FROZEN<geolocation>>, placeGeometryCoordinates list<FROZEN<geolocation>>, geoLocationLatitude double,
    geoLocationLongitude double, userId bigint, userName text, 
    userLang text, userDescription text, userListedCount bigint, 
    userLocation text, userProfileImageURL text, userProfileImageURLHttps text, 
    userScreenName text, userTimeZone text, userURL text, 
    userURLEntityDisplayURL text, userURLEntityEnd bigint, userURLEntityExpandedURL text, 
    userURLEntityStart bigint, userURLEntityText text, userURLEntityURL text, 
    userUtcOffset bigint, userWithheldInCountries list<text>, userIsContributorsEnabled boolean, 
    userIsDefaultProfile boolean, userIsDefaultProfileImage boolean, userIsFollowRequestSent boolean, 
    userIsGeoEnabled boolean, userIsProtected boolean, userIsShowAllInlineMedia boolean, 
    userIsTranslator boolean, userIsVerified boolean, userFriendsCount bigint, 
    userFavouritesCount bigint, userFollowersCount bigint, userStatusesCount bigint, 
    userMentionEntities list<FROZEN<user_mentions>>, uRLEntities list<FROZEN<urls>>, hashtagEntities list<FROZEN<hashtags>>, 
    mediaEntities list<FROZEN<media>>, symbolEntities list<FROZEN<symbols>>, 
    PRIMARY KEY ((lang, year, month, day), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC);
`

#### tweets_hamburg_by_user

PRIMARY KEY ((userId, year), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC)

`CREATE TABLE IF NOT EXISTS tweets_hamburg_by_user (
    year int, month int, day int, hour int, tweetId bigint, createdAt bigint, currentUserRetweetId bigint, favoriteCount bigint, 
    contributors list<bigint>, inReplyToScreenName text, 
    inReplyToStatusId bigint, inReplyToUserId bigint, lang text, 
    quotedStatusId bigint, quotedStatusCreatedAt bigint, quotedStatusUserId bigint, quotedStatusUserName text,    
    retweetedStatusId bigint, retweetedStatusCreatedAt bigint, retweetedStatusUserId bigint, retweetedStatusUserName text,
    retweetCount bigint, source text, 
    text text, withheldInCountries list<text>, isFavorited boolean,
    isPossiblySensitive boolean, isRetweet boolean, isRetweeted boolean,
    isRetweetedByMe boolean, isTruncated boolean, placeCountry text,
    placeStreetAddress text, placeName text, placeId text,
    placeFullName text, placeURL text, placeCountryCode text, 
    placeType text, placeBoundingBoxType text, placeGeometryType text,
    placeBoundingBoxCoordinates list<FROZEN<geolocation>>, placeGeometryCoordinates list<FROZEN<geolocation>>, geoLocationLatitude double,
    geoLocationLongitude double, userId bigint, userName text, 
    userLang text, userDescription text, userListedCount bigint, 
    userLocation text, userProfileImageURL text, userProfileImageURLHttps text, 
    userScreenName text, userTimeZone text, userURL text, 
    userURLEntityDisplayURL text, userURLEntityEnd bigint, userURLEntityExpandedURL text, 
    userURLEntityStart bigint, userURLEntityText text, userURLEntityURL text, 
    userUtcOffset bigint, userWithheldInCountries list<text>, userIsContributorsEnabled boolean, 
    userIsDefaultProfile boolean, userIsDefaultProfileImage boolean, userIsFollowRequestSent boolean, 
    userIsGeoEnabled boolean, userIsProtected boolean, userIsShowAllInlineMedia boolean, 
    userIsTranslator boolean, userIsVerified boolean, userFriendsCount bigint, 
    userFavouritesCount bigint, userFollowersCount bigint, userStatusesCount bigint, 
    userMentionEntities list<FROZEN<user_mentions>>, uRLEntities list<FROZEN<urls>>, hashtagEntities list<FROZEN<hashtags>>, 
    mediaEntities list<FROZEN<media>>, symbolEntities list<FROZEN<symbols>>, 
    PRIMARY KEY ((userId, year), createdAt, tweetId)) WITH CLUSTERING ORDER BY (createdAt DESC);
`

#### more tables

Do the same for tables:
* tweets_berlin_located
* tweets_berlin_by_lang
* tweets_berlin_by_user
* tweets_munich_located
* tweets_munich_by_lang
* tweets_munich_by_user
* tweets_dresden_located
* tweets_dresden_by_lang
* tweets_dresden_by_user

##### Please note:
Later on we are going to run the ingestion processes for each Twitter stream (search words "Hamburg", "Berlin", "Munich" and "Dresden" in this case) on its own cluster node. 

### Counter tables

PRIMARY KEY (table_name))  
`CREATE TABLE IF NOT EXISTS tweets_counter (table_name text, tweets_counter counter, PRIMARY KEY (table_name));
`

PRIMARY KEY (table_name, year, month, day, hour))  
`CREATE TABLE IF NOT EXISTS tweets_counter_hourly (table_name text, year int, month int, day int, hour int, tweets_counter counter, PRIMARY KEY (table_name, year, month, day, hour));
`

PRIMARY KEY (table_name, year, month))  
`CREATE TABLE IF NOT EXISTS tweets_counter_monthly (table_name text, year int, month int, tweets_counter counter, PRIMARY KEY (table_name, year, month));
`

PRIMARY KEY (table_name, year, month, day))  
`CREATE TABLE IF NOT EXISTS tweets_counter_daily (table_name text, year int, month int, day int, tweets_counter counter, PRIMARY KEY (table_name, year, month, day));
`


PRIMARY KEY (table_name, lang))  
`CREATE TABLE IF NOT EXISTS tweets_counter_by_lang (table_name text, lang text, tweets_counter counter, PRIMARY KEY (table_name, lang));
`

PRIMARY KEY (table_name, year, month, day, hour, lang))  
`CREATE TABLE IF NOT EXISTS tweets_counter_by_lang_hourly (table_name text, year int, month int, day int, hour int, lang text, tweets_counter counter, PRIMARY KEY (table_name, year, month, day, hour, lang));
`

PRIMARY KEY (table_name, year, month, lang))  
`CREATE TABLE IF NOT EXISTS tweets_counter_by_lang_monthly (table_name text, year int, month int, lang text, tweets_counter counter, PRIMARY KEY (table_name, year, month, lang));
`

PRIMARY KEY (table_name, year, month, day, lang))  
`CREATE TABLE IF NOT EXISTS tweets_counter_by_lang_daily (table_name text, year int, month int, day int, lang text, tweets_counter counter, PRIMARY KEY (table_name, year, month, day, lang));
`


PRIMARY KEY ((table_name, year, month), day, hour, userLang, userName, userId))  
`CREATE TABLE IF NOT EXISTS tweets_counter_by_user_hourly (table_name text, year int, month int, day int, hour int, userLang text, userName text, userId bigint, tweets_counter counter, PRIMARY KEY ((table_name, year, month), day, hour, userLang, userName, userId));
`

PRIMARY KEY ((table_name, year, month), userLang, userName, userId))  
`CREATE TABLE IF NOT EXISTS tweets_counter_by_user_monthly (table_name text, year int, month int, userLang text, userName text, userId bigint, tweets_counter counter, PRIMARY KEY ((table_name, year, month), userLang, userName, userId));
`

PRIMARY KEY ((table_name, year, month), day, userLang, userName, userId))  
`CREATE TABLE IF NOT EXISTS tweets_counter_by_user_daily (table_name text, year int, month int, day int, userLang text, userName text, userId bigint, tweets_counter counter, PRIMARY KEY ((table_name, year, month), day, userLang, userName, userId));
`

## Deploy SparkPipeline to cluster nodes

We are going to deploy this project to all cluster nodes because we want to run SparkPipeline processes on all nodes. 

### Clone project to cluster nodes

`git clone https://github.com/mavoll/SparkPipeline.git`

### Adjust config files

Adjust /SparkPipeline/src/main/resources/application.conf:
* Add Twitter consumerKey, consumerSecret, accessToken, accessTokenSecret
* Add Cassandra user, passwd, port, hosts, keyspaces, tables, consistancy, replication factor
* Add Kafka topics
* Twitter search keywords and locations.

#### Please note:
Here we are using our 4 servers each to connect with different accounts to Twitters Streaming API and fetch tweets in regard to corresponding keywords and locations ("Hamburg", "Berlin", "Dresden", "Munich", "München", "Muenchen" as well as the geolocated boundingbox for each city).

Searching twitters standart parameter "track" and "location" ([Twitter streaming API parameters](https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html)) using twitter4j and scala: 
```
...
val boundingBox: Array[Double] = Array(11.232151,48.019056) 
val boundingBox1: Array[Double] = Array(11.836399,48.314901)
val keyWords = Array("Muenchen","M\u00FCnchen", "Munich") 
...
val query = new FilterQuery()
query.track(keyWords:_*)
query.locations(boundingBox, boundingBox1)
twitterStream.filter(query)
```


### Build project on cluster nodes

`cd /SparkPipeline`  
`mvn clean package`  
`mvn compile`

## Start/Stop SparkPipeline apps on cluster nodes 

### Ingestion
#### twitterstreamapp
Responsible to fetch tweets from Twitters Streaming API and publish them to Kafka topic

`sudo systemctl stop twitterstreamapp.service`  
`sudo systemctl start twitterstreamapp.service`  
`sudo systemctl status twitterstreamapp.service`
#### cassandrakafkaconsumer
Responsible to fetch tweets from Kafka topic and load them to cassandra tables

`sudo systemctl stop cassandrakafkaconsumer.service`  
`sudo systemctl start cassandrakafkaconsumer.service`  
`sudo systemctl status cassandrakafkaconsumer.service`

### Serving Layer
#### akkahttpserver
Responsible to execute pre specified queries and retrun results back to web client (through Akka Http).

`sudo systemctl stop akkahttpserver.service`  
`sudo systemctl start akkahttpserver.service`  
`sudo systemctl status akkahttpserver.service`

##### REST Routes: Get tweets
Returns Tweets within an time frame collected per Twitterstream.

REST-Routes: 
* tweets/hamburg
* tweets/berlin
* tweets/dresden
* tweets/munich

Parameter: 
* from_hour         ("01-01-2018 13:00:00")
* to_hour		    ("21-01-2018 23:00:00")
* upperleft_lat 	("53.408320")		optional
* upperleft_lon 	("9.657984")		optional
* lowerright_lat 	("53.748372")	 	optional
* lowerright_lon 	("10.370027")	 	optional
* lang 		        ("de")  	 		optional
* userId 		    ("271572434")	 	optional	

Note: 
* If upperleft_lat, upperleft_lon, lowerright_lat and lowerright_lon are given, then only located tweets (if place or direct geolocation is available) within this geolocated rectangle will be returned
* If lang (e.g. “de” or “en”) is given, than only Tweets written in that specified language will be returned
* If a userId  is given, than only Tweets from that user will returned
* You can just provide one optinal argument (lang, userId or upperleft_lat, upperleft_lon, lowerright_lat and lowerright_lon together) at time. 
* The more days you asking for the bigger is the JSON-Response as well as the runtime (600 sec timeout). Choose wisely depending on the number of Tweets collected for an specific Stream and time window

Example:

`http://192.168.13.16:9000/tweets/hamburg?from_hour=25-06-2018%2013:00:00&to_hour=27-06-2018%2013:00:00
http://192.168.13.16:9000/tweets/munich?from_hour=25-06-2018%2013:00:00&to_hour=27-06-2018%2013:00:00
http://192.168.13.16:9000/tweets/hamburg?from_hour=25-06-2018%2013:00:00&to_hour=27-06-2018%2013:00:00&lang=%27de%27
http://192.168.13.16:9000/tweets/hamburg?from_hour=25-03-2018%2013:00:00&to_hour=27-06-2018%2013:00:00&upperleft_lat=60&upperleft_lon=7&lowerright_lat=50&lowerright_lon=12`

Resulting fields (as json): 

field | type | comment
--- | --- | ---
createdAt | bigint |
tweetId | bigint |
userName | text |
lang | text | Tweet language
text | text | Tweet text
geoLocationLatitude | double | If available
geoLocationLongitude | double | If available


#### realtimeview
Compines batch and real-time view. Get batch results from cassandra and add real-time results from Speed Layer (SparkStreamKafka)

### Batch Layer
We are filtering our incoming Twitter stream (per node) by predefined terms and saving filtered tweets into corresponding Cassandra tables (corresponding to the keywords). Batch intervall: 60 sec 

#### batchprocessingunit (filtering tasks)

### Speed Layer
We are directly filtering our incoming Kafka stream (per node) by predefined terms and sending results to view. Speed intervall: 1 sec 
#### SparkStreamKafkaConsumer (filtering tasks)

## Check Apache Zeppelin notebooks

### Import notebooks
* Download notebooks from project folder "zeppelin_notebooks" to your lokal file system
* Use Apache Zeppelins web GUI and import the notebooks saved to your file system into your Zeppelin installation

#### Twitter ingestion notebooks
##### Twitter ingestion cockpit (total)
* Total tweets by twitterstreams (via CQL and Cassandra table: master_dataset.tweets_counter)
* Monthly tweets by twitterstreams (via CQL and Cassandra table: master_dataset.tweets_counter_monthly)
* Daily tweets by twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_daily)
* Hourly tweets by twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_hourly)

##### Twitter ingestion cockpit (by language)
* Total tweets by lang and twitterstream (via CQL and Cassandra table: master_dataset.tweets_counter_by_lang)
* Monthly tweets by lang and twitterstreams (via CQL and Cassandra table: master_dataset.tweets_counter_by_lang_monthly)
* Daily tweets by lang and twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_by_lang_daily)
* Hourly tweets by lang and twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_by_lang_hourly)

##### Twitter ingestion cockpit (by user)
* Total tweets by user and twitterstream (via CQL and Cassandra table: master_dataset.tweets_counter_by_user)
* Monthly tweets by user and twitterstreams (via CQL and Cassandra table: master_dataset.tweets_counter_by_user_monthly)
* Daily tweets by user and twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_by_user_daily)
* Hourly tweets by user and twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_by_user_hourly)

##### Twitter ingestion cockpit (by located)
* Total tweets with geolocation by twitterstream (via CQL and Cassandra table: master_dataset.tweets_counter)
* Monthly tweets with geolocation by twitterstreams (via CQL and Cassandra table: master_dataset.tweets_counter_monthly)
* Daily tweets with geolocation by twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_daily)
* Hourly tweets with geolocation by twitterstreams (via Spark, Spark-Cassandra Connector and Cassandra table: master_dataset.tweets_counter_hourly)

#### Create cassandra keyspaces notebook
* CQL statements to create the former described keyspace and its tables
* CQL statements to generate more keyspaces and tables

#### Admin notebook (Cassandra, Kafka, Spark, Zeppelin)
* Restarting services
* Fetch and print Kafka streams to out
* Create, describe, list, print Kafka topics
* List Zookeeper brokers and its status
* Check Cassandras, its keyspaces and nodes status
* Create, describe, list, print Cassandras keyspaces and tables
* CQL scripts
* Restart Sparks master and slave nodes
* Spark shell support including Spark-Cassandra Connector  

## Authors

* **Marc-André Vollstedt** - marc.vollstedt@gmail.com

## References

* [Apache Cassandra](http://cassandra.apache.org/)
* [Apache Spark](http://spark.apache.org/)
* [Apache Spark Streaming](http://spark.apache.org/docs/latest/streaming-programming-guide.html)
* [Apache Kafka](https://kafka.apache.org/)
* [Akka HTTP](http://doc.akka.io/docs/akka/2.4.7/scala/http/index.html)
* [Scala](http://scala-lang.org/)
* [Twitter streaming API - Parameters](https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html)
* [Twitter streaming API - Message types](https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/streaming-message-types)* 
* [ebay - Cassandra data modeling best practices part 1](https://www.ebayinc.com/stories/blogs/tech/cassandra-data-modeling-best-practices-part-1/)
* [ebay - Cassandra data modeling best practices part 2](https://www.ebayinc.com/stories/blogs/tech/cassandra-data-modeling-best-practices-part-2/)
* [lambda-architecture.net](http://lambda-architecture.net/)
* [KillrWeather - Reference application](https://github.com/killrweather/killrweather)
* [DataStax - Advanced time series with cassandra](https://www.datastax.com/dev/blog/advanced-time-series-with-cassandra)
* [knoldus - Twitter’s tweets analysis using lambda architecture](https://blog.knoldus.com/2017/01/31/twitters-tweets-analysis-using-lambda-architecture/)
* [jaxenter - Spark, Mesos, Akka, Cassandra, Kafka: Aus Big Data werde Fast Data](https://jaxenter.de/next-generation-big-data-mit-smack-48060)
* [JAVA MAGAZIN - Daten mit Kafka und Akka annehmen](https://public.centerdevice.de/4c90efbb-fcfe-4d71-a677-674fbb332319)
* [JAVA MAGAZIN - Streaming-Apps mit Kafka, Spark und Cassandra](https://public.centerdevice.de/7a7ddb85-e943-4a15-a73b-7c4d8948817d)
* [JAVA MAGAZIN - Datenanalyse mit Spark und Apache Zeppelin](https://public.centerdevice.de/d56fa4c1-6f6e-47c2-820d-6a110a0271e2)
* [geothread.net - Apache Spark, Zeppelin and geospatial big data processing](http://www.geothread.net/apache-spark-zeppelin-and-geospatial-big-data-processing/)


## Acknowledgments










