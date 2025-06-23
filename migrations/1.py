import os
import sys
import sys
sys.path.append('C:\\Users\\djsega1\\Desktop\\project2')
from database.connection import get_conn, release_conn

conn = get_conn()
cur = conn.cursor()
conn.autocommit = True

sql = """
-- ===================================================================
--                      SCHEMA CREATION
-- ===================================================================

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
  user_id         SERIAL    PRIMARY KEY,
  username        VARCHAR(100) UNIQUE NOT NULL,
  joined_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Счета
CREATE TABLE IF NOT EXISTS accounts (
  account_id      SERIAL    PRIMARY KEY,
  user_id         INTEGER   NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name            VARCHAR(100) NOT NULL,
  currency        VARCHAR(3)   NOT NULL,
  current_balance NUMERIC(12,2) NOT NULL DEFAULT 0
);

-- Категории (иерархия)
CREATE TABLE IF NOT EXISTS categories (
  category_id        SERIAL    PRIMARY KEY,
  user_id            INTEGER   NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name               VARCHAR(100) NOT NULL,
  parent_category_id INTEGER   REFERENCES categories(category_id) ON DELETE SET NULL
);

-- Транзакции
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id SERIAL    PRIMARY KEY,
  account_id     INTEGER   NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
  category_id    INTEGER   REFERENCES categories(category_id) ON DELETE SET NULL,
  amount         NUMERIC(12,2) NOT NULL,
  type           CHAR(1)   NOT NULL CHECK (type IN ('I','E')),
  occurred_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  description    TEXT
);

-- Бюджеты
CREATE TABLE IF NOT EXISTS budgets (
  budget_id     SERIAL    PRIMARY KEY,
  user_id       INTEGER   NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  category_id   INTEGER   NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
  amount_limit  NUMERIC(12,2) NOT NULL,
  spent NUMERIC(12,2) NOT NULL DEFAULT 0,
  start_date    DATE      NOT NULL,
  end_date      DATE      NOT NULL,
  CONSTRAINT ck_budget_dates CHECK (end_date > start_date)
);

ALTER TABLE budgets
  ADD COLUMN IF NOT EXISTS spent NUMERIC(12,2) NOT NULL DEFAULT 0;

-- Цели
CREATE TABLE IF NOT EXISTS goals (
  goal_id        SERIAL    PRIMARY KEY,
  user_id        INTEGER   NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name           VARCHAR(200) NOT NULL,
  target_amount  NUMERIC(12,2) NOT NULL,
  saved_amount   NUMERIC(12,2) NOT NULL DEFAULT 0,
  due_date       DATE,
  is_achieved    BOOLEAN   NOT NULL DEFAULT FALSE
);

-- Теги
CREATE TABLE IF NOT EXISTS tags (
  tag_id     SERIAL    PRIMARY KEY,
  user_id    INTEGER   NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name       VARCHAR(100) NOT NULL,
  UNIQUE(user_id, name)
);

-- M:N связь транзакций и тегов
CREATE TABLE IF NOT EXISTS transaction_tags (
  transaction_id INTEGER NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
  tag_id         INTEGER NOT NULL REFERENCES tags(tag_id)             ON DELETE CASCADE,
  PRIMARY KEY(transaction_id, tag_id)
);

-- Повторяющиеся транзакции
CREATE TABLE IF NOT EXISTS recurring_transactions (
  recur_id       SERIAL    PRIMARY KEY,
  user_id        INTEGER   NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  account_id     INTEGER   NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
  category_id    INTEGER   REFERENCES categories(category_id) ON DELETE SET NULL,
  amount         NUMERIC(12,2) NOT NULL,
  type           CHAR(1)   NOT NULL CHECK (type IN ('I','E')),
  freq_interval  INTERVAL  NOT NULL,
  next_run       DATE      NOT NULL,
  description    TEXT
);

-- ===================================================================
--                     TRIGGER FUNCTIONS
-- ===================================================================
CREATE OR REPLACE FUNCTION trg_before_insert_tx()
RETURNS trigger AS $$
DECLARE
  curr_balance NUMERIC;
  new_balance  NUMERIC;
BEGIN
  SELECT current_balance
    INTO curr_balance
    FROM accounts
   WHERE account_id = NEW.account_id
   FOR UPDATE;

  IF NEW.type = 'I' THEN
    new_balance := curr_balance + NEW.amount;
  ELSE
    new_balance := curr_balance - NEW.amount;
  END IF;

  IF new_balance < 0 THEN
    RAISE EXCEPTION 'Недостаточно средств: счёт #% (баланс после операции %).',
      NEW.account_id, new_balance;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1) После INSERT в transactions — корректируем баланс счёта
CREATE OR REPLACE FUNCTION trg_after_insert_transaction()
RETURNS trigger AS $$
BEGIN
  -- 2.1) Обновляем баланс счёта
  IF NEW.type = 'I' THEN
    UPDATE accounts
      SET current_balance = current_balance + NEW.amount
    WHERE account_id = NEW.account_id;
  ELSE
    UPDATE accounts
      SET current_balance = current_balance - NEW.amount
    WHERE account_id = NEW.account_id;
  END IF;

  -- 2.2) Если это расход (E), то снимаем с бюджета
  IF NEW.type = 'E' THEN
    UPDATE budgets b
    SET spent = b.spent + NEW.amount
    FROM accounts a
    WHERE a.account_id    = NEW.account_id
      AND b.user_id       = a.user_id
      AND b.category_id   = NEW.category_id
      AND (NEW.occurred_at::date BETWEEN b.start_date AND b.end_date);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2) После DELETE из transactions — возвращаем баланс
CREATE OR REPLACE FUNCTION trg_after_delete_transaction()
RETURNS trigger AS $$
BEGIN
  -- 3.1) Старый код: возвращаем баланс счёта
  IF OLD.type = 'I' THEN
    UPDATE accounts
      SET current_balance = current_balance - OLD.amount
    WHERE account_id = OLD.account_id;
  ELSE
    UPDATE accounts
      SET current_balance = current_balance + OLD.amount
    WHERE account_id = OLD.account_id;
  END IF;

  -- 3.2) Новое: если это расход (E), то возвращаем деньги в бюджет
  IF OLD.type = 'E' THEN
    UPDATE budgets b
    SET spent = b.spent - OLD.amount
    FROM accounts a
    WHERE a.account_id    = OLD.account_id
      AND b.user_id       = a.user_id
      AND b.category_id   = OLD.category_id
      AND (OLD.occurred_at::date BETWEEN b.start_date AND b.end_date);
  END IF;

  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- 3) Перед INSERT в budgets — проверяем, что даты валидны
CREATE OR REPLACE FUNCTION trg_before_insert_budget() RETURNS trigger AS $$
BEGIN
  IF NEW.end_date <= NEW.start_date THEN
    RAISE EXCEPTION 'end_date (%) must be > start_date (%)', NEW.end_date, NEW.start_date;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4) После UPDATE в goals — помечаем достигнутые
CREATE OR REPLACE FUNCTION trg_after_update_goal() RETURNS trigger AS $$
BEGIN
  IF NEW.saved_amount  >= NEW.target_amount
     AND OLD.is_achieved = FALSE THEN
    UPDATE goals
      SET is_achieved = TRUE
    WHERE goal_id = NEW.goal_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5) После INSERT в recurring_transactions — сразу создаём транзакцию и сдвигаем next_run
CREATE OR REPLACE FUNCTION trg_after_insert_recurring() RETURNS trigger AS $$
BEGIN
  INSERT INTO transactions(account_id, category_id, amount, type, occurred_at, description)
    VALUES (NEW.account_id, NEW.category_id, NEW.amount, NEW.type, NEW.next_run::timestamptz, NEW.description);
  UPDATE recurring_transactions
    SET next_run = NEW.next_run + NEW.freq_interval
    WHERE recur_id = NEW.recur_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6) Перед UPDATE freq_interval в recurring_transactions — не ниже 1 дня
CREATE OR REPLACE FUNCTION trg_before_update_recurring() RETURNS trigger AS $$
BEGIN
  IF NEW.freq_interval < INTERVAL '1 day' THEN
    RAISE EXCEPTION 'freq_interval (%) must be at least 1 day', NEW.freq_interval;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
--                        TRIGGERS REGISTRATION
-- ===================================================================

DROP TRIGGER IF EXISTS tr_check_ins ON transactions;
CREATE TRIGGER tr_check_ins
  BEFORE INSERT ON transactions
  FOR EACH ROW
  EXECUTE FUNCTION trg_before_insert_tx();

DROP TRIGGER IF EXISTS tr_insert_tx  ON transactions;
CREATE TRIGGER tr_insert_tx
  AFTER INSERT ON transactions
  FOR EACH ROW EXECUTE FUNCTION trg_after_insert_transaction();

DROP TRIGGER IF EXISTS tr_delete_tx  ON transactions;
CREATE TRIGGER tr_delete_tx
  AFTER DELETE ON transactions
  FOR EACH ROW EXECUTE FUNCTION trg_after_delete_transaction();

DROP TRIGGER IF EXISTS tr_insert_budget  ON budgets;
CREATE TRIGGER tr_insert_budget
  BEFORE INSERT ON budgets
  FOR EACH ROW EXECUTE FUNCTION trg_before_insert_budget();

DROP TRIGGER IF EXISTS tr_update_goal  ON goals;
CREATE TRIGGER tr_update_goal
  AFTER UPDATE ON goals
  FOR EACH ROW EXECUTE FUNCTION trg_after_update_goal();

DROP TRIGGER IF EXISTS tr_insert_recurring  ON recurring_transactions;
CREATE TRIGGER tr_insert_recurring
  AFTER INSERT ON recurring_transactions
  FOR EACH ROW EXECUTE FUNCTION trg_after_insert_recurring();

DROP TRIGGER IF EXISTS tr_update_recurring  ON recurring_transactions;
CREATE TRIGGER tr_update_recurring
  BEFORE UPDATE OF freq_interval ON recurring_transactions
  FOR EACH ROW EXECUTE FUNCTION trg_before_update_recurring();

-- Indices

CREATE INDEX IF NOT EXISTS idx_transactions_acc_occurred ON transactions(account_id, occurred_at DESC);

"""

try:
    cur.execute(sql)
    print("✓ Схема БД и триггеры успешно созданы.")
except Exception as e:
    print("❌ Ошибка при инициализации БД:", e)
finally:
    conn.close()
