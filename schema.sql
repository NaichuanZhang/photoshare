DROP DATABASE photoshare;
CREATE DATABASE photoshare;
USE photoshare;
/*
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;
DROP TABLE Friends CASCADE;
DROP TABLE Albums CASCADE;
DROP TABLE Tags CASCADE;
DROP TABLE Pictures_Tags CASCADE;
DROP TABLE Comments CASCADE;
*/

CREATE TABLE Users(
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    fname varchar(30),
    lname varchar(30),
    dateofbirth date,
    hometown varchar(255),
    password varchar(255),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Friends(
	friend_id_1 int NOT NULL,
    friend_id_2 int NOT NULL,
    foreign key(friend_id_1) references Users(user_id),
    foreign key(friend_id_2) references Users(user_id),
    primary key(friend_id_1, friend_id_2)

);
CREATE TABLE Albums
(
  album_id int4 AUTO_INCREMENT,
  album_name varchar(255) NOT NULL,
  owner_id int4 NOT NULL,
  date_of_create date NOT NULL,
  PRIMARY KEY (album_id),
  FOREIGN KEY (owner_id) REFERENCES Users(user_id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT NOT NULL,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  album_id int,
  foreign key(user_id)references Users(user_id),
  foreign key(album_id)references Albums(album_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);
CREATE TABLE Comments
(
	comment_id int4 auto_increment NOT NULL,
    date_of_create date NOT NULL,
    description text NOT NULL,
    photo_id int4,
    PRIMARY KEY(comment_id),
    FOREIGN KEY(photo_id)references Pictures(picture_id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE TABLE Tags
(
	tag_id int4 auto_increment NOT NULL,
	description text,
    PRIMARY KEY(tag_id)
);
CREATE TABLE Pictures_Tags
(
	picture_id int4,
    tag_id int4,
    FOREIGN KEY (picture_id) references Pictures(picture_id) ON UPDATE CASCADE,
    FOREIGN KEY (tag_id) references Tags(tag_id) ON UPDATE CASCADE
);

/* testing data*/
INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
INSERT INTO albums(album_id,album_name,owner_id,date_of_create) Values (1,"album_one",2,'1001-01-01');

alter table albums drop date_of_create;
alter table albums add date_of_create datetime default CURRENT_TIMESTAMP;
