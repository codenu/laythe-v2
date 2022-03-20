-- auto-generated definition
create table settings
(
    guild_id          bigint(30)           not null
        primary key,
    accepted          tinyint(1) default 0 not null,
    custom_prefix     text                 null,
    flags             bigint(30) default 0 not null,
    mute_role         bigint(30)           null,
    log_channel       bigint(30)           null,
    welcome_channel   bigint(30)           null,
    starboard_channel bigint(30)           null,
    greet             text                 null,
    greet_dm          text                 null,
    bye               text                 null,
    reward_roles      text                 null,
    warn_actions      text                 null
);

