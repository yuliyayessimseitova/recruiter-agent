CREATE TABLE vacancies(id SERIAL PRIMARY KEY, title TEXT, brief TEXT, description TEXT, criteria JSONB, status TEXT DEFAULT 'draft', created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE candidates(id SERIAL PRIMARY KEY, vacancy_id INT REFERENCES vacancies, source TEXT, tg_chat_id BIGINT, full_name TEXT, phone TEXT, email TEXT, status TEXT DEFAULT 'new', score INT, summary TEXT, created_at TIMESTAMPTZ DEFAULT now(), delete_after DATE);
CREATE TABLE consents(id SERIAL PRIMARY KEY, candidate_id INT REFERENCES candidates, text_version TEXT, given_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE messages(id SERIAL PRIMARY KEY, candidate_id INT REFERENCES candidates, direction TEXT, body TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE interviews(id SERIAL PRIMARY KEY, candidate_id INT REFERENCES candidates, starts_at TIMESTAMPTZ, gcal_event_id TEXT, confirmed BOOL DEFAULT false);
CREATE TABLE audit_log(id SERIAL PRIMARY KEY, actor TEXT, action TEXT, details JSONB, at TIMESTAMPTZ DEFAULT now());
