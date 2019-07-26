
CREATE SEQUENCE settings_seq START 1000;
CREATE TABLE settings (
    id          INTEGER NOT NULL DEFAULT NEXTVAL('settings_seq'),
    settings    JSON DEFAULT NULL,
    CONSTRAINT settings_pk PRIMARY KEY (id)
};


CREATE SEQUENCE alarm_contact_phone_seq START 1000;
CREATE TABLE alarm_contact_phone (
    id           INTEGER NOT NULL DEFAULT NEXTVAL('alarm_contact_seq'),
    phone_number VARCHAR(12) DEFAULT NULL,
    info         JSON DEFAULT NULL,
    CONSTRAINT alarm_contact_phone_pk PRIMARY KEY (id),
    UNIQUE (phone_number)
);
CREATE INDEX alarm_contact_phone_idx_phone_number ON alarm_contact(phone_number);


CREATE SEQUENCE alarm_contact_email_seq START 1000;
CREATE TABLE alarm_contact_email (
    id           INTEGER NOT NULL DEFAULT NEXTVAL('alarm_contact_seq'),
    email        VARCHAR(256) DEFAULT NULL,
    hash         VARCHAR(100) DEFAULT NULL,
    info         JSON DEFAULT NULL,
    CONSTRAINT alarm_contact_email_pk PRIMARY KEY (id),
    UNIQUE (email)
);
CREATE INDEX alarm_contact_email_idx_email ON alarm_contact(email);


CREATE SEQUENCE outgoing_alarm_seq START 1000;
CREATE TABLE outgoing_alarm (
    id           INTEGER NOT NULL DEFAULT NEXTVAL('outgoing_alarm_seq'),
    datetime     TIMESTAMPTZ,
    message      JSON DEFAULT NULL,
    recipient    VARCHAR DEFAULT NULL,
    CONSTRAINT outgoing_alarm_pk PRIMARY KEY (id)
);

-- TODO: Logs, for now keep in file

