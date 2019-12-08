-- テーブルの全消去
drop table user_info, question, user_question;

-- ユーザーテーブルの作成
create table user_info(
  name varchar(128) not null,
  passwd varchar(128) not null unique,
  primary key(name, passwd)
);

create table question(
  id serial,
  url varchar(256) not null unique,
  stem varchar(256),
  primary key(id)
);

create table user_question(
  name varchar(128),
  passwd varchar(128),
  q_id serial,
  correct_key varchar(128),
  distracter_0 varchar(128),
  distracter_1 varchar(128),
  distracter_2 varchar(128),
  selected_choice varchar(128),
  primary key(name, passwd, q_id),
  foreign key(name, passwd) references user_info(name, passwd),
  foreign key(q_id) references question(id)
);
