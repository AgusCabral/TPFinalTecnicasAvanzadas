PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS generos (
    id_genero INTEGER PRIMARY KEY, -- ID oficial de TMDB
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS peliculas (
    id_pelicula INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id INTEGER NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    anio INTEGER,
    duracion_min INTEGER,
    poster_path TEXT,
    estado TEXT NOT NULL CHECK (estado IN ('vista', 'pendiente')),
    puntaje INTEGER CHECK (puntaje BETWEEN 1 AND 5), -- 1 a 5 pochoclos
    nota_diario TEXT,
    fecha_vista DATE,
    id_genero INTEGER NOT NULL,
    FOREIGN KEY (id_genero) REFERENCES generos(id_genero)
);

CREATE TABLE IF NOT EXISTS etiquetas (
    id_etiqueta INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL CHECK (tipo IN ('mood', 'contexto'))
);

CREATE TABLE IF NOT EXISTS pelicula_etiquetas (
    id_pelicula INTEGER NOT NULL,
    id_etiqueta INTEGER NOT NULL,
    PRIMARY KEY (id_pelicula, id_etiqueta),
    FOREIGN KEY (id_pelicula) REFERENCES peliculas(id_pelicula) ON DELETE CASCADE,
    FOREIGN KEY (id_etiqueta) REFERENCES etiquetas(id_etiqueta) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS suscripciones_usuario (
    provider_id INTEGER PRIMARY KEY, -- ID oficial de TMDB
    nombre TEXT NOT NULL,
    logo_path TEXT,
    activa INTEGER NOT NULL DEFAULT 0 CHECK (activa IN (0, 1))
);

CREATE TABLE IF NOT EXISTS peliculas_descartadas (
    tmdb_id INTEGER PRIMARY KEY,
    fecha_descarte DATE NOT NULL DEFAULT (DATE('now')),
    motivo TEXT
);

-- Géneros oficiales de TMDB
INSERT OR IGNORE INTO generos (id_genero, nombre) VALUES
    (28, 'Acción'), (12, 'Aventura'), (16, 'Animación'), (35, 'Comedia'),
    (80, 'Crimen'), (99, 'Documental'), (18, 'Drama'), (14, 'Fantasía'),
    (27, 'Terror'), (10749, 'Romance'), (878, 'Ciencia Ficción'), (53, 'Suspenso');

-- Etiquetas de Contexto y Mood personalizadas
INSERT OR IGNORE INTO etiquetas (nombre, tipo) VALUES
    ('Días de lluvia', 'contexto'),
    ('De madrugada', 'contexto'),
    ('Con amigos', 'contexto'),
    ('En pareja', 'contexto'),
    ('En familia', 'contexto'),
    ('Para llorar', 'mood'),
    ('Para reír', 'mood'),
    ('Nostalgia', 'mood'),
    ('Sin pensar', 'mood'),
    ('Alucinante', 'mood');

-- Plataformas populares en Argentina precargadas
INSERT OR IGNORE INTO suscripciones_usuario (provider_id, nombre, logo_path, activa) VALUES
    (8, 'Netflix', '/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg', 1),
    (119, 'Amazon Prime Video', '/dQeAar5H991VYporEjUspolDarG.jpg', 1),
    (337, 'Disney Plus', '/7rwgEs15tFwyR9NPQ5vpzxTj19Q.jpg', 0),
    (1899, 'Max', '/fksCUZ9QDWZMUwL2LgMtLckROUN.jpg', 0),
    (531, 'Paramount Plus', '/xbhHHa1YgtpwhC8lb1NQ3ACVcLd.jpg', 0),
    (350, 'Apple TV Plus', '/2E03IAZsX4ZaUqM7tXlctEPMGWS.jpg', 0),
    (283, 'Crunchyroll', '/mXeC4TrcgdU6ltE9bCBCEORwSQR.jpg', 0),
    (300, 'Pluto TV', '/t6N57S17sdXQLmZmVkaGnjWrNJ0.jpg', 0),
    (467, 'DGO', '/cDzkhghgS4V2N9530962728.jpg', 0),
    (339, 'Movistar TV', '/5vfrJQgNe9UnHVgVNAwZTy0Jo9o.jpg', 0);
