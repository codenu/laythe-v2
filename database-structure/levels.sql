-- auto-generated definition
create table levels
(
    user_id  bigint(30)                not null,
    guild_id bigint(30)                not null,
    exp      bigint unsigned default 0 not null,
    level    bigint unsigned default 0 not null
);

