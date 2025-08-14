# API REST - CRUD de Microservicios de Gestión de Tareas

Una aplicación basada en microservicios para la gestión de tareas, la autenticación de usuarios y el manejo de datos de usuarios, desarrollada con Flask y SQLite. El sistema consta de cuatro servicios: API Gateway, Servicio de Autenticación, Servicio de Usuario y Servicio de Tareas, orquestados mediante un script Bash.

## Desarrollador
- Emmanuel Zuñiga Suare<>

## Descripción general de los servicios

- API Gateway (Puerto 5000): Transfiere solicitudes a los servicios de autenticación, usuario y tareas.

- Servicio de autenticación (Puerto 5001): Gestiona el registro e inicio de sesión de usuarios con autenticación JWT.

- Servicio de usuario (Puerto 5002): Gestiona los datos de usuario (operaciones CRUD) almacenados en memoria.

- Servicio de tareas (Puerto 5003): Gestiona tareas (operaciones CRUD) con base de datos SQLite y control de acceso basado en JWT.

## API Endpoints

### API Gateway (http://localhost:5000)
- `/auth/<path>` → Al servicio de Auth Service.
- `/user/<path>` → Al servicio de User Service.
- `/task/<path>` → Al servicio de Task Service.

### Authentication Service (http://localhost:5001)
- `POST /auth/register` → Registrar nuevo usario (username, password).
- `GET /auth/login/` → Inicie sesión y reciba el token JWT (username, password).

### User Service (http://localhost:5002)
- `GET /users/1` → Lista de usuarios específicos por nombre de usuario.
- `GET /users_id/<id>` → Obtener el usuario por ID.
- `POST /create_user` → Crear un usuario (username, password).
- `PUT /update_user/<id>` → Actualizar un usuario (username, password).
- `DELETE /users_id/<id>` →  Eliminar un usuario por ID.

### Task Service (http://localhost:5003) (JWT Required)
- `GET /tasks` → Listar todas las tareas.
- `GET /tasks/<id>` → Obtener la tarea por ID
- `POST /register_task` → Crear una tarea (name, description, created_at, dead_line, status, is_alive, created_by).
- `PUT /update_task/<id>` → Actualizar una tarea by ID.
- `PUT /disable_task/<id>` →  Desabilitar a task (is_alive = 0).
- `PUT /enable_task/<id>` →   Habilitar a task (is_alive = 1).
- Nota: El status de la tarea debe ser: En curso, Revisión, Completada, En pausa o Incompleta. Las fechas deben estar en formato AAAA-MM-DD.


## Seguridad
- JWT requerido para todas las rutas protegidas
- Token con expiración de 5 minutos
- Middleware `@token_required` 
- Roles definidos manualmente (admin.) en el mismo token

## Version
Python 3.12.6

## Crear entorno virtual
python3 -m venv venv
En Windows con WSL: source venv/Scripts/activate  o /bin/ depende tu configuracion de tu .sh           

## Instala dependencias
pip install -r requirements.txt

## Start services
El script start_services.sh inicializa el entorno virtual, busca puertos libres (5000–5003) e inicia todos los servicios en segundo plano.
Usando WSL para Windows
1. ./start_services.sh

## Stop services
Usando WSL para Windows
1. ./stop_services.sh


## Instalación
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu_usuario/nombre_proyecto.git
   cd nombre_proyecto
