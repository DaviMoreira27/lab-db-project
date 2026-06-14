CREATE TABLE users (
    userid SERIAL NOT NULL PRIMARY KEY,
    login VARCHAR(200) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    id_original INTEGER,
    CONSTRAINT chk_tipo CHECK (tipo IN ('Admin', 'Escuderia', 'Piloto'))
);

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- A autenticação foi implementada diretamente pela tabela USERS devido a população inicial dos dados. O dataset possui centenas de pilotos e escuderias.
-- Criar roles nativas exigiria um script externo com acesso administrativo ao SGBD para a carga inicial,
-- aumentando a complexidade do setup. Com a tabela USERS um único INSERT INTO ... SELECT popula todos os usuários em uma transação SQL.

-- Um outro motivo, apesar do banco de dados permitir que roles so possam ver ou operar em tabelas selecionadas, essa verificacao teria que ser feita diretamente
-- no aplicativo de qualquer forma. Apesar da redundancia disso nao ser algo ruim, adiciona uma complexidade na qual nao queremos lidar no momento.
-- Por isso, essa verificacao so sera feita no app.

INSERT INTO users (login, password, tipo, id_original)
VALUES (
    'admin',
    crypt('admin', gen_salt('bf')),
    'Admin',
    NULL
);

INSERT INTO users (login, password, tipo, id_original)
SELECT
    c.constructor_ref || '_c',
    crypt(c.constructor_ref, gen_salt('bf')),
    'Escuderia',
    c.id
FROM constructors c
ON CONFLICT (login) DO NOTHING;

INSERT INTO users (login, password, tipo, id_original)
SELECT
    d.driver_ref || '_d',
    crypt(d.driver_ref, gen_salt('bf')),
    'Piloto',
    d.id
FROM drivers d
ON CONFLICT (login) DO NOTHING;

-- ==========================================
-- FUNÇÃO: PILOTO → USERS
-- ==========================================
CREATE OR REPLACE FUNCTION sync_driver_to_users()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO users (login, password, tipo, id_original)
        VALUES (
            NEW.driver_ref || '_d',
            crypt(NEW.driver_ref, gen_salt('bf')),
            'Piloto',
            NEW.id
        );

    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE users
        SET
            login    = NEW.driver_ref || '_d',
            password = crypt(NEW.driver_ref, gen_salt('bf'))
        WHERE id_original = NEW.id
          AND tipo = 'Piloto';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- FUNÇÃO: ESCUDERIA → USERS
-- ==========================================
CREATE OR REPLACE FUNCTION sync_constructor_to_users()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO users (login, password, tipo, id_original)
        VALUES (
            NEW.constructor_ref || '_c',
            crypt(NEW.constructor_ref, gen_salt('bf')),
            'Escuderia',
            NEW.id
        );

    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE users
        SET
            login    = NEW.constructor_ref || '_c',
            password = crypt(NEW.constructor_ref, gen_salt('bf'))
        WHERE id_original = NEW.id
          AND tipo = 'Escuderia';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_sync_driver
    AFTER INSERT OR UPDATE ON drivers
    FOR EACH ROW
    EXECUTE FUNCTION sync_driver_to_users();

CREATE OR REPLACE TRIGGER trg_sync_constructor
    AFTER INSERT OR UPDATE ON constructors
    FOR EACH ROW
    EXECUTE FUNCTION sync_constructor_to_users();

CREATE TABLE IF NOT EXISTS users_log (
    userid    INT          NOT NULL REFERENCES users(userid),
    action    VARCHAR(10)  NOT NULL,
    log_time  TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_users_log PRIMARY KEY (userid, log_time),
    CONSTRAINT chk_action CHECK (action IN ('LOGIN', 'LOGOUT', 'CRIAR_PIL', 'CRIAR_ESC'))
);

SELECT * FROM users;
