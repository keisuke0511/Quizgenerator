-- テーブルの全消去
drop table user_info, question, user_question;

-- ユーザーテーブルの作成
create table user_info(
  id serial,
  name varchar(128) not null,
  passwd varchar(128) not null unique,
  primary key(id)
);

create table question(
  id serial,
  url varchar(256) not null,
  stem varchar(256),
  primary key(id)
);

create table user_question(
  id serial,
  u_id integer,
  q_id integer,
  correct_key varchar(128),
  distracter_0 varchar(128),
  distracter_1 varchar(128),
  distracter_2 varchar(128),
  selected_choice varchar(128),
  primary key(id),
  foreign key(u_id) references user_info(id),
  foreign key(q_id) references question(id)
);
