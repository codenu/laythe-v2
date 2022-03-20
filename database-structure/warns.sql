-- auto-generated definition
create table warns
(
    guild_id bigint(30) not null,
    date     bigint(30) not null,
    user_id  bigint(30) not null,
    mod_id   bigint(30) not null,
    reason   text       not null
);

